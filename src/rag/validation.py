"""
Input validation for the RAG system's query interface.

Without this, JobVectorStore.search() will happily "succeed" on garbage
input in ways that are worse than an error: an empty string embeds to a
near-zero vector and returns some arbitrary top_k with tiny/meaningless
scores; a 50,000-character query pays real embedding cost for no benefit;
a non-string (None, a list, a number) reaches sklearn/sentence-transformers
internals and crashes with a confusing stack trace instead of a clear
message pointing at the actual problem.

validate_query() is the single choke point every entry into the RAG
system (JobPulseRAG.query(), the CLI) should call before touching the
vector store.
"""
import re
from typing import Tuple

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 500
MIN_TOP_K = 1
MAX_TOP_K = 50
DEFAULT_TOP_K = 5

# A query must contain at least one alphanumeric character somewhere —
# rejects pure punctuation/whitespace/emoji input ("???", "...", "🎉🎉")
# that would otherwise embed to noise and still return "results".
_HAS_ALPHANUMERIC = re.compile(r"[a-zA-Z0-9]")


class QueryValidationError(ValueError):
    """Raised when a query or top_k value can't be used to search —
    always carries a message safe to show directly to an end user."""


def validate_query(text, top_k=DEFAULT_TOP_K) -> Tuple[str, int]:
    """Validate and normalize a (query, top_k) pair.

    Returns (cleaned_text, clamped_top_k) on success. Raises
    QueryValidationError with a specific, user-facing message on failure.

    Deliberately different failure modes for different problems:
      - wrong type / empty / too short / no real content -> hard error,
        there's nothing sensible to search for
      - too long -> truncated with the string returned, not an error,
        since the intent is usually clear and truncating is friendlier
      - top_k wrong type or out of range -> clamped/defaulted, not an
        error, since it's a secondary parameter, not the user's actual
        question
    """
    # --- type check ---
    if not isinstance(text, str):
        raise QueryValidationError(
            f"Query must be text, got {type(text).__name__}. "
            f"Pass a search string, e.g. \"python developer in Kenya\"."
        )

    cleaned = text.strip()

    # --- emptiness / whitespace-only ---
    if not cleaned:
        raise QueryValidationError(
            "Query is empty. Try something like \"remote data analyst\" "
            "or \"senior backend engineer in Nigeria\"."
        )

    # --- too short to mean anything ---
    if len(cleaned) < MIN_QUERY_LENGTH:
        raise QueryValidationError(
            f"Query \"{cleaned}\" is too short to search meaningfully "
            f"(minimum {MIN_QUERY_LENGTH} characters). Try adding a role, "
            f"skill, or location."
        )

    # --- must contain real content, not just punctuation/symbols/emoji ---
    if not _HAS_ALPHANUMERIC.search(cleaned):
        raise QueryValidationError(
            f"Query \"{cleaned}\" doesn't contain any searchable text "
            f"(letters or numbers). Try describing a role, skill, or location."
        )

    # --- too long: truncate rather than reject, log-worthy not fatal ---
    if len(cleaned) > MAX_QUERY_LENGTH:
        cleaned = cleaned[:MAX_QUERY_LENGTH].rstrip()

    # --- top_k: coerce, clamp, never crash on a bad secondary param ---
    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = DEFAULT_TOP_K
    top_k = max(MIN_TOP_K, min(MAX_TOP_K, top_k))

    return cleaned, top_k
