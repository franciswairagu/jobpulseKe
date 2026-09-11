#!/usr/bin/env python3
"""Fine-tune the JobPulse RAG model.

Usage:
    python scripts/fine_tune_model.py [--generate-data] [--train] [--export] [--check-deps]
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import NLP_DATA_DIR, RAG_DATA_DIR
from src.rag.fine_tune.data_generator import TrainingDataGenerator
from src.rag.fine_tune.training_data import TrainingDataManager, load_sample_manual_pairs
from src.rag.fine_tune.trainer import JobPulseTrainer
from src.rag.fine_tune.export_model import ModelExporter

FINE_TUNING_DIR = RAG_DATA_DIR / "fine_tuning"


def check_dependencies():
    """Check if fine-tuning dependencies are installed."""
    print("Checking dependencies...")
    deps = {
        "torch": False,
        "transformers": False,
        "peft": False,
        "trl": False,
        "datasets": False,
        "accelerate": False,
        "sentence_transformers": False,
        "chromadb": False,
    }

    for pkg in deps:
        try:
            __import__(pkg)
            deps[pkg] = True
        except ImportError:
            pass

    for pkg, installed in deps.items():
        status = "OK" if installed else "MISSING"
        print(f"  {pkg}: {status}")

    missing = [pkg for pkg, installed in deps.items() if not installed]
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    return True


def generate_training_data():
    """Generate training data from job postings."""
    print("\n=== Generating Training Data ===")

    # Find latest NLP output
    from src.nlp.nlpv2 import latest_nlp_output
    nlp_output = latest_nlp_output()

    if nlp_output is None or not nlp_output.exists():
        print("No NLP output found. Run NLP extraction first.")
        return None

    print(f"Using NLP output: {nlp_output}")

    # Generate auto pairs
    generator = TrainingDataGenerator(seed=42)
    auto_output = FINE_TUNING_DIR / "auto_generated_pairs.json"
    auto_pairs = generator.generate_from_parquet(
        nlp_output,
        max_pairs_per_job=2,
        output_path=auto_output,
    )
    print(f"Generated {len(auto_pairs)} auto pairs")

    # Create manual pairs
    manager = TrainingDataManager(data_dir=FINE_TUNING_DIR)
    if not manager.pairs:
        print("Adding sample manual pairs...")
        sample = load_sample_manual_pairs()
        manager.add_batch(sample)
        manager.save()
    print(f"Manual pairs: {len(manager.pairs)}")

    # Merge
    chatml_pairs = generator.generate_chatml_format(auto_pairs)
    manual_chatml = manager.to_chatml()
    all_pairs = manual_chatml + chatml_pairs

    merged_output = FINE_TUNING_DIR / "merged_training_data.json"
    merged_output.parent.mkdir(parents=True, exist_ok=True)
    with open(merged_output, "w") as f:
        json.dump(all_pairs, f, indent=2)
    print(f"Merged training data: {len(all_pairs)} pairs -> {merged_output}")

    return all_pairs


def train_model():
    """Run fine-tuning."""
    print("\n=== Training Model ===")

    trainer = JobPulseTrainer()

    # Check deps
    deps = trainer.check_dependencies()
    if not deps.get("torch"):
        print("PyTorch is required for training")
        return None

    # Load training data
    data_file = FINE_TUNING_DIR / "merged_training_data.json"
    if not data_file.exists():
        print("No training data found. Run --generate-data first.")
        return None

    with open(data_file, "r") as f:
        training_data = json.load(f)

    print(f"Training on {len(training_data)} pairs")

    # Train
    metrics = trainer.train(training_data)
    print(f"Training complete. Loss: {metrics.get('train_loss', 'N/A')}")
    print(f"Adapter saved to: {metrics.get('adapter_dir', 'N/A')}")

    return metrics


def export_model():
    """Export fine-tuned model to Ollama."""
    print("\n=== Exporting Model ===")

    exporter = ModelExporter()
    try:
        model_name = exporter.export_full_pipeline()
        print(f"Model exported: {model_name}")
        return model_name
    except Exception as e:
        print(f"Export failed: {e}")
        print("Note: Export requires llama.cpp or ctransformers")
        return None


def main():
    parser = argparse.ArgumentParser(description="Fine-tune JobPulse model")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--generate-data", action="store_true", help="Generate training data")
    parser.add_argument("--train", action="store_true", help="Train the model")
    parser.add_argument("--export", action="store_true", help="Export to Ollama")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.check_deps:
        check_dependencies()
        return

    if not any([args.generate_data, args.train, args.export, args.all]):
        parser.print_help()
        return

    if args.all or args.generate_data:
        generate_training_data()

    if args.all or args.train:
        train_model()

    if args.all or args.export:
        export_model()


if __name__ == "__main__":
    main()