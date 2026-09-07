#!/usr/bin/env python3
"""JobPulse - Comprehensive Model Evaluation Script.

Evaluates all six model components:
  1. Skill Extractor — precision/recall/F1
  2. Metadata Extractor — seniority/work-mode/employment accuracy
  3. Job Recommender — ranking accuracy
  4. RAG Retrieval — Precision@k, Recall@k, MRR
  5. Skill Normalizer — alias resolution accuracy
  6. Skill Matcher — match/score correctness

Usage:
    python scripts/evaluate_all_models.py
    python scripts/evaluate_all_models.py --samples 50
    python scripts/evaluate_all_models.py --no-rag
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.gold_standard import build_gold_set
from src.evaluation.skill_eval import evaluate_skill_extractor
from src.evaluation.metadata_eval import evaluate_metadata_extractor
from src.evaluation.recommender_eval import evaluate_job_recommender
from src.evaluation.rag_eval import evaluate_rag_retrieval
from src.evaluation.normalizer_eval import evaluate_skill_normalizer
from src.evaluation.matcher_eval import evaluate_skill_matcher
from src.evaluation.report import generate_csv, generate_markdown


def main():
    parser = argparse.ArgumentParser(description="Evaluate all JobPulse models")
    parser.add_argument("--samples", type=int, default=30,
                        help="Number of gold standard samples to use (default: 30)")
    parser.add_argument("--no-rag", action="store_true",
                        help="Skip RAG retrieval evaluation")
    parser.add_argument("--save-json", action="store_true",
                        help="Also save raw JSON results")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print("JobPulse Model Evaluation")
    print(f"Timestamp: {timestamp}")
    print("=" * 60)

    # 1. Build gold standard
    print("\n[1/7] Building gold standard set...")
    gold_set = build_gold_set(n_samples=args.samples)
    print(f"  Gold set size: {len(gold_set)} examples")

    results = {"timestamp": timestamp, "gold_set_size": len(gold_set)}

    # 2. Skill Extractor
    print("\n[2/7] Evaluating Skill Extractor...")
    results["skill_extractor"] = evaluate_skill_extractor(gold_set)
    sk = results["skill_extractor"]
    print(f"  Precision: {sk['precision']:.3f}  Recall: {sk['recall']:.3f}  F1: {sk['f1']:.3f}")

    # 3. Metadata Extractor
    print("\n[3/7] Evaluating Metadata Extractor...")
    results["metadata_extractor"] = evaluate_metadata_extractor(gold_set)
    md = results["metadata_extractor"]
    s_acc = md["seniority"]["accuracy"]
    w_acc = md["work_mode"]["accuracy"]
    e_acc = md["employment_type"]["accuracy"]
    print(f"  Seniority accuracy: {s_acc if s_acc is not None else 'N/A'}")
    print(f"  Work mode accuracy: {w_acc if w_acc is not None else 'N/A'}")
    print(f"  Employment type accuracy: {e_acc if e_acc is not None else 'N/A'}")

    # 4. Job Recommender
    print("\n[4/7] Evaluating Job Recommender...")
    results["job_recommender"] = evaluate_job_recommender()
    rec = results["job_recommender"]
    print(f"  Top-1 accuracy: {rec['top1_accuracy']:.3f} ({rec['top1_correct']}/{rec['n_candidates']})")
    print(f"  Mean rank of best: {rec['mean_rank_of_best']:.3f}")

    # 5. RAG Retrieval
    if not args.no_rag:
        print("\n[5/7] Evaluating RAG Retrieval...")
        results["rag_retrieval"] = evaluate_rag_retrieval()
        rag = results["rag_retrieval"]
        if rag.get("status") == "ok":
            print(f"  Avg MRR: {rag['avg_mrr']:.3f}")
            print(f"  Avg Precision@5: {rag['avg_precision_at_5']:.3f}")
            print(f"  Low-confidence rate: {rag['low_confidence_rate']:.3f}")
        else:
            print(f"  Status: {rag.get('status')} — {rag.get('error', '')}")
    else:
        print("\n[5/7] Skipping RAG Retrieval (--no-rag)")
        results["rag_retrieval"] = {"status": "skipped"}

    # 6. Skill Normalizer
    print("\n[6/7] Evaluating Skill Normalizer...")
    results["skill_normalizer"] = evaluate_skill_normalizer()
    norm = results["skill_normalizer"]
    print(f"  Accuracy: {norm['accuracy']:.3f} ({norm['correct']}/{norm['total']})")

    # 7. Skill Matcher
    print("\n[7/7] Evaluating Skill Matcher...")
    results["skill_matcher"] = evaluate_skill_matcher()
    matcher = results["skill_matcher"]
    print(f"  Match accuracy: {matcher['match_accuracy']:.3f}")
    print(f"  Score accuracy: {matcher['score_accuracy']:.3f}")

    # Generate reports
    print("\n" + "=" * 60)
    print("Generating reports...")
    csv_path = generate_csv(results, timestamp)
    md_path = generate_markdown(results, timestamp)
    print(f"  CSV:      {csv_path}")
    print(f"  Markdown: {md_path}")

    if args.save_json:
        json_dir = Path(PROJECT_ROOT) / "reports" / "eval"
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"evaluation_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  JSON:     {json_path}")

    print("\n" + "=" * 60)
    print("Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
