"""Generate job, course, and interview-practice recommendations from a CV."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cv import extract_text, profile_from_text
from src.recommender import JobRecommender, load_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Match a CV against JobPulse job data.")
    parser.add_argument("--cv", required=True, help="Path to a .txt, .pdf, or .docx CV")
    parser.add_argument("--jobs", required=True, help="Path to a JobPulse CSV or Parquet export")
    parser.add_argument("--top-k", type=int, default=10, help="Maximum jobs to return")
    parser.add_argument("--name", default="", help="Override candidate name inferred from CV")
    args = parser.parse_args()

    candidate = profile_from_text(extract_text(args.cv), args.name)
    plan = JobRecommender().build_plan(candidate, load_jobs(args.jobs), args.top_k)
    print(json.dumps(asdict(plan), default=str, indent=2))


if __name__ == "__main__":
    main()
