"""One user-facing command for the common JobPulse workflows.

Examples:
    python scripts/jobpulse.py refresh --max-pages 5
    python scripts/jobpulse.py recommend --cv candidate.pdf --jobs output/master_africa_tech_jobs.csv
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, arguments: list[str]) -> int:
    """Run a project script with this interpreter, independent of shell setup."""
    command = [sys.executable, str(PROJECT_ROOT / script), *arguments]
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run common JobPulse workflows.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    refresh = subcommands.add_parser("refresh", help="Scrape jobs and run stages 1–4.")
    refresh.add_argument("--sources", nargs="+", help="Optional scraper source names.")
    refresh.add_argument("--max-pages", type=int, default=5)
    refresh.add_argument("--nlp-batch-size", type=int, default=1000)

    scrape = subcommands.add_parser("scrape", help="Run scrapers only, without the data pipeline.")
    scrape.add_argument("--sources", nargs="+")
    scrape.add_argument("--max-pages", type=int, default=5)

    recommend = subcommands.add_parser("recommend", help="Generate recommendations from a CV.")
    recommend.add_argument("--cv", required=True, help="Path to a .txt, .pdf, or .docx CV.")
    recommend.add_argument("--jobs", required=True, help="Path to a JobPulse CSV or Parquet file.")
    recommend.add_argument("--top-k", type=int, default=10)
    recommend.add_argument("--name", default="")

    args = parser.parse_args()
    if args.command == "refresh":
        command_args = ["--max-pages", str(args.max_pages), "--nlp-batch-size", str(args.nlp_batch_size)]
        if args.sources:
            command_args.extend(["--sources", *args.sources])
        return _run("scripts/run_scheduled_scrape.py", command_args)
    if args.command == "scrape":
        command_args = ["--max-pages", str(args.max_pages), "--scrape-only"]
        if args.sources:
            command_args.extend(["--sources", *args.sources])
        return _run("scripts/run_scheduled_scrape.py", command_args)

    command_args = ["--cv", args.cv, "--jobs", args.jobs, "--top-k", str(args.top_k)]
    if args.name:
        command_args.extend(["--name", args.name])
    return _run("scripts/recommend_from_cv.py", command_args)


if __name__ == "__main__":
    raise SystemExit(main())
