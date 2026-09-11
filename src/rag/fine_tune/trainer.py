"""Fine-tune qwen2.5:1.5b using QLoRA for the JobPulse domain.

Uses unsloth for efficient fine-tuning with LoRA adapters.
Outputs adapter weights that can be merged and exported to Ollama.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_TRAINING_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "rag" / "fine_tuning"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "src" / "models" / "fine_tuned"
BASE_MODEL_NAME = "Qwen/Qwen2.5-1.5B"
FINETUNED_MODEL_NAME = "jobpulse-finetuned"

# Training hyperparameters
DEFAULT_CONFIG = {
    "base_model": BASE_MODEL_NAME,
    "output_dir": str(DEFAULT_OUTPUT_DIR),
    "max_seq_length": 2048,
    "lora_rank": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "learning_rate": 2e-4,
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 4,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "logging_steps": 50,
    "save_steps": 500,
    "fp16": True,
    "bf16": False,
    "optim": "adamw_8bit",
}


class JobPulseTrainer:
    """Fine-tune qwen2.5:1.5b with QLoRA for JobPulse domain."""

    def __init__(self, config: dict | None = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.output_dir = Path(self.config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_dependencies(self) -> dict[str, bool]:
        """Check if required packages are installed."""
        deps = {}
        try:
            import torch
            deps["torch"] = True
            deps["cuda"] = torch.cuda.is_available()
        except ImportError:
            deps["torch"] = False
            deps["cuda"] = False

        for pkg in ["transformers", "peft", "trl", "datasets", "accelerate"]:
            try:
                __import__(pkg)
                deps[pkg] = True
            except ImportError:
                deps[pkg] = False

        try:
            import unsloth
            deps["unsloth"] = True
        except ImportError:
            deps["unsloth"] = False

        return deps

    def prepare_training_data(
        self,
        auto_pairs_path: Path | None = None,
        manual_pairs_path: Path | None = None,
    ) -> list[dict]:
        """Load and merge auto-generated and manual training pairs."""
        all_pairs = []

        if auto_pairs_path and auto_pairs_path.exists():
            with open(auto_pairs_path, "r") as f:
                auto_pairs = json.load(f)
            logger.info("Loaded %d auto-generated pairs", len(auto_pairs))
            all_pairs.extend(auto_pairs)

        if manual_pairs_path and manual_pairs_path.exists():
            with open(manual_pairs_path, "r") as f:
                manual_pairs = json.load(f)
            logger.info("Loaded %d manual pairs", len(manual_pairs))
            all_pairs.extend(manual_pairs)

        if not all_pairs:
            logger.warning("No training data found. Generating sample data...")
            from src.rag.fine_tune.training_data import load_sample_manual_pairs
            sample = load_sample_manual_pairs()
            for pair in sample:
                all_pairs.append({
                    "messages": [
                        {"role": "system", "content": "You are JobPulse Assistant."},
                        {"role": "user", "content": pair["question"]},
                        {"role": "assistant", "content": pair["answer"]},
                    ],
                    "question_type": pair.get("category", "general"),
                })

        logger.info("Total training pairs: %d", len(all_pairs))
        return all_pairs

    def train(
        self,
        training_data: list[dict],
        resume_from_checkpoint: str | None = None,
    ) -> dict[str, Any]:
        """Run QLoRA fine-tuning. Returns training metrics."""
        deps = self.check_dependencies()

        if not deps.get("torch"):
            raise ImportError("PyTorch is required. Install with: pip install torch")
        if not deps.get("transformers"):
            raise ImportError("transformers is required. Install with: pip install transformers")
        if not deps.get("peft"):
            raise ImportError("peft is required. Install with: pip install peft")
        if not deps.get("trl"):
            raise ImportError("trl is required. Install with: pip install trl")

        logger.info("Starting fine-tuning with config: %s", self.config)

        try:
            return self._train_with_unsloth(training_data, resume_from_checkpoint)
        except ImportError:
            logger.warning("unsloth not available, falling back to standard training")
            return self._train_standard(training_data, resume_from_checkpoint)

    def _train_with_unsloth(
        self,
        training_data: list[dict],
        resume_from_checkpoint: str | None = None,
    ) -> dict[str, Any]:
        """Train using unsloth for maximum efficiency."""
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import Dataset

        logger.info("Loading base model with unsloth: %s", self.config["base_model"])

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.config["base_model"],
            max_seq_length=self.config["max_seq_length"],
            dtype=None,
            load_in_4bit=True,
        )

        model = FastLanguageModel.get_peft_model(
            model,
            r=self.config["lora_rank"],
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                           "gate_proj", "up_proj", "down_proj"],
            lora_alpha=self.config["lora_alpha"],
            lora_dropout=self.config["lora_dropout"],
            bias="none",
            use_gradient_checkpointing="unsloth",
        )

        dataset = Dataset.from_list(training_data)

        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=self.config["num_train_epochs"],
            per_device_train_batch_size=self.config["per_device_train_batch_size"],
            gradient_accumulation_steps=self.config["gradient_accumulation_steps"],
            learning_rate=self.config["learning_rate"],
            warmup_steps=self.config["warmup_steps"],
            weight_decay=self.config["weight_decay"],
            logging_steps=self.config["logging_steps"],
            save_steps=self.config["save_steps"],
            fp16=self.config["fp16"],
            bf16=self.config["bf16"],
            optim=self.config["optim"],
            save_total_limit=3,
            report_to="none",
        )

        def formatting_func(examples):
            """Format messages for SFTTrainer."""
            # Handle both batched and single example formats
            messages_list = examples.get("messages", [])
            if messages_list and isinstance(messages_list[0], dict):
                # Single example: messages is a list of message dicts
                text = tokenizer.apply_chat_template(messages_list, tokenize=False, add_generation_prompt=False)
                return [text]
            # Batched: messages is a list of lists
            outputs = []
            for messages in messages_list:
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                outputs.append(text)
            return outputs

        try:
            trainer = SFTTrainer(
                model=model,
                processing_class=tokenizer,
                train_dataset=dataset,
                formatting_func=formatting_func,
                args=training_args,
            )
        except TypeError:
            # Older trl/unsloth versions use 'tokenizer' parameter
            trainer = SFTTrainer(
                model=model,
                tokenizer=tokenizer,
                train_dataset=dataset,
                formatting_func=formatting_func,
                args=training_args,
            )

        logger.info("Starting training...")
        train_result = trainer.train(resume_from_checkpoint=resume_from_checkpoint)

        # Save adapter
        adapter_dir = self.output_dir / "adapter"
        adapter_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))

        # Save training metrics
        metrics = {
            "train_loss": train_result.training_loss,
            "train_runtime": train_result.metrics.get("train_runtime", 0),
            "train_samples_per_second": train_result.metrics.get("train_samples_per_second", 0),
            "total_steps": train_result.global_step,
            "adapter_dir": str(adapter_dir),
        }

        metrics_path = self.output_dir / "training_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info("Training complete. Adapter saved to %s", adapter_dir)
        return metrics

    def _train_standard(
        self,
        training_data: list[dict],
        resume_from_checkpoint: str | None = None,
    ) -> dict[str, Any]:
        """Train using standard transformers + peft (without unsloth)."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from peft import LoraConfig, get_peft_model
        from trl import SFTTrainer
        from datasets import Dataset

        logger.info("Loading base model: %s", self.config["base_model"])

        tokenizer = AutoTokenizer.from_pretrained(
            self.config["base_model"],
            trust_remote_code=True,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Determine dtype based on available hardware
        if torch.cuda.is_available():
            dtype = torch.float16
            device_map = "auto"
        else:
            dtype = torch.float32
            device_map = None

        model = AutoModelForCausalLM.from_pretrained(
            self.config["base_model"],
            torch_dtype=dtype,
            device_map=device_map,
            trust_remote_code=True,
        )

        # Enable gradient checkpointing for memory efficiency
        model.gradient_checkpointing_enable()

        lora_config = LoraConfig(
            r=self.config["lora_rank"],
            lora_alpha=self.config["lora_alpha"],
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=self.config["lora_dropout"],
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)

        def formatting_func(examples):
            """Format messages for SFTTrainer."""
            # Handle both batched and single example formats
            messages_list = examples.get("messages", [])
            if messages_list and isinstance(messages_list[0], dict):
                # Single example: messages is a list of message dicts
                text = tokenizer.apply_chat_template(messages_list, tokenize=False, add_generation_prompt=False)
                return [text]
            # Batched: messages is a list of lists
            outputs = []
            for messages in messages_list:
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                outputs.append(text)
            return outputs

        dataset = Dataset.from_list(training_data)

        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=self.config["num_train_epochs"],
            per_device_train_batch_size=self.config["per_device_train_batch_size"],
            gradient_accumulation_steps=self.config["gradient_accumulation_steps"],
            learning_rate=self.config["learning_rate"],
            warmup_steps=self.config["warmup_steps"],
            weight_decay=self.config["weight_decay"],
            logging_steps=self.config["logging_steps"],
            save_steps=self.config["save_steps"],
            fp16=self.config["fp16"],
            optim=self.config["optim"],
            save_total_limit=3,
            report_to="none",
        )

        try:
            trainer = SFTTrainer(
                model=model,
                processing_class=tokenizer,
                train_dataset=dataset,
                formatting_func=formatting_func,
                args=training_args,
            )
        except TypeError:
            trainer = SFTTrainer(
                model=model,
                tokenizer=tokenizer,
                train_dataset=dataset,
                formatting_func=formatting_func,
                args=training_args,
            )

        logger.info("Starting training...")
        train_result = trainer.train(resume_from_checkpoint=resume_from_checkpoint)

        adapter_dir = self.output_dir / "adapter"
        adapter_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))

        metrics = {
            "train_loss": train_result.training_loss,
            "train_runtime": train_result.metrics.get("train_runtime", 0),
            "total_steps": train_result.global_step,
            "adapter_dir": str(adapter_dir),
        }

        metrics_path = self.output_dir / "training_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info("Training complete. Adapter saved to %s", adapter_dir)
        return metrics
