#!/usr/bin/env python3
"""
JobPulse - Query the RAG system from the command line.

Usage:
    python scripts/query_rag.py "remote python developer in Kenya"
    python scripts/query_rag.py "senior devops engineer" --top-k 3
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import JobPulseRAG
from src.rag.validation import QueryValidationError


def main():
    parser = argparse.ArgumentParser(description="Query the JobPulse RAG system")
    parser.add_argument("query", help="Free-text search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    args = parser.parse_args()

    rag = JobPulseRAG().ensure_ready()

    try:
        results = rag.query(args.query, top_k=args.top_k)
    except QueryValidationError as e:
        print(f"\n⚠ {e}")
        sys.exit(1)

    def clean(value, fallback="Unknown"):
        if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
            return fallback
        return str(value)

    print(f"\nTop {len(results)} results for: \"{args.query}\"\n")

    if not rag.has_strong_matches(results):
        print("⚠ No strong matches found — showing the closest available results, "
              "but none may be a great fit. Try different or more specific terms.\n")

    for i, row in results.iterrows():
        company = clean(row["company"], "Unknown company")
        location = clean(row["location"], clean(row["country"], "Unknown location"))
        print(f"{i + 1}. {row['job_title']} — {company} ({location}) [score={row['score']:.3f}]")
        print(f"   Skills: {', '.join(row['skills']) if len(row['skills']) else 'none listed'}")
        print(f"   {clean(row['vacancy_url'], 'No URL available')}")
        print()


if __name__ == "__main__":
    main()
