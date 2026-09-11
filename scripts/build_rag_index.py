#!/usr/bin/env python3
"""Build the ChromaDB RAG index from NLP-enriched job data.

Usage:
    python scripts/build_rag_index.py [--rebuild] [--stats]
"""
import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAG_DATA_DIR
from src.rag.vector_store import JobVectorStore
from src.nlp.nlpv2 import latest_nlp_output


def main():
    parser = argparse.ArgumentParser(description="Build RAG index")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild")
    parser.add_argument("--stats", action="store_true", help="Show stats only")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    store = JobVectorStore(persist_dir=RAG_DATA_DIR)

    if args.stats:
        if store.exists():
            stats = store.get_metadata_stats()
            print(f"Index stats: {stats}")
        else:
            print("No index found")
        return

    if store.exists() and not args.rebuild:
        print("Index already exists. Use --rebuild to recreate.")
        print(f"Documents: {store.count()}")
        return

    nlp_output = latest_nlp_output()
    if nlp_output is None or not nlp_output.exists():
        print("No NLP output found. Run NLP extraction first:")
        print("  python src/nlp/nlpv2.py")
        sys.exit(1)

    print(f"Building index from: {nlp_output}")
    import pandas as pd
    df = pd.read_parquet(nlp_output)
    print(f"Loaded {len(df)} records")

    store.clear()
    count = store.build(df)
    print(f"Index built: {count} documents")

    stats = store.get_metadata_stats()
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()
