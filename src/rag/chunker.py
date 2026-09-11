"""Semantic chunking for RAG documents.

Splits job postings into overlapping chunks optimized for embedding
and retrieval. Preserves structured fields as metadata.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 128
MIN_CHUNK_SIZE = 100


def count_tokens(text: str, tokenizer_name: str = "cl100k_base") -> int:
    """Count tokens using tiktoken."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding(tokenizer_name)
        return len(enc.encode(text))
    except ImportError:
        # Fallback: approximate token count
        return len(text) // 4


def split_text(
    text: str,
    max_tokens: int = DEFAULT_CHUNK_SIZE,
    overlap_tokens: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks by token count."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)

        if len(tokens) <= max_tokens:
            return [text]

        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = enc.decode(chunk_tokens)
            if len(chunk_text.strip()) >= MIN_CHUNK_SIZE // 4:
                chunks.append(chunk_text)
            if end >= len(tokens):
                break
            start = end - overlap_tokens
        return chunks
    except ImportError:
        # Fallback: split by characters
        return _split_by_chars(text, max_tokens * 4, overlap_tokens * 4)


def _split_by_chars(
    text: str,
    max_chars: int,
    overlap_chars: int,
) -> list[str]:
    """Fallback text splitting by character count."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind(".")
            if last_period > max_chars // 2:
                end = start + last_period + 1
                chunk = text[start:end]

        if len(chunk.strip()) >= MIN_CHUNK_SIZE:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap_chars
    return chunks


def chunk_rag_document(
    rag_document: str,
    metadata: dict[str, Any] | None = None,
    max_tokens: int = DEFAULT_CHUNK_SIZE,
    overlap_tokens: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Chunk a rag_document with metadata preservation.

    Returns list of dicts with keys: text, chunk_index, total_chunks, metadata.
    """
    metadata = metadata or {}
    chunks = split_text(rag_document, max_tokens, overlap_tokens)

    result = []
    for i, chunk_text in enumerate(chunks):
        result.append({
            "text": chunk_text,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "metadata": {
                **metadata,
                "chunk_id": f"{metadata.get('job_id', 'unknown')}_{i}",
            },
        })
    return result


def chunk_job_records(
    records: list[dict[str, Any]],
    text_field: str = "rag_document",
    max_tokens: int = DEFAULT_CHUNK_SIZE,
    overlap_tokens: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Chunk multiple job records into document chunks."""
    all_chunks = []
    for record in records:
        rag_doc = record.get(text_field, "")
        if not rag_doc:
            continue

        metadata = {
            "job_id": record.get("job_id", ""),
            "job_title": record.get("job_title", ""),
            "company": record.get("company", ""),
            "location": record.get("location", ""),
            "country": record.get("country", ""),
            "work_mode": record.get("work_mode", ""),
            "seniority_level": record.get("seniority_level", ""),
            "skills": record.get("skills", []),
            "vacancy_url": record.get("vacancy_url", ""),
        }

        chunks = chunk_rag_document(
            rag_doc,
            metadata=metadata,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )
        all_chunks.extend(chunks)

    logger.info(
        "Chunked %d records into %d chunks",
        len(records), len(all_chunks),
    )
    return all_chunks
