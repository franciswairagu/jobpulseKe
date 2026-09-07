#!/usr/bin/env python3
"""
JobPulse - Evaluate the Stage 3 NLP pipeline.

Runs three checks: coverage over the real enriched dataset, title/seniority
rule-based consistency, and precision/recall/F1 against a synthetic gold set.
See src/nlp/evaluation.py for details on why three checks instead of one score.

Usage:
    python scripts/evaluate_nlp.py
    python scripts/evaluate_nlp.py --save   # also write data/nlp/evaluation/*.json
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.evaluation import run_evaluation


def main():
    parser = argparse.ArgumentParser(description="Evaluate the JobPulse NLP pipeline")
    parser.add_argument("--save", action="store_true",
                         help="Also save the evaluation as JSON under data/nlp/evaluation/")
    args = parser.parse_args()
    run_evaluation(save=args.save)


if __name__ == "__main__":
    main()
