"""Generate CSV + Markdown evaluation reports with regression comparison."""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports" / "eval"
PREV_EVAL_DIR = Path(__file__).resolve().parents[2] / "data" / "nlp" / "evaluation"


def _find_previous_eval() -> Optional[Dict[str, Any]]:
    """Find the most recent evaluation JSON from the existing NLP evaluator."""
    if not PREV_EVAL_DIR.exists():
        return None
    json_files = sorted(PREV_EVAL_DIR.glob("nlp_evaluation_*.json"), reverse=True)
    if not json_files:
        return None
    try:
        with open(json_files[0]) as f:
            return json.load(f)
    except Exception:
        return None


def _status_emoji(current: float, previous: Optional[float], higher_is_better: bool = True) -> str:
    """Return a status indicator based on comparison with previous score."""
    if previous is None:
        return "  (new)"
    delta = current - previous
    if abs(delta) < 0.005:
        return "  (same)"
    if higher_is_better:
        return "  (UP)" if delta > 0 else "  (DOWN)"
    else:
        return "  (DOWN)" if delta > 0 else "  (UP)"


def generate_csv(results: Dict[str, Any], timestamp: str) -> Path:
    """Write flat CSV with one row per model × metric."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORTS_DIR / f"evaluation_{timestamp}.csv"

    rows = []
    for model_name, data in results.items():
        if model_name in ("timestamp", "gold_set_size"):
            continue
        if not isinstance(data, dict):
            continue
        if data.get("status") == "error":
            rows.append({"model": model_name, "metric": "status", "value": "error", "detail": data.get("error", "")})
            continue

        if model_name == "skill_extractor":
            rows.append({"model": model_name, "metric": "precision", "value": data.get("precision"), "detail": ""})
            rows.append({"model": model_name, "metric": "recall", "value": data.get("recall"), "detail": ""})
            rows.append({"model": model_name, "metric": "f1", "value": data.get("f1"), "detail": ""})
            for cat, cat_data in data.get("category_f1", {}).items():
                rows.append({"model": model_name, "metric": f"f1_{cat}", "value": cat_data["f1"], "detail": f"p={cat_data['precision']}, r={cat_data['recall']}"})

        elif model_name == "metadata_extractor":
            for field in ["seniority", "work_mode", "employment_type"]:
                field_data = data.get(field, {})
                rows.append({"model": model_name, "metric": f"{field}_accuracy", "value": field_data.get("accuracy"), "detail": f"n={field_data.get('total', 0)}"})

        elif model_name == "job_recommender":
            rows.append({"model": model_name, "metric": "top1_accuracy", "value": data.get("top1_accuracy"), "detail": ""})
            rows.append({"model": model_name, "metric": "mean_rank_of_best", "value": data.get("mean_rank_of_best"), "detail": ""})

        elif model_name == "rag_retrieval":
            rows.append({"model": model_name, "metric": "avg_precision_at_3", "value": data.get("avg_precision_at_3"), "detail": ""})
            rows.append({"model": model_name, "metric": "avg_precision_at_5", "value": data.get("avg_precision_at_5"), "detail": ""})
            rows.append({"model": model_name, "metric": "avg_recall_at_5", "value": data.get("avg_recall_at_5"), "detail": ""})
            rows.append({"model": model_name, "metric": "avg_mrr", "value": data.get("avg_mrr"), "detail": ""})
            rows.append({"model": model_name, "metric": "low_confidence_rate", "value": data.get("low_confidence_rate"), "detail": ""})

        elif model_name == "skill_normalizer":
            rows.append({"model": model_name, "metric": "accuracy", "value": data.get("accuracy"), "detail": f"{data.get('correct')}/{data.get('total')}"})
            rows.append({"model": model_name, "metric": "batch_normalize_correct", "value": 1 if data.get("batch_normalize_correct") else 0, "detail": ""})

        elif model_name == "skill_matcher":
            rows.append({"model": model_name, "metric": "match_accuracy", "value": data.get("match_accuracy"), "detail": ""})
            rows.append({"model": model_name, "metric": "score_accuracy", "value": data.get("score_accuracy"), "detail": ""})

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "metric", "value", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info("CSV report saved to %s", csv_path)
    return csv_path


def generate_markdown(results: Dict[str, Any], timestamp: str) -> Path:
    """Write human-readable Markdown report with recommendations."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / f"evaluation_{timestamp}.md"

    prev_eval = _find_previous_eval()
    lines = [
        f"# JobPulse Model Evaluation Report",
        f"",
        f"**Date:** {timestamp}",
        f"**Gold set size:** {results.get('gold_set_size', 'N/A')}",
        f"",
    ]

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Model | Key Metric | Score | Status |")
    lines.append("|-------|-----------|-------|--------|")

    def add_summary_row(model: str, metric: str, value, higher_is_better: bool = True):
        if value is None:
            lines.append(f"| {model} | {metric} | N/A | - |")
            return
        prev_val = None
        if prev_eval and model in prev_eval:
            prev_data = prev_eval[model]
            if isinstance(prev_data, dict) and metric in prev_data:
                prev_val = prev_data[metric]
        status = _status_emoji(value, prev_val, higher_is_better)
        lines.append(f"| {model} | {metric} | {value:.3f} |{status}|")

    sk = results.get("skill_extractor", {})
    add_summary_row("Skill Extractor", "F1", sk.get("f1"))

    md = results.get("metadata_extractor", {})
    add_summary_row("Metadata Extractor", "Seniority Accuracy", md.get("seniority", {}).get("accuracy"))
    add_summary_row("Metadata Extractor", "Work Mode Accuracy", md.get("work_mode", {}).get("accuracy"))

    rec = results.get("job_recommender", {})
    add_summary_row("Job Recommender", "Top-1 Accuracy", rec.get("top1_accuracy"))

    rag = results.get("rag_retrieval", {})
    add_summary_row("RAG Retrieval", "MRR", rag.get("avg_mrr"))

    norm = results.get("skill_normalizer", {})
    add_summary_row("Skill Normalizer", "Accuracy", norm.get("accuracy"))

    matcher = results.get("skill_matcher", {})
    add_summary_row("Skill Matcher", "Match Accuracy", matcher.get("match_accuracy"))

    lines.append("")

    # Detailed sections
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")

    # Skill Extractor
    if sk:
        lines.append("### Skill Extractor")
        lines.append(f"- **Precision:** {sk.get('precision', 'N/A')}")
        lines.append(f"- **Recall:** {sk.get('recall', 'N/A')}")
        lines.append(f"- **F1:** {sk.get('f1', 'N/A')}")
        lines.append(f"- **Total TP/FP/FN:** {sk.get('total_tp', 0)}/{sk.get('total_fp', 0)}/{sk.get('total_fn', 0)}")
        if sk.get("top_missed_skills"):
            lines.append(f"- **Top missed skills:** {', '.join(s[0] for s in sk['top_missed_skills'][:5])}")
        if sk.get("top_spurious_skills"):
            lines.append(f"- **Top spurious skills:** {', '.join(s[0] for s in sk['top_spurious_skills'][:5])}")
        if sk.get("category_f1"):
            lines.append("- **Per-category F1:**")
            for cat, cat_data in sorted(sk["category_f1"].items(), key=lambda x: x[1]["f1"]):
                lines.append(f"  - {cat}: {cat_data['f1']} (p={cat_data['precision']}, r={cat_data['recall']}, n={cat_data['support']})")
        lines.append("")

    # Metadata Extractor
    if md:
        lines.append("### Metadata Extractor")
        for field in ["seniority", "work_mode", "employment_type"]:
            field_data = md.get(field, {})
            acc = field_data.get("accuracy")
            if acc is not None:
                lines.append(f"- **{field} accuracy:** {acc} (n={field_data.get('total', 0)})")
                confusion = field_data.get("confusion", {})
                if confusion:
                    lines.append(f"  - Confusion: {confusion}")
            else:
                lines.append(f"- **{field}:** No labeled data")
        lines.append("")

    # Job Recommender
    if rec:
        lines.append("### Job Recommender")
        lines.append(f"- **Top-1 accuracy:** {rec.get('top1_accuracy', 'N/A')} ({rec.get('top1_correct', 0)}/{rec.get('n_candidates', 0)})")
        lines.append(f"- **Mean rank of best job:** {rec.get('mean_rank_of_best', 'N/A')}")
        lines.append(f"- **Component coverage:** {rec.get('component_coverage', {})}")
        lines.append("")

    # RAG Retrieval
    if rag and rag.get("status") == "ok":
        lines.append("### RAG Retrieval")
        lines.append(f"- **Avg Precision@3:** {rag.get('avg_precision_at_3', 'N/A')}")
        lines.append(f"- **Avg Precision@5:** {rag.get('avg_precision_at_5', 'N/A')}")
        lines.append(f"- **Avg Recall@5:** {rag.get('avg_recall_at_5', 'N/A')}")
        lines.append(f"- **Avg MRR:** {rag.get('avg_mrr', 'N/A')}")
        lines.append(f"- **Low-confidence rate:** {rag.get('low_confidence_rate', 'N/A')}")
        lines.append("")
    elif rag and rag.get("status") == "error":
        lines.append("### RAG Retrieval")
        lines.append(f"- **Status:** Error — {rag.get('error', 'unknown')}")
        lines.append("")

    # Skill Normalizer
    if norm:
        lines.append("### Skill Normalizer")
        lines.append(f"- **Accuracy:** {norm.get('accuracy', 'N/A')} ({norm.get('correct', 0)}/{norm.get('total', 0)})")
        lines.append(f"- **Batch normalize correct:** {norm.get('batch_normalize_correct', 'N/A')}")
        if norm.get("failures"):
            lines.append("- **Failures:**")
            for f in norm["failures"]:
                lines.append(f"  - `{f['input']}` -> expected `{f['expected']}`, got `{f['actual']}`")
        lines.append("")

    # Skill Matcher
    if matcher:
        lines.append("### Skill Matcher")
        lines.append(f"- **Match accuracy:** {matcher.get('match_accuracy', 'N/A')} ({matcher.get('correct_matches', 0)}/{matcher.get('total', 0)})")
        lines.append(f"- **Score accuracy:** {matcher.get('score_accuracy', 'N/A')} ({matcher.get('correct_scores', 0)}/{matcher.get('total', 0)})")
        if matcher.get("failures"):
            lines.append("- **Failures:**")
            for f in matcher["failures"][:5]:
                lines.append(f"  - candidate={f['candidate_skills']}, job={f['job_skills']}")
                lines.append(f"    expected matched={f['expected_matched']}, got={f['actual_matched']}")
        lines.append("")

    # Regression comparison
    if prev_eval:
        lines.append("---")
        lines.append("")
        lines.append("## Regression vs Previous Evaluation")
        lines.append("")
        lines.append("| Model | Metric | Previous | Current | Delta |")
        lines.append("|-------|--------|----------|---------|-------|")

        def add_regression_row(model: str, metric: str, current):
            if current is None:
                return
            prev_data = prev_eval.get(model, {})
            if isinstance(prev_data, dict) and metric in prev_data:
                prev_val = prev_data[metric]
                if prev_val is not None:
                    delta = current - prev_val
                    delta_str = f"+{delta:.3f}" if delta >= 0 else f"{delta:.3f}"
                    lines.append(f"| {model} | {metric} | {prev_val:.3f} | {current:.3f} | {delta_str} |")

        add_regression_row("skill_extractor", "f1", sk.get("f1"))
        add_regression_row("metadata_extractor", "seniority_accuracy", md.get("seniority", {}).get("accuracy"))
        add_regression_row("rag_retrieval", "avg_mrr", rag.get("avg_mrr"))
        lines.append("")

    # Recommendations
    lines.append("---")
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")

    # Auto-generate recommendations based on scores
    recommendations = []
    if sk.get("f1", 1) < 0.7:
        recommendations.append("- **Skill Extractor F1 is low** — Consider expanding the taxonomy or improving regex patterns for missed skills.")
    if sk.get("recall", 1) < 0.6:
        recommendations.append("- **Skill Extractor recall is low** — Many skills in job descriptions are not being captured. Review top missed skills list.")
    if sk.get("precision", 1) < 0.7:
        recommendations.append("- **Skill Extractor precision is low** — Too many false positives. Review word-boundary matching patterns.")
    if md.get("seniority", {}).get("accuracy", 1) < 0.8:
        recommendations.append("- **Metadata seniority accuracy is low** — Review seniority keyword patterns.")
    if rec.get("top1_accuracy", 1) < 0.6:
        recommendations.append("- **Job Recommender top-1 accuracy is low** — Consider tuning the hybrid scoring weights.")
    if rag.get("avg_mrr", 1) < 0.5:
        recommendations.append("- **RAG retrieval MRR is low** — Consider fine-tuning embeddings or improving the rag_document format.")
    if norm.get("accuracy", 1) < 1.0:
        recommendations.append("- **Skill Normalizer has misses** — Add missing aliases to SKILL_ALIASES dict.")
    if matcher.get("match_accuracy", 1) < 1.0:
        recommendations.append("- **Skill Matcher has issues** — Review normalization pipeline for edge cases.")

    if not recommendations:
        recommendations.append("- All models performing within acceptable ranges. Consider expanding the gold set for more robust evaluation.")

    lines.extend(recommendations)
    lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    logger.info("Markdown report saved to %s", md_path)
    return md_path
