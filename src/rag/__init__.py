"""JobPulse RAG System.

Provides retrieval-augmented generation over African tech job postings.
"""
from src.rag.retriever import JobPulseRAG
from src.rag.vector_store import JobVectorStore
from src.rag.llm import OllamaLLM, LLMConfig
from src.rag.assistant import JobPulseAssistant, AssistantAnswer
from src.rag.chunker import chunk_job_records, chunk_rag_document
from src.rag.prompts import (
    SYSTEM_PROMPT,
    build_rag_prompt,
    format_retrieved_context,
)

__all__ = [
    "JobPulseRAG",
    "JobVectorStore",
    "OllamaLLM",
    "LLMConfig",
    "JobPulseAssistant",
    "AssistantAnswer",
    "chunk_job_records",
    "chunk_rag_document",
    "SYSTEM_PROMPT",
    "build_rag_prompt",
    "format_retrieved_context",
]
