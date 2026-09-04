"""
Stage 3 (v2): NLP Enrichment — script version of notebooks/notebook.ipynb.

The notebook's own NLP work never got past "load the data" (it reads
data/archive/jobs_master.csv, calls a couple of .info()/.isna() calls, and
a roadmap sketch — no actual extraction). The real skill/metadata
extraction logic already existed as reusable engines in this package
(skill_extractor.py, metadata_extractor.py). This script is what the
notebook was building toward: a real, runnable pipeline that

  1. loads the latest Stage 2 (cleaned) dataset,
  2. runs every job through SkillExtractor + MetadataExtractor,
  3. flattens the results into parquet-friendly columns (sets/dicts don't
     round-trip through parquet, so skills become sorted lists + a JSON
     string for full fidelity),
  4. builds a single `rag_document` text field per job — title, company,
     location, seniority, skills, description all folded into one blob —
     which is exactly what the RAG system in src/rag/ embeds and searches,
  5. saves the enriched dataset to data/nlp/, and
  6. writes a `.last_nlp_output` marker (same pattern Stage 1 uses for
     Stage 2) so downstream scripts always pick up the freshest run
     without a hardcoded filename.

Why "v2" and not just replacing nlp_pipeline.py: nlp_pipeline.py's
process_record() looks up record.get('title', '') — but this project's
schema column is `job_title`, not `title` — so seniority/skill matching
against the title silently sees an empty string on every record. This
script fixes that and is the version actually wired into the pipeline
below; nlp_pipeline.py is left as-is rather than touched blind.

Run directly:
    python src/nlp/nlpv2.py

Or import:
    from src.nlp.nlpv2 import run_nlp_extraction_v2
    df, summary = run_nlp_extraction_v2()
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

# Allow running this file directly (`python src/nlp/nlpv2.py`) as well as
# importing it as `src.nlp.nlpv2` — both need the project root on sys.path
# for the `from src....` absolute imports below.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DATA_DIR, NLP_DATA_DIR
from src.nlp.skill_extractor import get_extractor
from src.nlp.metadata_extractor import get_metadata_extractor

logger = logging.getLogger(__name__)

LAST_CLEANED_GLOB = "jobpulse_cleaned_*.parquet"
LAST_NLP_MARKER = PROCESSED_DATA_DIR / ".last_nlp_output"

MAX_RAG_DOC_DESCRIPTION_CHARS = 1200  # keep embedded documents a reasonable size


def latest_cleaned_parquet() -> Optional[Path]:
    """Find the newest Stage 2 output, same auto-detect pattern
    run_stage2_cleaning.py uses for Stage 1's output (no hardcoded
    filenames anywhere in this pipeline)."""
    candidates = sorted(
        PROCESSED_DATA_DIR.glob(LAST_CLEANED_GLOB),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def latest_nlp_output() -> Optional[Path]:
    """Find the newest Stage 3 (nlpv2) output: prefer the marker file this
    module just wrote, fall back to the newest jobs_nlp_enriched_*.parquet
    on disk. Used by both src/rag/retriever.py and src/nlp/evaluation.py
    so there's a single source of truth for "what's the latest NLP run."
    """
    if LAST_NLP_MARKER.exists():
        marked = Path(LAST_NLP_MARKER.read_text().strip())
        if marked.exists():
            return marked
    candidates = sorted(
        NLP_DATA_DIR.glob("jobs_nlp_enriched_*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def _build_rag_document(row: Dict[str, Any], skills_flat: list, seniority: str) -> str:
    """One text blob per job for embedding/retrieval in src/rag.

    Deliberately puts the most search-relevant, low-noise fields first
    (title, company, location, seniority, skills) before the free-text
    description, since embedding models weight earlier tokens more
    reliably for short-document retrieval.
    """
    description = _s(row.get("job_description"))[:MAX_RAG_DOC_DESCRIPTION_CHARS]
    location = _s(row.get("location")) or _s(row.get("country")) or "Unknown"
    parts = [
        f"Job Title: {_s(row.get('job_title')) or 'Unknown'}",
        f"Company: {_s(row.get('company')) or 'Unknown'}",
        f"Location: {location}",
        f"Country: {_s(row.get('country')) or 'Unknown'}",
        f"Work Mode: {_s(row.get('work_mode')) or 'Unknown'}",
        f"Seniority: {seniority}",
        f"Employment Type: {_s(row.get('employment_type')) or 'Unknown'}",
        f"Skills: {', '.join(skills_flat) if skills_flat else 'None listed'}",
        f"Description: {description or 'Not available'}",
    ]
    return "\n".join(parts)


def _s(value) -> str:
    """NaN/float-safe string coercion. `nan or ""` doesn't work here since
    float('nan') is truthy in Python, so a missing pandas cell (read back
    as NaN) would otherwise reach .lower() as a float and crash."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def enrich_record(row: Dict[str, Any], skill_extractor, metadata_extractor) -> Dict[str, Any]:
    """Run one job record through skill + metadata extraction and flatten
    the results into columns that survive a parquet round-trip."""
    job_title = _s(row.get("job_title"))
    job_description = _s(row.get("job_description"))
    country = _s(row.get("country"))

    # --- Skills ---
    skills_by_category = skill_extractor.extract_skills(job_description)
    # Titles carry real signal too ("Senior Python Developer") and cost
    # nothing extra to check.
    title_skills = skill_extractor.extract_skills(job_title)
    for category, skills in title_skills.items():
        skills_by_category.setdefault(category, set()).update(skills)

    skills_flat = sorted({s for skills in skills_by_category.values() for s in skills})
    skill_categories = sorted(skills_by_category.keys())
    skills_json = json.dumps(
        {cat: sorted(skills) for cat, skills in skills_by_category.items()}
    )

    years_experience = skill_extractor.extract_years_experience(job_description)
    education = skill_extractor.extract_education(job_description)
    certifications = skill_extractor.extract_certifications(job_description)

    # --- Metadata ---
    seniority = metadata_extractor.extract_seniority_level(job_title, job_description)
    employment_type = metadata_extractor.extract_employment_type(job_description)
    work_mode_extracted = metadata_extractor.extract_work_mode(job_description)
    salary_range = metadata_extractor.extract_salary_range(job_description)
    is_remote_eligible = metadata_extractor.is_remote_eligible(job_description, country)

    enriched = {
        **row,
        "skills": skills_flat,
        "skill_categories": skill_categories,
        "skill_count": len(skills_flat),
        "skills_json": skills_json,
        "years_experience": years_experience,
        "education_extracted": education,
        "certifications": certifications,
        "seniority_level": seniority.value,
        "employment_type_extracted": employment_type,
        "work_mode_extracted": work_mode_extracted,
        "is_remote_eligible": is_remote_eligible,
        "salary_min_extracted": salary_range.get("min"),
        "salary_max_extracted": salary_range.get("max"),
        "salary_currency_extracted": salary_range.get("currency"),
    }
    enriched["rag_document"] = _build_rag_document(row, skills_flat, seniority.value)
    return enriched


def run_nlp_extraction_v2(
    input_parquet: Optional[Path] = None,
    output_dir: Path = NLP_DATA_DIR,
) -> "tuple[pd.DataFrame, Dict[str, Any]]":
    """Execute the full Stage 3 (v2) NLP enrichment pipeline.

    Returns (enriched_dataframe, summary_dict). Nothing is written to a
    reports/ directory — the summary is returned in-memory only, per the
    rest of this pipeline's convention (see run_stage1/2 scripts).
    """
    if input_parquet is None:
        input_parquet = latest_cleaned_parquet()
    if input_parquet is None or not Path(input_parquet).exists():
        raise FileNotFoundError(
            f"No Stage 2 output found in {PROCESSED_DATA_DIR} "
            f"(looked for {LAST_CLEANED_GLOB}). Run scripts/run_stage2_cleaning.py first."
        )
    input_parquet = Path(input_parquet)

    print(f"Using Stage 2 output: {input_parquet}")
    df = pd.read_parquet(input_parquet)
    input_count = len(df)
    print(f"Loaded {input_count:,} records")

    skill_extractor = get_extractor()
    metadata_extractor = get_metadata_extractor()

    records = df.to_dict(orient="records")
    enriched_records = []
    batch_size = 1000
    for i in range(0, input_count, batch_size):
        batch = records[i:i + batch_size]
        for row in batch:
            enriched_records.append(enrich_record(row, skill_extractor, metadata_extractor))
        done = min(i + batch_size, input_count)
        print(f"  Processed: {done:,}/{input_count:,} ({done / input_count * 100:.1f}%)")

    enriched_df = pd.DataFrame(enriched_records)

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"jobs_nlp_enriched_{timestamp}.parquet"
    enriched_df.to_parquet(output_path, index=False)
    LAST_NLP_MARKER.write_text(str(output_path))
    print(f"\n✓ Saved enriched dataset: {output_path}")

    # --- Summary (printed + returned, not written to disk) ---
    all_skills = [s for skills in enriched_df["skills"] for s in skills]
    from collections import Counter
    top_skills = Counter(all_skills).most_common(15)
    seniority_dist = enriched_df["seniority_level"].value_counts().to_dict()
    remote_pct = enriched_df["is_remote_eligible"].mean() * 100

    summary = {
        "stage": "Stage 3 (v2): NLP Enrichment",
        "timestamp": datetime.now().isoformat(),
        "input": {"records": input_count, "source": str(input_parquet)},
        "output": {"records": len(enriched_df), "path": str(output_path)},
        "top_skills": top_skills,
        "seniority_distribution": seniority_dist,
        "remote_eligible_pct": round(remote_pct, 1),
        "records_with_years_experience": int((enriched_df["years_experience"] > 0).sum()),
    }

    print("\n" + "=" * 60)
    print("STAGE 3 (v2) COMPLETE")
    print(f"  Records enriched: {len(enriched_df):,}")
    print(f"  Top skills: {', '.join(s for s, _ in top_skills[:8])}")
    print(f"  Remote-eligible: {remote_pct:.1f}%")
    print("=" * 60)

    return enriched_df, summary


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_nlp_extraction_v2()


if __name__ == "__main__":
    main()
