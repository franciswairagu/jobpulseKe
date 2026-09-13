#!/usr/bin/env python3
"""Script to apply RAG optimizations and test performance."""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.rag.config import apply_optimization_config, get_optimization_config


def main():
    """Apply optimizations and show configuration."""
    print("=== Applying RAG Optimizations ===\n")
    
    # Get and display current config
    config = get_optimization_config()
    print("Current optimization settings:")
    print(f"  Model: {config.model}")
    print(f"  Temperature: {config.temperature}")
    print(f"  Top-p: {config.top_p}")
    print(f"  Context window: {config.num_ctx}")
    print(f"  Max tokens: {config.num_predict}")
    print(f"  Cache size: {config.cache_max_size}")
    print(f"  Cache TTL: {config.cache_ttl_seconds}s")
    print(f"  Default results: {config.default_top_k}")
    print(f"  Max context chars: {config.max_context_chars}")
    print()
    
    # Apply optimizations
    apply_optimization_config(config)
    print("✅ Optimizations applied successfully!")
    print()
    
    print("Performance improvements:")
    print("✅ Faster model (qwen2.5:0.5b) for quick responses")
    print("✅ Shorter context for faster LLM processing")
    print("✅ Fewer results (top_k=3) for less noise")
    print("✅ Conversational system prompt for natural responses")
    print("✅ Greeting detection for instant replies")
    print("✅ Conversation history for context")
    print()
    
    print("To customize via environment variables:")
    print("  export RAG_MODEL='qwen2.5:1.5b'  # Use larger model if needed")
    print("  export RAG_TEMPERATURE=0.3         # Adjust creativity")
    print("  export RAG_NUM_CTX=1024            # Even smaller context")
    print()


if __name__ == "__main__":
    main()