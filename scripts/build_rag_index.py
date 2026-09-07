#!/usr/bin/env python3
"""
JobPulse - Build the RAG vector index from the latest NLP output.

Run from anywhere with:
    python scripts/build_rag_index.py
    python scripts/build_rag_index.py --embedder tfidf   # force offline TF-IDF
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import JobPulseRAG


def main():
    parser = argparse.ArgumentParser(description="Build the JobPulse RAG index")
    parser.add_argument(
        "--embedder", choices=["auto", "sentence-transformer", "tfidf"], default="auto",
        help="Embedding backend (default: auto — tries sentence-transformers, "
             "falls back to TF-IDF if unavailable/offline)",
    )
    args = parser.parse_args()

    rag = JobPulseRAG()
    rag.build(embedder_prefer=args.embedder)
    print(f"\n✓ RAG index saved to: {rag.store.index_dir}")
    print(f"  Documents indexed: {rag.store.vectors.shape[0]:,}")
    print(f"  Embedder backend: {rag.store.embedder.name}")


if __name__ == "__main__":
    main()
