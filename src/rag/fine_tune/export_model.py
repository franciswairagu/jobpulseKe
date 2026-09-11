"""Export fine-tuned model to Ollama format."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "src" / "models" / "fine_tuned"
OLLAMA_MODEL_NAME = "jobpulse-finetuned"


class ModelExporter:
    """Export fine-tuned model to Ollama-compatible format."""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    def merge_adapters(
        self,
        base_model="Qwen/Qwen2.5-1.5B",
        adapter_dir=None,
        merged_output_dir=None,
    ):
        """Merge LoRA adapters with the base model."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        if adapter_dir is None:
            adapter_dir = self.output_dir / "adapter"
        if merged_output_dir is None:
            merged_output_dir = self.output_dir / "merged"

        merged_output_dir.mkdir(parents=True, exist_ok=True)

        import torch
        logger.info("Loading base model: %s", base_model)
        tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(
            base_model, torch_dtype=dtype, trust_remote_code=True
        )

        logger.info("Loading adapter from: %s", adapter_dir)
        model = PeftModel.from_pretrained(model, str(adapter_dir))

        logger.info("Merging adapters...")
        model = model.merge_and_unload()

        logger.info("Saving merged model to: %s", merged_output_dir)
        model.save_pretrained(str(merged_output_dir))
        tokenizer.save_pretrained(str(merged_output_dir))

        logger.info("Merge complete")
        return merged_output_dir

    def convert_to_gguf(
        self,
        merged_model_dir=None,
        output_gguf=None,
        quantization="q4_k_m",
    ):
        """Convert merged model to GGUF format using llama.cpp."""
        if merged_model_dir is None:
            merged_model_dir = self.output_dir / "merged"
        if output_gguf is None:
            output_gguf = self.output_dir / f"jobpulse-finetuned-{quantization}.gguf"

        convert_script = Path("llama.cpp/convert_hf_to_gguf.py")
        if not convert_script.exists():
            logger.warning("llama.cpp not found. Using ctransformers fallback.")
            return self._convert_with_ctransformers(merged_model_dir, output_gguf)

        logger.info("Converting to GGUF with quantization: %s", quantization)
        cmd = [
            "python", str(convert_script),
            str(merged_model_dir),
            "--outfile", str(output_gguf),
            "--outtype", "f16",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"GGUF conversion failed: {result.stderr}")

        logger.info("GGUF model saved to: %s", output_gguf)
        return output_gguf

    def _convert_with_ctransformers(self, model_dir, output_gguf):
        """Fallback conversion using ctransformers."""
        from ctransformers import AutoModelForCausalLM as CTAutoModel
        model = CTAutoModel.from_pretrained(str(model_dir), model_type="qwen2")
        model.save(str(output_gguf))
        logger.info("GGUF model saved to: %s", output_gguf)
        return output_gguf

    def create_modelfile(self, gguf_path=None, modelfile_path=None):
        """Create Ollama Modelfile for the fine-tuned model."""
        if gguf_path is None:
            gguf_path = self.output_dir / "jobpulse-finetuned-q4_k_m.gguf"
        if modelfile_path is None:
            modelfile_path = self.output_dir / "Modelfile"

        system_prompt = (
            "You are JobPulse Assistant, an AI helper for the African tech job market. "
            "Answer questions about tech jobs, skills, careers, and market trends across Africa. "
            "Use ONLY the provided context. Be concise, cite sources, and end with a practical recommendation."
        )

        # Read the template from a separate file to avoid escaping issues
        template_path = Path(__file__).parent / "modelfile_template.txt"
        if template_path.exists():
            template = template_path.read_text()
        else:
            # Fallback: simple Modelfile
            template = f"FROM {gguf_path}\n\nSYSTEM {repr(system_prompt)}\n\nPARAMETER temperature 0.3\nPARAMETER top_p 0.9\nPARAMETER num_ctx 4096"

        modelfile_path.parent.mkdir(parents=True, exist_ok=True)
        modelfile_path.write_text(template)
        logger.info("Modelfile written to: %s", modelfile_path)
        return modelfile_path

    def register_in_ollama(
        self,
        gguf_path=None,
        model_name=OLLAMA_MODEL_NAME,
    ):
        """Register the fine-tuned model in Ollama."""
        modelfile_path = self.create_modelfile(gguf_path)

        logger.info("Creating Ollama model: %s", model_name)
        cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Ollama create failed: {result.stderr}")

        logger.info("Model %s registered in Ollama", model_name)
        return model_name

    def export_full_pipeline(
        self,
        base_model="Qwen/Qwen2.5-1.5B",
        model_name=OLLAMA_MODEL_NAME,
    ):
        """Run the full export pipeline: merge -> Ollama."""
        logger.info("Starting full export pipeline...")

        # Step 1: Merge adapters
        merged_dir = self.merge_adapters(base_model=base_model)

        # Step 2: Try GGUF conversion, skip if not available
        try:
            gguf_path = self.convert_to_gguf(merged_model_dir=merged_dir)
            self.register_in_ollama(gguf_path=gguf_path, model_name=model_name)
            logger.info("Export pipeline complete. Model available as: %s", model_name)
        except Exception as e:
            logger.warning("GGUF conversion failed: %s", e)
            logger.info("Merged model saved to: %s", merged_dir)
            logger.info("To use with Ollama, convert manually or use transformers+peft directly.")
        return model_name
