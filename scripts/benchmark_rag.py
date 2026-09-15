#!/usr/bin/env python3
"""Benchmark script to test RAG system performance improvements."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.rag.assistant import JobPulseAssistant
from src.rag.cache import query_cache


def benchmark_rag():
    """Run performance benchmarks on the RAG system."""
    print("=== RAG Performance Benchmark ===\n")
    
    # Initialize assistant
    print("1. Initializing RAG assistant...")
    start = time.time()
    try:
        assistant = JobPulseAssistant()
        assistant.rag.ensure_ready()
        print(f"   ✅ Assistant ready in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you have the required packages: pip install -r requirements.txt")
        print("2. For sentence-transformers, install: pip install sentence-transformers")
        print("3. For TF-IDF only, ensure scikit-learn is installed: pip install scikit-learn")
        return
    
    # Test queries
    test_queries = [
        "What are the most in-demand skills in Kenya?",
        "Find remote Python developer jobs",
        "How do I become a data scientist?",
        "What companies are hiring in Nigeria?",
        "What skills do I need for machine learning?",
    ]
    
    print("\n2. Running performance tests...")
    times = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        
        # Clear cache for fresh test
        query_cache.clear()
        
        start = time.time()
        try:
            result = assistant.ask(query, top_k=5)
            elapsed = time.time() - start
            times.append(elapsed)
            
            print(f"   ✅ Response in {elapsed:.2f}s")
            print(f"   Method: {'LLM' if 'LLM' in str(result.confidence) else 'Template'}")
            print(f"   Confidence: {result.confidence}")
            print(f"   Sources: {len(result.sources)}")
            print(f"   Answer length: {len(result.answer)} chars")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test caching
    print("\n3. Testing cache performance...")
    query_cache.clear()
    
    # First call (cold cache)
    test_query = "What are the top skills in South Africa?"
    start = time.time()
    result1 = assistant.ask(test_query, top_k=5)
    cold_time = time.time() - start
    
    # Second call (warm cache)
    start = time.time()
    result2 = assistant.ask(test_query, top_k=5)
    warm_time = time.time() - start
    
    print(f"   Cold cache: {cold_time:.2f}s")
    print(f"   Warm cache: {warm_time:.2f}s")
    if warm_time > 0:
        print(f"   Speedup: {cold_time / warm_time:.1f}x")
    
    # Summary
    print("\n=== Summary ===")
    if times:
        avg_time = sum(times) / len(times)
        print(f"Average response time: {avg_time:.2f}s")
        print(f"Fastest: {min(times):.2f}s")
        print(f"Slowest: {max(times):.2f}s")
        print(f"Cache size: {query_cache.size()} entries")
    
    print("\nOptimization recommendations:")
    print("1. Ensure Ollama is running with: OLLAMA_HOST=0.0.0.0 ollama serve")
    print("2. Pull the model: ollama pull qwen2.5:1.5b")
    print("3. For even faster responses, consider using a smaller model like qwen2.5:0.5b")
    print("4. Monitor cache hit rate in production logs")
    print("5. Use environment variables to customize: RAG_MODEL, RAG_TEMPERATURE, etc.")


if __name__ == "__main__":
    benchmark_rag()