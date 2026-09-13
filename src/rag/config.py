"""Configuration for RAG system optimizations."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RAGOptimizationConfig:
    """Configuration for RAG performance optimizations."""
    
    # Model optimization
    model: str = "qwen2.5:0.5b"  # Fast model for quick responses
    temperature: float = 0.3
    top_p: float = 0.85
    num_ctx: int = 512
    repeat_penalty: float = 1.1
    num_predict: int = 80
    
    # Timeout settings
    request_timeout: int = 15
    
    # Cache settings
    cache_max_size: int = 500
    cache_ttl_seconds: int = 1800
    
    # Retrieval optimization
    min_score_threshold: float = 0.1
    max_context_chars: int = 400
    default_top_k: int = 3
    
    # Embedding optimization
    tfidf_max_features: int = 3000
    tfidf_ngram_range: tuple = (1, 1)
    tfidf_min_df: int = 2
    tfidf_max_df: float = 0.95
    
    # Response optimization
    enable_streaming: bool = True
    enable_caching: bool = True


# Global configuration instance
_global_config: Optional[RAGOptimizationConfig] = None


def get_optimization_config() -> RAGOptimizationConfig:
    """Get optimization configuration from environment variables with defaults.
    
    Environment variables:
        RAG_MODEL           — Ollama model name (default: qwen2.5:0.5b)
        RAG_TEMPERATURE     — Sampling temperature (default: 0.4)
        RAG_TOP_P           — Top-p nucleus sampling (default: 0.85)
        RAG_NUM_CTX         — Context window size (default: 1024)
        RAG_REPEAT_PENALTY  — Repetition penalty (default: 1.1)
        RAG_NUM_PREDICT     — Max tokens to generate (default: 180)
        RAG_MAX_CONTEXT_CHARS — Max context chars passed to LLM (default: 800)
        RAG_CACHE_MAX_SIZE  — LRU cache entries (default: 500)
        RAG_CACHE_TTL       — Cache TTL in seconds (default: 1800)
    """
    global _global_config
    
    if _global_config is not None:
        return _global_config
    
    config = RAGOptimizationConfig()
    
    # Override from environment variables if set
    if os.getenv("RAG_MODEL"):
        config.model = os.getenv("RAG_MODEL")
    if os.getenv("RAG_TEMPERATURE"):
        config.temperature = float(os.getenv("RAG_TEMPERATURE"))
    if os.getenv("RAG_TOP_P"):
        config.top_p = float(os.getenv("RAG_TOP_P"))
    if os.getenv("RAG_NUM_CTX"):
        config.num_ctx = int(os.getenv("RAG_NUM_CTX"))
    if os.getenv("RAG_REPEAT_PENALTY"):
        config.repeat_penalty = float(os.getenv("RAG_REPEAT_PENALTY"))
    if os.getenv("RAG_NUM_PREDICT"):
        config.num_predict = int(os.getenv("RAG_NUM_PREDICT"))
    if os.getenv("RAG_MAX_CONTEXT_CHARS"):
        config.max_context_chars = int(os.getenv("RAG_MAX_CONTEXT_CHARS"))
    if os.getenv("RAG_CACHE_MAX_SIZE"):
        config.cache_max_size = int(os.getenv("RAG_CACHE_MAX_SIZE"))
    if os.getenv("RAG_CACHE_TTL"):
        config.cache_ttl_seconds = int(os.getenv("RAG_CACHE_TTL"))
    
    _global_config = config
    return config


def apply_optimization_config(config: RAGOptimizationConfig = None):
    """Apply optimization configuration to the RAG system."""
    global _global_config
    
    if config is None:
        config = get_optimization_config()
    
    _global_config = config
    
    # Update cache config
    from .cache import query_cache
    query_cache.max_size = config.cache_max_size
    query_cache.ttl_seconds = config.cache_ttl_seconds
    
    # Update embedding config
    from .embeddings import TfidfEmbedder
    TfidfEmbedder.max_features = config.tfidf_max_features
    
    return config


def create_llm_config() -> 'LLMConfig':
    """Create an LLMConfig using the current optimization settings."""
    from .llm import LLMConfig
    
    config = get_optimization_config()
    return LLMConfig(
        model=config.model,
        timeout=config.request_timeout,
        temperature=config.temperature,
        top_p=config.top_p,
        num_ctx=config.num_ctx,
        repeat_penalty=config.repeat_penalty,
        num_predict=config.num_predict,
    )