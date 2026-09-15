"""Thin wrapper around Ollama for local LLM generation in the RAG pipeline.

Falls back gracefully when Ollama is not running — callers always get a
usable response (either LLM-generated or a structured template answer).

Usage:
    from src.rag.llm import OllamaLLM

    llm = OllamaLLM()                          # defaults to qwen2.5:0.5b
    answer = llm.generate(prompt="...", context="...")
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Generator, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5:0.5b"
DEFAULT_BASE_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 2
RETRY_DELAYS = [1.0, 2.0]


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_HOST", DEFAULT_BASE_URL))
    timeout: int = REQUEST_TIMEOUT
    temperature: float = 0.3
    top_p: float = 0.85
    num_ctx: int = 512
    repeat_penalty: float = 1.1
    num_predict: int = 80
    num_thread: int = field(default_factory=lambda: min(8, os.cpu_count() or 4))


class OllamaLLM:
    """Generate natural-language answers via a local Ollama model.

    The instance probes connectivity once on first use and caches the
    result so subsequent calls are fast. If Ollama is unreachable the
    ``available`` property returns False and ``generate`` returns None,
    letting callers fall back to template-based answers.
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client = None
        self._available: bool | None = None

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

    def _reset_available(self):
        """Reset availability so next call re-probes instead of permanently giving up."""
        self._available = None

    # ------------------------------------------------------------------
    # Internal: build messages + options
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        history: list[dict[str, str]] | None = None,
        max_context_chars: int = 800,
    ) -> list[dict[str, str]]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history[-4:])
        if context and len(context) > max_context_chars:
            context = context[:max_context_chars]
        if context:
            full_prompt = f"Here are relevant job listings:\n\n{context}\n\n---\n\n{prompt}"
        else:
            full_prompt = f"No job listings were found for this query.\n\n---\n\n{prompt}"
        messages.append({"role": "user", "content": full_prompt})
        return messages

    def _build_options(self) -> dict:
        return {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "num_ctx": self.config.num_ctx,
            "repeat_penalty": self.config.repeat_penalty,
            "num_predict": self.config.num_predict,
            "num_thread": self.config.num_thread,
        }

    # ------------------------------------------------------------------
    # Generation (blocking)
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        history: list[dict[str, str]] | None = None,
        max_context_chars: int = 800,
    ) -> str | None:
        """Generate a complete answer from the LLM.

        Returns the generated text, or None if the LLM is unavailable or
        an error occurs after retries. Callers should fall back to
        template answers on None.
        """
        self._ensure_client()
        if self._client is None or not self.available:
            return None

        messages = self._build_messages(prompt, context, system, history, max_context_chars)
        options = self._build_options()

        for attempt in range(1 + MAX_RETRIES):
            try:
                response_stream = self._client.chat(
                    model=self.config.model,
                    messages=messages,
                    options=options,
                    stream=True,
                )
                response_text = []
                for chunk in response_stream:
                    if "message" in chunk and "content" in chunk["message"]:
                        response_text.append(chunk["message"]["content"])
                return "".join(response_text).strip()
            except Exception as exc:
                logger.warning(
                    "Ollama generation failed (attempt %d/%d): %s",
                    attempt + 1, 1 + MAX_RETRIES, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                # All retries exhausted — temporarily mark unavailable but
                # allow re-probe on next call instead of permanent lockout.
                self._reset_available()
                return None

    # ------------------------------------------------------------------
    # Generation (streaming) — yields token chunks
    # ------------------------------------------------------------------

    def generate_stream(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        history: list[dict[str, str]] | None = None,
        max_context_chars: int = 800,
    ) -> Generator[str, None, None]:
        """Yield token chunks from the LLM as they arrive.

        Falls back silently if the LLM is unavailable — yields nothing.
        """
        self._ensure_client()
        if self._client is None or not self.available:
            return

        messages = self._build_messages(prompt, context, system, history, max_context_chars)
        options = self._build_options()

        for attempt in range(1 + MAX_RETRIES):
            try:
                response_stream = self._client.chat(
                    model=self.config.model,
                    messages=messages,
                    options=options,
                    stream=True,
                )
                for chunk in response_stream:
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
                return  # Success — exit generator
            except Exception as exc:
                logger.warning(
                    "Ollama streaming failed (attempt %d/%d): %s",
                    attempt + 1, 1 + MAX_RETRIES, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                self._reset_available()
                return

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
# System prompt for JobPulse — conversational style
# ---------------------------------------------------------------------------

JOBPULSE_SYSTEM_PROMPT = """\
You are JobPulse, a career assistant for the African tech job market. \
You will receive relevant job listings as context. \
Answer the user's question using ONLY the provided job listings. \
If the listings don't contain enough information to answer, say so honestly — do not make up information. \
Be warm, concise (2-4 sentences), and conversational. Use contractions. \
Always reference specific jobs from the listings when possible. \
End with a natural follow-up question."""


def build_rag_prompt(question: str, question_type: str = "general") -> str:
    """Build the user prompt for the LLM — includes explicit context instructions."""
    return f"""Based on the job listings provided above, answer this question: {question}

If the listings don't match the question, say you couldn't find relevant results rather than making up an answer."""


# ---------------------------------------------------------------------------
# Quick greeting responses (no LLM needed)
# ---------------------------------------------------------------------------

_GREETINGS = {
    "hello": "Hey there! I'm JobPulse, your go-to assistant for tech careers across Africa. What are you curious about?",
    "hi": "Hi! I can help you explore tech jobs, skills, and career paths across Africa. What would you like to know?",
    "hey": "Hey! Looking for tech job insights in Africa? I've got you covered. What's on your mind?",
    "good morning": "Good morning! Ready to explore some career opportunities? What are you looking for?",
    "good afternoon": "Good afternoon! What can I help you with today?",
    "good evening": "Good evening! Got questions about the African tech job market? I'm here to help.",
    "help": "I can help you with:\n- **Job searches** — find roles by skill, location, or company\n- **Skill demand** — see what's hot in the market\n- **Career advice** — plan your next move\n- **Market trends** — stay ahead of the curve\n\nJust ask me anything!",
    "who are you": "I'm JobPulse — your AI career assistant for the African tech market. I know about 9,500+ job postings across Nigeria, Kenya, South Africa, and beyond. Ask me anything!",
    "what can you do": "I can search jobs, tell you which skills are in demand, give career advice, and share market insights for African tech. What interests you?",
}


def detect_greeting(text: str) -> Optional[str]:
    """Return a quick conversational response for greetings, or None."""
    lowered = text.lower().strip().rstrip("!?.,;:")
    if lowered in _GREETINGS:
        return _GREETINGS[lowered]
    if any(lowered.startswith(g) for g in ("hello", "hi ", "hey")):
        return _GREETINGS["hello"]
    return None
