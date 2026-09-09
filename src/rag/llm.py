"""Thin wrapper around Ollama for local LLM generation in the RAG pipeline.

Falls back gracefully when Ollama is not running — callers always get a
usable response (either LLM-generated or a structured template answer).

Usage:
    from src.rag.llm import OllamaLLM

    llm = OllamaLLM()                          # defaults to qwen2.5:1.5b
    answer = llm.generate(prompt="...", context="...")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5:1.5b"
DEFAULT_BASE_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 60  # seconds


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_HOST", DEFAULT_BASE_URL))
    timeout: int = REQUEST_TIMEOUT
    temperature: float = 0.3
    top_p: float = 0.9
    num_ctx: int = 4096


class OllamaLLM:
    """Generate natural-language answers via a local Ollama model.

    The instance probes connectivity once on first use and caches the
    result so subsequent calls are fast. If Ollama is unreachable the
    ``available`` property returns False and ``generate`` returns None,
    letting callers fall back to template-based answers.
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client = None  # lazy ollama.Client
        self._available: bool | None = None  # None = not probed yet

    # ------------------------------------------------------------------
    # Connectivity
    # ------------------------------------------------------------------

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
            logger.warning("ollama package not installed — LLM generation disabled")
            self._available = False

    def probe(self) -> bool:
        """Check whether Ollama is reachable and the model is available."""
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

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
    ) -> str | None:
        """Generate an answer from the LLM.

        Returns the generated text, or None if the LLM is unavailable or
        an error occurs. Callers should fall back to template answers on
        None.
        """
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
                model=self.config.model,
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

    def pull_model(self) -> bool:
        """Pull the configured model if not already present. Returns True on success."""
        self._ensure_client()
        if self._client is None:
            return False
        try:
            logger.info("Pulling model %s (this may take a while)...", self.config.model)
            self._client.pull(self.config.model)
            logger.info("Model %s ready", self.config.model)
            return True
        except Exception as exc:
            logger.error("Failed to pull model %s: %s", self.config.model, exc)
            return False


# ---------------------------------------------------------------------------
# System prompt for JobPulse
# ---------------------------------------------------------------------------

JOBPULSE_SYSTEM_PROMPT = """\
You are JobPulse Assistant, an AI helper for the African tech job market.

Your role is to answer questions about tech jobs, skills, careers, and market \
trends across Africa using ONLY the provided context (retrieved job postings \
and market data).

Rules:
1. Base your answer ONLY on the provided context. Do not invent facts.
2. If the context does not contain enough information, say so honestly.
3. When listing skills or roles, cite the specific job postings where you \
   found them.
4. Be concise but thorough. Aim for 2-4 paragraphs.
5. Use markdown formatting: bold for emphasis, bullet points for lists.
6. If the user asks about salary, note that salary data may be limited in \
   the dataset.
7. Always end with a practical recommendation or next step.
"""


def build_rag_prompt(question: str, question_type: str = "general") -> str:
    """Build the user prompt for the LLM, incorporating question type hints."""
    type_hints = {
        "skill_inquiry": "Focus on skill demand, frequency across jobs, and learning recommendations.",
        "job_search": "List the most relevant job postings with company, location, and key skills.",
        "career_advice": "Provide career progression advice based on the retrieved roles and seniority levels.",
        "market_intelligence": "Summarize market trends, top skills, and hiring patterns from the data.",
        "salary_compensation": "Note any salary or compensation data found in the context.",
        "company_industry": "Focus on which companies are hiring and what roles they offer.",
        "location_geography": "Focus on geographic distribution of jobs and location-specific insights.",
        "general": "Provide a comprehensive answer covering all relevant aspects.",
    }
    hint = type_hints.get(question_type, type_hints["general"])

    return (
        f"Question type: {question_type}\n"
        f"Guidance: {hint}\n\n"
        f"User question: {question}\n\n"
        f"Using the context above, provide a grounded, helpful answer."
    )
