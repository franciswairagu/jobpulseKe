"""
reliability_audit.py — Field & Date Reliability Audit

Quantifies which fields in the cleaned JobPulse dataset can actually be
trusted for downstream analysis, broken down by source. Produces:
  - reports/field_completeness_<ts>.csv
  - reports/date_reliability_<ts>.csv
  - reports/reliability_audit_<ts>.md   (human-readable summary)

Key finding this encodes: missingness in this dataset is not random — it's
concentrated in specific sources (fantastic_jobs_hf, jobberman, etc.), and
even where date_posted IS populated, a meaningful share of values are
batch/import artifacts rather than genuine per-listing timestamps (many
unrelated postings sharing one exact date). This module flags both.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

# Columns worth auditing for completeness — the ones downstream stages
# (salary analytics, seniority classification, career pathways) depend on.
AUDIT_COLUMNS = [
    "date_posted", "salary", "currency", "experience_required",
    "education_required", "tech_category", "job_field",
    "employment_type", "country", "work_mode",
]

BATCH_SUSPECT_THRESHOLD = 5  # rows sharing one (source, date) pair -> suspect


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date_posted_dt"] = pd.to_datetime(df["date_posted"], errors="coerce")
    df["scraped_at_dt"] = (
        pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
        .dt.tz_localize(None)
    )
    return df


def field_completeness_by_source(df: pd.DataFrame) -> pd.DataFrame:
    """% populated for each audited column, broken down by source."""
    rows = []
    for source, g in df.groupby("source"):
        row = {"source": source, "n_rows": len(g)}
        for col in AUDIT_COLUMNS:
            row[f"{col}_pct_populated"] = round((1 - g[col].isna().mean()) * 100, 1)
        rows.append(row)

    overall = {"source": "ALL", "n_rows": len(df)}
    for col in AUDIT_COLUMNS:
        overall[f"{col}_pct_populated"] = round((1 - df[col].isna().mean()) * 100, 1)
    rows.append(overall)

    return pd.DataFrame(rows).sort_values("n_rows", ascending=False)


def date_reliability_audit(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Flags date_posted values that are likely batch/import artifacts rather
    than genuine per-listing dates: any (source, date) pair shared by
    BATCH_SUSPECT_THRESHOLD or more unrelated postings.

    Returns:
        source_summary: per-source date reliability stats
        trustworthy_rows: the subset of rows judged individually reliable
    """
    valid = df[
        (df["date_posted_dt"] >= "2020-01-01")
        & (df["date_posted_dt"] <= df["scraped_at_dt"].max())
    ].copy()

    pair_counts = valid.groupby(["source", "date_posted_dt"])["job_id"].transform("count")
    valid["is_batch_suspect"] = pair_counts >= BATCH_SUSPECT_THRESHOLD
    trustworthy_rows = valid[~valid["is_batch_suspect"]].copy()
    trustworthy_rows["days_since_posted"] = (
        trustworthy_rows["scraped_at_dt"] - trustworthy_rows["date_posted_dt"]
    ).dt.days

    rows = []
    for source, g in valid.groupby("source"):
        n = len(g)
        distinct_dates = g["date_posted_dt"].nunique()
        trustworthy_n = (~g["is_batch_suspect"]).sum()
        rows.append({
            "source": source,
            "dated_rows": n,
            "distinct_dates": distinct_dates,
            "avg_rows_per_date": round(n / distinct_dates, 1) if distinct_dates else None,
            "trustworthy_rows": int(trustworthy_n),
            "trustworthy_pct": round(trustworthy_n / n * 100, 1) if n else None,
        })
    source_summary = pd.DataFrame(rows).sort_values("dated_rows", ascending=False)

    return source_summary, trustworthy_rows


def bootstrap_ci(values, n_iter: int = 2000, ci: float = 95, seed: int = 42):
    """Bootstrap confidence interval for the median of a 1D array."""
    import numpy as np
    rng = np.random.default_rng(seed)
    data = np.asarray(values)
    data = data[~np.isnan(data)]
    if len(data) == 0:
        return None, None, None
    boot_medians = np.array([
        np.median(rng.choice(data, size=len(data), replace=True))
        for _ in range(n_iter)
    ])
    lo, hi = np.percentile(boot_medians, [(100 - ci) / 2, 100 - (100 - ci) / 2])
    return float(np.median(data)), float(lo), float(hi)


def write_report(
    completeness: pd.DataFrame,
    date_summary: pd.DataFrame,
    trustworthy_rows: pd.DataFrame,
    out_dir: Path,
    ts: str,
) -> Path:
    observed, ci_lo, ci_hi = bootstrap_ci(trustworthy_rows["days_since_posted"])

    lines = []
    lines.append("# JobPulse — Field & Date Reliability Audit\n")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_\n")

    lines.append("## Field Completeness\n")
    lines.append("Missingness is concentrated by source, not random. "
                  "Fields below `country` and `work_mode` should not be used "
                  "for whole-dataset analysis without filtering to the "
                  "sources that actually populate them.\n")
    lines.append(completeness.to_markdown(index=False))
    lines.append("")

    lines.append("\n## date_posted Reliability\n")
    lines.append(
        f"A `(source, date)` pair shared by {BATCH_SUSPECT_THRESHOLD}+ unrelated "
        "postings is flagged as a likely batch/import artifact rather than a "
        "genuine per-listing timestamp, and excluded from the trustworthy subset.\n"
    )
    lines.append(date_summary.to_markdown(index=False))
    lines.append("")
    lines.append(f"\n**Trustworthy dated rows (whole dataset): {len(trustworthy_rows)}**\n")
    if observed is not None:
        lines.append(
            f"Bootstrap 95% CI for median posting age on the trustworthy subset: "
            f"observed = {observed:.0f} days, CI = [{ci_lo:.0f}, {ci_hi:.0f}] days "
            f"(n={len(trustworthy_rows)}, 2000 resamples).\n"
        )

    lines.append("\n## Recommendations\n")
    lines.append(
        "- Do not build trend, salary, or experience-level analysis on the full "
        "dataset without first checking this report's completeness table.\n"
        "- `date_posted` needs a scraper-level fix for `fantastic_jobs_hf`, "
        "`jobberman`, `brightermonday`, `fuzu`, `indeed`, `jobwebkenya` — "
        "these sources never capture it, at ingestion or after cleaning.\n"
        "- Treat `date_posted` as unreliable for any (source, date) pair with "
        f"{BATCH_SUSPECT_THRESHOLD}+ postings; only the trustworthy subset "
        "should feed time-based analysis.\n"
        "- `salary`, `experience_required`, `education_required`, `job_field`, "
        "`employment_type` are all >90% missing dataset-wide — flag to "
        "teammates building Stage 4/5/6 on these fields.\n"
    )

    report_path = out_dir / f"reliability_audit_{ts}.md"
    report_path.write_text("\n".join(lines))
    return report_path


def run(input_path: str, output_dir: str = "reports"):
    print("=" * 80)
    print("DATA RELIABILITY AUDIT")
    print("=" * 80)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n[STEP 1/4] Loading data...")
    df = load_data(input_path)
    print(f"✓ Loaded {len(df)} rows")

    print("\n[STEP 2/4] Auditing field completeness by source...")
    completeness = field_completeness_by_source(df)
    completeness_path = out_dir / f"field_completeness_{ts}.csv"
    completeness.to_csv(completeness_path, index=False)
    print(f"✓ Saved {completeness_path}")

    print("\n[STEP 3/4] Auditing date_posted reliability...")
    date_summary, trustworthy_rows = date_reliability_audit(df)
    date_summary_path = out_dir / f"date_reliability_{ts}.csv"
    date_summary.to_csv(date_summary_path, index=False)
    print(f"✓ Saved {date_summary_path}")
    print(f"✓ Trustworthy dated rows: {len(trustworthy_rows)} / {df['date_posted'].notna().sum()} dated rows")

    print("\n[STEP 4/4] Writing summary report...")
    report_path = write_report(completeness, date_summary, trustworthy_rows, out_dir, ts)
    print(f"✓ Saved {report_path}")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

    return {
        "completeness": completeness,
        "date_summary": date_summary,
        "trustworthy_rows": trustworthy_rows,
        "report_path": report_path,
    }


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/jobpulse_cleaned.parquet"
    run(input_path)
