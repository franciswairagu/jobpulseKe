"""Ask a grounded question over the JobPulse RAG index."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag import JobPulseAssistant, QueryValidationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the grounded JobPulse RAG assistant.")
    parser.add_argument("question", help="A job-market question or search request.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print a machine-readable response.")
    args = parser.parse_args()
    try:
        answer = JobPulseAssistant().ask(args.question, args.top_k)
    except (FileNotFoundError, QueryValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(answer.to_dict(), indent=2))
    else:
        print(answer.answer)
        if answer.sources:
            print("\nSources:")
            for source in answer.sources:
                print(f"- {source['title']} at {source['company']} ({source['url'] or 'no URL'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
