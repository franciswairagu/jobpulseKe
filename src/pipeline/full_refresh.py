"""Orchestration for one complete scrape-to-analytics data refresh."""

import logging
from datetime import datetime
from pathlib import Path

from src.config import ANALYTICS_DATA_DIR, PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)


def run_full_refresh(master_csv: Path, nlp_batch_size: int = 1000) -> dict[str, str]:
    """Run stages 1–4 against the master CSV created by the current scrape."""
    if not master_csv.is_file():
        raise FileNotFoundError(f"Scraper master dataset was not created: {master_csv}")

    # Local imports keep cron --help usable until all pipeline dependencies are
    # installed, and avoid making the scheduler itself a heavyweight import.
    from src.analytics.stage4_orchestrator import run_stage_4_analytics
    from src.ingestion.loader import run_stage_1_ingestion
    from src.nlp.nlpv2 import run_nlp_extraction_v2
    from src.processing.cleaner import run_stage_2_cleaning

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("Stage 1/4 — ingesting current scraper master: %s", master_csv)
    _, stage1_summary = run_stage_1_ingestion(str(master_csv))
    stage1_output = _latest_file(PROCESSED_DATA_DIR, "ingested_raw_*.parquet")

    logger.info("Stage 2/4 — cleaning and deduplicating: %s", stage1_output)
    _, _, stage2_output = run_stage_2_cleaning(str(stage1_output))

    logger.info("Stage 3/4 — extracting skills and metadata: %s", stage2_output)
    _, stage3_summary = run_nlp_extraction_v2(Path(stage2_output), batch_size=nlp_batch_size)
    stage3_output = Path(stage3_summary["output"]["path"])

    logger.info("Building the refreshed RAG index")
    from src.rag.retriever import JobPulseRAG
    JobPulseRAG().build(stage3_output, embedder_prefer="auto")

    stage4_output = PROCESSED_DATA_DIR / f"jobpulse_features_{run_id}.parquet"
    analytics_run_dir = ANALYTICS_DATA_DIR / f"refresh_{run_id}"
    logger.info("Stage 4/4 — engineering features and analytics exports")
    run_stage_4_analytics(stage3_output, stage4_output, analytics_run_dir)

    return {
        "master_csv": str(master_csv), "stage1": str(stage1_output),
        "stage2": str(stage2_output), "stage3": str(stage3_output),
        "stage4": str(stage4_output), "analytics": str(analytics_run_dir),
        "rag_index": str(JobPulseRAG().store.index_dir),
        "records_ingested": str(stage1_summary["total_records_ingested"]),
    }


def _latest_file(directory: Path, pattern: str) -> Path:
    candidates = list(directory.glob(pattern))
    if not candidates:
        raise RuntimeError(f"Expected output matching {pattern} was not created in {directory}")
    return max(candidates, key=lambda candidate: candidate.stat().st_mtime)
