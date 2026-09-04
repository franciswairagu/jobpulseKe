#!/usr/bin/env python3
"""
JobPulse - Stage 3 (v2): NLP Enrichment Entry Point

Run from anywhere with:
    python scripts/run_nlp_extraction.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.nlpv2 import run_nlp_extraction_v2


def main():
    df, summary = run_nlp_extraction_v2()
    return df


if __name__ == "__main__":
    main()
