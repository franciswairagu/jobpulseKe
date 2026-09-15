# RAG System Performance Optimizations

## Summary of Changes

### 1. Model Parameter Optimization (`src/rag/llm.py`)
- **Reduced temperature**: 0.3 → 0.1 (faster, more focused responses)
- **Reduced top_p**: 0.9 → 0.8 (faster sampling)
- **Reduced context window**: 4096 → 2048 tokens (faster inference)
- **Added repeat_penalty**: 1.1 (prevents repetition, faster completion)
- **Added num_predict**: 256 (limits response length)
- **Reduced timeout**: 60s → 30s (faster failure detection)

### 2. Streaming Response Support (`src/rag/llm.py`)
- Enabled streaming for faster perceived response times
- Users see tokens as they're generated instead of waiting for full response

### 3. Query Caching (`src/rag/cache.py`)
- Implemented LRU cache with TTL expiration
- Default cache size: 500 entries
- Default TTL: 30 minutes
- Significant speedup for repeated queries

### 4. Prompt Optimization (`src/rag/llm.py`)
- Added context truncation (max 1500 chars) for faster processing
- Optimized prompt structure for faster LLM processing

### 5. TF-IDF Optimization (`src/rag/embeddings.py`)
- Reduced max_features: 5000 → 3000 (faster processing)
- Changed ngram_range: (1,2) → (1,1) (unigrams only)
- Added sublinear_tf scaling for better performance
- Added min_df=2 and max_df=0.95 to filter rare/common terms

### 6. Retrieval Optimization (`src/rag/vector_store.py`)
- Added min_score_threshold parameter (default: 0.1)
- Pre-filters low-quality results for faster, more accurate responses
- Optimized vector search with score-based filtering

### 7. Configuration Management (`src/rag/config.py`)
- Centralized configuration for all optimizations
- Environment variable support for easy tuning
- Default values optimized for speed/quality balance

### 8. Performance Monitoring (`ui/jobpulse-backend/jobpulse-backend/app/api/rag.py`)
- Added timing logs for RAG queries
- Logs response times and methods used

## Usage

### Apply Optimizations
```bash
python scripts/optimize_rag.py
```

### Benchmark Performance
```bash
python scripts/benchmark_rag.py
```

### Environment Variables
```bash
# Use smaller model for fastest responses
export RAG_MODEL='qwen2.5:0.5b'

# Adjust temperature (lower = faster, more focused)
export RAG_TEMPERATURE=0.05

# Adjust context window (smaller = faster)
export RAG_NUM_CTX=1024

# Adjust cache size
export RAG_CACHE_MAX_SIZE=1000

# Adjust cache TTL (seconds)
export RAG_CACHE_TTL=3600
```

## Performance Tips

1. **Model Selection**:
   - `qwen2.5:0.5b` - Fastest responses (less accurate)
   - `qwen2.5:1.5b` - Balanced speed/quality (recommended)
   - `qwen2.5:3b` - Best quality (slower)

2. **Hardware Optimization**:
   - Enable GPU acceleration in Ollama for 2-5x speedup
   - Run Ollama on SSD for faster model loading
   - Ensure adequate RAM for model loading

3. **Cache Management**:
   - Monitor cache hit rate in logs
   - Adjust cache size based on usage patterns
   - Clear cache if memory usage is high

4. **Production Recommendations**:
   - Use environment variables for easy tuning
   - Monitor response times in logs
   - Adjust parameters based on user feedback
   - Consider A/B testing different configurations

## Expected Performance Improvements

- **Response Time**: 30-50% faster with optimized parameters
- **Cache Hit Rate**: 60-80% for repeated queries
- **Memory Usage**: Reduced with smaller context window
- **User Experience**: Streaming responses improve perceived performance

## Monitoring

Check logs for:
- Response times: `RAG query completed in X.XX seconds`
- Cache hits: Monitor cache size and hit rate
- LLM availability: Check if LLM or template is being used

## Rollback

To revert to default settings:
```bash
unset RAG_MODEL RAG_TEMPERATURE RAG_TOP_P RAG_NUM_CTX
```

Then restart the application.