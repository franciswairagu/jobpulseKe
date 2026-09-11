# RAG Rebuild Plan: Fine-Tuned qwen2.5:1.5b + ChromaDB

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FINE-TUNING PIPELINE                      │
│  Job Data → Auto Q&A Gen → Manual Q&A → Fine-tune qwen2.5  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE (REBUILT)                    │
│                                                              │
│  1. Chunking/Tokenization                                    │
│  2. Embedding Generation (all-MiniLM-L6-v2)                 │
│  3. Vector Storage (ChromaDB)                                │
│  4. Query Encoding                                           │
│  5. Semantic Retrieval                                       │
│  6. Prompt Augmentation                                      │
│  7. LLM Generation (fine-tuned qwen2.5:1.5b via Ollama)    │
└─────────────────────────────────────────────────────────────┘
```

## New Files to Create

| File | Purpose |
|------|---------|
| `src/rag/chunker.py` | Semantic chunking/tokenization |
| `src/rag/prompts.py` | Centralized prompt templates |
| `src/rag/fine_tune/__init__.py` | Fine-tuning module init |
| `src/rag/fine_tune/data_generator.py` | Auto-generate Q&A pairs from job data |
| `src/rag/fine_tune/training_data.py` | Manual Q&A pair management |
| `src/rag/fine_tune/trainer.py` | Fine-tuning orchestration (QLoRA) |
| `src/rag/fine_tune/export_model.py` | Export fine-tuned model to Ollama |
| `scripts/fine_tune_model.py` | CLI entry point for fine-tuning |

## Files to Rewrite

| File | Changes |
|------|---------|
| `src/rag/__init__.py` | Updated exports |
| `src/rag/embeddings.py` | Cleaner interface, remove TF-IDF fallback |
| `src/rag/vector_store.py` | ChromaDB backend (replaces numpy) |
| `src/rag/retriever.py` | ChromaDB-backed retrieval |
| `src/rag/llm.py` | Fine-tuned model support |
| `src/rag/assistant.py` | Cleaner orchestration |
| `src/rag/validation.py` | Minor cleanup |
| `scripts/build_rag_index.py` | New index builder for ChromaDB |
| `requirements.txt` | Add fine-tuning dependencies |

## Implementation Phases

### Phase 1: Fine-Tuning (~30 min)
1. Create `src/rag/fine_tune/data_generator.py`
   - Parse rag_document fields (title, company, skills, location, seniority)
   - Generate Q&A pairs using templates
   - Target: 5000-10000 auto-generated pairs

2. Create `src/rag/fine_tune/training_data.py`
   - JSON-based storage for manual Q&A pairs
   - Categories: market_intelligence, skill_inquiry, job_search, career_advice
   - Load/merge with auto-generated pairs

3. Create `src/rag/fine_tune/trainer.py`
   - QLoRA fine-tuning with unsloth/transformers + peft
   - Base model: Qwen/Qwen2.5-1.5B from HuggingFace
   - Training format: ChatML template
   - Hyperparameters: lr=2e-4, epochs=3, batch_size=4, rank=16

4. Create `src/rag/fine_tune/export_model.py`
   - Merge LoRA weights with base model
   - Convert to GGUF format
   - Create Modelfile for Ollama
   - Register as `jobpulse-finetuned`

### Phase 2: Core RAG Rebuild (~45 min)
1. Rewrite `src/rag/embeddings.py`
   - Keep SentenceTransformerEmbedder
   - Remove TfidfEmbedder (ChromaDB handles this)
   - Add batch embedding with progress tracking

2. Create `src/rag/chunker.py`
   - Semantic chunking of rag_document fields
   - 512 token chunks with 128 token overlap
   - Preserve structured fields as metadata

3. Rewrite `src/rag/vector_store.py`
   - ChromaDB backend
   - Collections: jobpulse_chunks, jobpulse_jobs
   - Metadata filtering: country, work_mode, seniority_level, skills
   - Persistent storage in data/rag/chromadb/

4. Rewrite `src/rag/retriever.py`
   - ChromaDB similarity search with metadata filters
   - Hybrid search: embedding similarity + metadata matching
   - Confidence scoring with low-confidence threshold

5. Create `src/rag/prompts.py`
   - Centralized prompt templates for each question type
   - System prompt for fine-tuned model
   - Token budget management

6. Rewrite `src/rag/llm.py`
   - Support fine-tuned and base models (configurable)
   - Fine-tuned: jobpulse-finetuned via Ollama
   - Fallback: base qwen2.5:1.5b
   - Streaming support

7. Rewrite `src/rag/assistant.py`
   - Cleaner orchestration
   - Use centralized prompts
   - Improved question type detection

### Phase 3: Integration (~15 min)
1. Update `scripts/build_rag_index.py` for ChromaDB
2. Create `scripts/fine_tune_model.py` CLI
3. Update backend API endpoint (if needed)
4. Update `requirements.txt`

### Phase 4: Testing (~15 min)
1. Test fine-tuning pipeline
2. Test chunking + embedding
3. Test ChromaDB storage + retrieval
4. Test end-to-end RAG flow
5. Test LLM generation with fine-tuned model

## Dependencies to Add

```
# Fine-tuning
unsloth>=2024.0
peft>=0.7.0
datasets>=2.16.0
trl>=0.7.0
bitsandbytes>=0.42.0
accelerate>=0.26.0

# Tokenization
tiktoken>=0.5.0

# Model export
ctransformers>=0.2.0
```

## Key Decisions
- **Base model:** qwen2.5:1.5b (via HuggingFace Qwen/Qwen2.5-1.5B)
- **Fine-tuning method:** QLoRA (efficient, low memory)
- **Vector store:** ChromaDB (replaces numpy brute-force)
- **Embeddings:** all-MiniLM-L6-v2 (proven, fast)
- **LLM hosting:** Ollama (local, no API costs)
- **Fine-tuning data:** Auto-generated + manual Q&A pairs
