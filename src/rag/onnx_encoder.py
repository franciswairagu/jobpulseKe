"""
ONNX Runtime encoder for all-MiniLM-L6-v2.

Why this exists
---------------
`sentence-transformers` hard-requires `torch` (>=2.2), and torch is ~1GB+
installed — too heavy for the deployment images (Render/Railway free tiers
were the reason `sentence-transformers` was dropped from the backend
requirements in 80dfb16). This module gives the *same* embeddings with no
torch at all: ONNX Runtime (~40MB) + the transformers tokenizer.

It runs the official ONNX export of `sentence-transformers/all-MiniLM-L6-v2`
(`Xenova/all-MiniLM-L6-v2` on the HF hub) with the exact same pooling
sentence-transformers uses (attention-masked mean pooling + L2 normalize),
so vectors are interchangeable with the torch-built index: a query embedded
here can search an index built by sentence-transformers and vice versa.

Model files are resolved in this order:

  1. ``$RAG_ONNX_MODEL_DIR``            (explicit override)
  2. ``/app/onnx_model``                (baked into the Docker image at build)
  3. ``~/.cache/jobpulse/onnx-models/`` (downloaded on first use)

`prefetch_model()` is what the Dockerfile calls at build time so the image
starts offline-capable.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ONNX export of sentence-transformers/all-MiniLM-L6-v2 (same weights).
DEFAULT_ONNX_REPO = "Xenova/all-MiniLM-L6-v2"
HF_MODEL_NAME = "all-MiniLM-L6-v2"

# Files AutoTokenizer needs, plus the ONNX graph itself.
TOKENIZER_FILES = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.txt",
]
ONNX_FILE = "onnx/model.onnx"

BAKED_MODEL_DIR = "/app/onnx_model"


def onnx_available() -> bool:
    """True when the ONNX stack (onnxruntime + transformers) is installed."""
    try:
        import onnxruntime  # noqa: F401
        import transformers  # noqa: F401
    except Exception:
        return False
    return True


def _model_dir_candidates() -> List[Path]:
    candidates = []
    env_dir = os.environ.get("RAG_ONNX_MODEL_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(Path(BAKED_MODEL_DIR))
    cache_root = os.environ.get(
        "JOBPULSE_CACHE_DIR", str(Path.home() / ".cache" / "jobpulse")
    )
    candidates.append(Path(cache_root) / "onnx-models" / HF_MODEL_NAME)
    return candidates


def _is_complete(path: Path) -> bool:
    return (path / ONNX_FILE).exists() and (path / "tokenizer.json").exists()


def resolve_model_dir(download: bool = True) -> Path:
    """Locate a usable ONNX model directory, downloading it if allowed."""
    for cand in _model_dir_candidates():
        if _is_complete(cand):
            return cand

    if not download:
        raise FileNotFoundError(
            "No local ONNX model found. Set RAG_ONNX_MODEL_DIR or run "
            "prefetch_model()."
        )
    dest = _model_dir_candidates()[-1]
    return prefetch_model(dest)


def prefetch_model(dest: Path | str, repo_id: str = DEFAULT_ONNX_REPO) -> Path:
    """Download the tokenizer + ONNX graph into ``dest`` (idempotent)."""
    from huggingface_hub import hf_hub_download

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for filename in TOKENIZER_FILES:
        try:
            hf_hub_download(repo_id, filename, local_dir=str(dest))
        except Exception as e:
            # vocab.txt / special_tokens_map.json are optional depending on
            # tokenizer layout — tokenizer.json is the one that matters.
            logger.debug("skip %s: %s", filename, e)

    target = dest / ONNX_FILE
    if not target.exists():
        import shutil

        tmp = hf_hub_download(repo_id, ONNX_FILE, local_dir=str(dest / "_dl"))
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, target)
        shutil.rmtree(dest / "_dl", ignore_errors=True)

    if not _is_complete(dest):
        raise RuntimeError(f"ONNX model download incomplete at {dest}")
    logger.info("ONNX model ready at %s", dest)
    return dest


class MiniLMOnnxEncoder:
    """Encodes text with the ONNX export of all-MiniLM-L6-v2.

    Output contract matches SentenceTransformer(..., normalize_embeddings=True):
    float32, L2-normalized, shape (n, 384).
    """

    def __init__(self, model_name: str = HF_MODEL_NAME, model_dir: Optional[Path] = None):
        import onnxruntime as ort
        from transformers import AutoTokenizer

        if not onnx_available():
            raise ImportError("onnxruntime/transformers not installed")

        self.model_name = model_name
        self.model_dir = Path(model_dir) if model_dir else resolve_model_dir()
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        self.session = ort.InferenceSession(
            str(self.model_dir / ONNX_FILE),
            providers=["CPUExecutionProvider"],
        )
        self._input_names = [i.name for i in self.session.get_inputs()]
        self._output_name = self._pick_output()
        logger.info("ONNX encoder ready: %s (%s)", self.model_name, self.model_dir)

    def _pick_output(self) -> str:
        for out in self.session.get_outputs():
            shape = out.shape
            if len(shape) == 3:  # (batch, seq, hidden) = last_hidden_state
                return out.name
        return self.session.get_outputs()[0].name

    def encode(self, texts: List[str]) -> np.ndarray:
        enc = self.tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )
        feed = {}
        for name in self._input_names:
            if name == "input_ids":
                feed[name] = enc["input_ids"]
            elif name == "attention_mask":
                feed[name] = enc["attention_mask"]
            elif name == "token_type_ids":
                feed[name] = np.zeros_like(enc["input_ids"])
            else:
                raise KeyError(f"Unexpected ONNX model input: {name}")

        hidden = self.session.run([self._output_name], feed)[0]  # (b, seq, h)
        mask = enc["attention_mask"].astype(np.float32)[..., None]
        summed = (hidden * mask).sum(axis=1)
        counts = np.clip(mask.sum(axis=1), 1e-9, None)
        pooled = summed / counts
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        pooled = pooled / np.clip(norms, 1e-9, None)
        return pooled.astype(np.float32)


if __name__ == "__main__":
    enc = MiniLMOnnxEncoder()
    out = enc.encode(["remote python developer in Kenya", "data analyst"])
    print("shape:", out.shape, "norms:", np.linalg.norm(out, axis=1))
