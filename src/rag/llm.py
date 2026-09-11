"""Ollama wrapper for local LLM generation.

Supports both base and fine-tuned models via Ollama.
Falls back gracefully when Ollama is not running.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5:1.5b"
DEFAULT_BASE_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 60


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    base_url: str = field(
        default_factory=lambda: os.environ.get("OLLAMA_HOST", DEFAULT_BASE_URL)
    )
    timeout: int = REQUEST_TIMEOUT
    temperature: float = 0.3
    top_p: float = 0.9
    num_ctx: int = 4096


class OllamaLLM:
    """Generate natural-language answers via a local Ollama model."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client = None
        self._available: bool | None = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            import ollama as _ollama
            self._client = _ollama.Client(
                host=self.config.base_url,
                timeout=self.config.timeout,
            )
        except ImportError:
            logger.warning("ollama package not installed")
            self._available = False

    def probe(self) -> bool:
        """Check if Ollama is reachable."""
        self._ensure_client()
        if self._client is None:
            return False
        try:
            self._client.list()
            self._available = True
            return True
        except Exception as exc:
            logger.info("Ollama not reachable: %s", exc)
            self._available = False
            return False

    @property
    def available(self) -> bool:
        if self._available is None:
            return self.probe()
        return self._available

    def list_models(self) -> list[str]:
        """List available Ollama models."""
        self._ensure_client()
        if self._client is None:
            return []
        try:
            response = self._client.list()
            return [m["name"] for m in response.get("models", [])]
        except Exception:
            return []

    def has_model(self, model_name: str | None = None) -> bool:
        """Check if a specific model is available."""
        model_name = model_name or self.config.model
        models = self.list_models()
        return any(model_name in m for m in models)

    def generate(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        model: str | None = None,
    ) -> str | None:
        """Generate an answer from the LLM."""
        self._ensure_client()
        if self._client is None or not self.available:
            return None

        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\n{prompt}"
        messages.append({"role": "user", "content": full_prompt})

        try:
            response = self._client.chat(
                model=model or self.config.model,
                messages=messages,
                options={
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                    "num_ctx": self.config.num_ctx,
                },
                stream=False,
            )
            return response["message"]["content"].strip()
        except Exception as exc:
            logger.warning("Ollama generation failed: %s", exc)
            self._available = False
            return None

    def pull_model(self, model_name: str | None = None) -> bool:
        """Pull a model if not already present."""
        self._ensure_client()
        if self._client is None:
            return False
        model_name = model_name or self.config.model
        try:
            logger.info("Pulling model %s...", model_name)
            self._client.pull(model_name)
            logger.info("Model %s ready", model_name)
            return True
        except Exception as exc:
            logger.error("Failed to pull model %s: %s", model_name, exc)
            return False
