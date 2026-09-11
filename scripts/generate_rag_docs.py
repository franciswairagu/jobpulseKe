#!/usr/bin/env python3
"""Generate a PDF explaining the JobPulse RAG system."""

from fpdf import FPDF

class RAGDocsPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "JobPulse RAG System - Technical Documentation", align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 80, 160)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 80, 160)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def code_block(self, code):
        self.set_font("Courier", "", 8)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(40, 40, 40)
        lines = code.strip().split("\n")
        for line in lines:
            self.cell(0, 4, "  " + line, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        self.cell(5, 5, "-")
        self.multi_cell(0, 5, text)
        self.ln(1)

    def simple_list(self, items):
        for item in items:
            self.bullet(item)
        self.ln(2)


pdf = RAGDocsPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title page
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(30, 80, 160)
pdf.ln(40)
pdf.cell(0, 15, "JobPulse RAG System", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 10, "Retrieval-Augmented Generation", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Technical Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(20)
pdf.set_font("Helvetica", "", 11)
pdf.cell(0, 8, "A simple, file-by-file explanation of every RAG-related", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "module in the JobPulse project.", align="C", new_x="LMARGIN", new_y="NEXT")

# ============================================================
# TABLE OF CONTENTS
# ============================================================
pdf.add_page()
pdf.chapter_title("Table of Contents")
pdf.set_font("Helvetica", "", 11)
toc = [
    "1. System Overview - How everything fits together",
    "2. src/rag/__init__.py - Module exports",
    "3. src/rag/vector_store.py - ChromaDB storage and search",
    "4. src/rag/retriever.py - High-level retrieval interface",
    "5. src/rag/llm.py - Ollama LLM wrapper",
    "6. src/rag/assistant.py - Main orchestrator",
    "7. src/rag/chunker.py - Text splitting for embeddings",
    "8. src/rag/prompts.py - Prompt templates",
    "9. src/rag/fine_tune/data_generator.py - Auto Q&A generation",
    "10. src/rag/fine_tune/training_data.py - Manual Q&A management",
    "11. src/rag/fine_tune/trainer.py - QLoRA fine-tuning",
    "12. src/rag/fine_tune/export_model.py - Model export to Ollama",
    "13. scripts/build_rag_index.py - Index builder CLI",
    "14. scripts/fine_tune_model.py - Fine-tuning CLI",
    "15. Data Flow Diagram",
    "16. Quick Reference - All files at a glance",
]
for item in toc:
    pdf.cell(0, 7, item, new_x="LMARGIN", new_y="NEXT")

# ============================================================
# 1. SYSTEM OVERVIEW
# ============================================================
pdf.add_page()
pdf.chapter_title("1. System Overview")
pdf.body_text(
    "JobPulse is an AI-powered job market assistant for the African tech sector. "
    "It uses Retrieval-Augmented Generation (RAG) to answer questions about jobs, "
    "skills, salaries, and market trends across 10 African countries."
)
pdf.body_text(
    "RAG works by first RETRIEVING relevant job postings from a database, then "
    "passing them as context to a language model that GENERATES a natural answer. "
    "This way the AI always grounds its answers in real data."
)

pdf.section_title("The pipeline has 4 stages:")
pdf.simple_list([
    "INGEST: Job postings are collected, NLP-enriched, and chunked into searchable pieces.",
    "INDEX: Chunks are converted to vector embeddings and stored in ChromaDB for fast similarity search.",
    "RETRIEVE: When a user asks a question, it is converted to an embedding and matched against the index.",
    "GENERATE: The matched results are passed as context to Ollama (qwen2.5:1.5b) which writes a natural answer.",
])

pdf.section_title("File roles at a glance:")
pdf.simple_list([
    "vector_store.py = The library (ChromaDB) that stores and searches embeddings",
    "retriever.py = The librarian who knows how to query the library",
    "llm.py = The writer who takes notes and turns them into sentences",
    "assistant.py = The manager who coordinates librarian and writer",
    "chunker.py = The paper cutter that splits long documents into searchable pieces",
    "prompts.py = The instruction manual that tells the writer how to answer",
    "fine_tune/* = Tools to train the writer on JobPulse-specific data",
])

# ============================================================
# 2. __init__.py
# ============================================================
pdf.add_page()
pdf.chapter_title("2. src/rag/__init__.py")
pdf.body_text(
    "This file is the front door of the RAG module. It imports and re-exports "
    "all the important classes so other parts of the codebase can do:"
)
pdf.code_block("from src.rag import JobPulseRAG, JobPulseAssistant")
pdf.body_text(
    "Instead of importing from each sub-file. It lists everything in __all__ "
    "so IDE autocompletion works properly."
)

# ============================================================
# 3. vector_store.py
# ============================================================
pdf.add_page()
pdf.chapter_title("3. src/rag/vector_store.py")
pdf.section_title("What it does:")
pdf.body_text(
    "This is the heart of the retrieval system. It manages a ChromaDB database "
    "that stores job postings as vector embeddings (lists of numbers that capture "
    "meaning). When you search, it finds the embeddings most similar to your query."
)

pdf.section_title("Key concepts:")
pdf.bullet("Embeddings: Each text is converted to a 384-dimensional vector by all-MiniLM-L6-v2. Similar meanings produce similar vectors.")
pdf.bullet("ChromaDB: An open-source vector database. It persists data to disk so the index survives restarts.")
pdf.bullet("Cosine similarity: Measures the angle between two vectors. Score of 1.0 = identical meaning, 0.0 = unrelated.")

pdf.section_title("class SentenceTransformerEmbeddingFunction:")
pdf.body_text(
    "Wraps the sentence-transformers library. When ChromaDB needs to convert "
    "text to vectors, it calls this function. The model all-MiniLM-L6-v2 is "
    "small (80MB) and fast, making it ideal for real-time search."
)
pdf.code_block(
    "def __call__(self, input):\n"
    "    embeddings = self.model.encode(input)\n"
    "    return embeddings.tolist()"
)

pdf.section_title("def _get_embedding_function():")
pdf.body_text(
    "Tries to load sentence-transformers first. If that fails (e.g., not installed), "
    "falls back to ChromaDB's built-in DefaultEmbeddingFunction which uses ONNX."
)

pdf.section_title("class JobVectorStore:")
pdf.body_text("The main class. Here is what each method does:")

pdf.section_title("  _get_client()")
pdf.body_text(
    "Creates a ChromaDB PersistentClient that saves data to data/rag/chromadb/. "
    "Uses lazy loading - only connects when first needed."
)

pdf.section_title("  _get_collection()")
pdf.body_text(
    "Gets or creates a ChromaDB collection named 'jobpulse_jobs'. "
    "A collection is like a table in a database. The metadata config "
    "'hnsw:space: cosine' tells ChromaDB to use cosine similarity for search."
)

pdf.section_title("  build(df, text_field, batch_size)")
pdf.body_text(
    "Takes a DataFrame of job postings and indexes them into ChromaDB.\n\n"
    "Step 1: Extracts the text from the 'rag_document' column.\n"
    "Step 2: For each row, builds a metadata dict with job_id, title, company, "
    "location, country, skills, etc.\n"
    "Step 3: Handles tricky data types - numpy arrays are converted to lists, "
    "NaN values become empty strings, lists are joined with commas.\n"
    "Step 4: Adds documents in batches of 100 to avoid memory issues.\n"
    "Step 5: ChromaDB automatically generates embeddings and stores them."
)

pdf.section_title("  search(query, top_k, where)")
pdf.body_text(
    "Searches the index for the top_k most similar documents.\n\n"
    "Step 1: Converts the query text to an embedding (384-dim vector).\n"
    "Step 2: Finds the k nearest vectors using HNSW (Hierarchical Navigable Small World).\n"
    "Step 3: Returns distance scores. We convert distance to similarity: score = 1.0 - distance.\n"
    "Step 4: Builds a DataFrame with results, metadata, and scores."
)

pdf.section_title("  get_metadata_stats()")
pdf.body_text(
    "Returns statistics: total documents, list of countries, work modes, "
    "and seniority levels found in the index. Used by the frontend dashboard."
)

# ============================================================
# 4. retriever.py
# ============================================================
pdf.add_page()
pdf.chapter_title("4. src/rag/retriever.py")
pdf.section_title("What it does:")
pdf.body_text(
    "This is a higher-level wrapper around JobVectorStore. While vector_store.py "
    "handles the low-level database operations, retriever.py handles the business "
    "logic: loading data, building the index, querying with filters, and formatting "
    "results for the LLM."
)

pdf.section_title("class JobPulseRAG:")
pdf.body_text("The main retriever class.")

pdf.section_title("  __init__(persist_dir)")
pdf.body_text(
    "Creates a JobVectorStore pointed at data/rag/. "
    "The persist_dir is where ChromaDB saves its files."
)

pdf.section_title("  ensure_ready()")
pdf.body_text(
    "The most important method. Called before every query. It checks if the "
    "ChromaDB index already exists. If yes, it loads it. If not, it builds it "
    "from the NLP-enriched parquet file. This means the first query is slower "
    "(builds the index) but subsequent queries are fast."
)

pdf.section_title("  build(nlp_parquet)")
pdf.body_text(
    "Reads the latest NLP output file (a parquet file with enriched job data) "
    "and passes it to the vector store's build method. The NLP pipeline adds "
    "a 'rag_document' field to each job which combines title, description, "
    "skills, company, and location into a single searchable text."
)

pdf.section_title("  query(text, top_k, where)")
pdf.body_text(
    "Performs semantic search. The 'where' parameter allows metadata filtering. "
    "For example: where={'country': 'Kenya'} would only return Kenyan jobs."
)

pdf.section_title("  query_with_filters(text, country, work_mode, seniority_level)")
pdf.body_text(
    "A convenience method that builds the 'where' filter from separate parameters. "
    "Used when the frontend has dropdown filters for country, remote/onsite, etc."
)

pdf.section_title("  has_strong_matches(results, threshold=0.15)")
pdf.body_text(
    "Checks if the top result has a similarity score above 0.15. If not, the "
    "results are considered too weak and the assistant shows a 'no matches' message "
    "instead of forcing a poor answer."
)

pdf.section_title("  format_context(results)")
pdf.body_text(
    "Converts the search results DataFrame into a formatted text block that can "
    "be passed to the LLM. Each result is formatted as:\n\n"
    "[Result 1 | score=0.65] Data Analyst at Company X - Nairobi\n"
    "The full job description text...\n"
    "Skills: python, sql, pandas\n\n"
    "---\n\n"
    "[Result 2 | score=0.62] ..."
)

# ============================================================
# 5. llm.py
# ============================================================
pdf.add_page()
pdf.chapter_title("5. src/rag/llm.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Wraps the Ollama API to generate natural language answers using a local "
    "large language model (qwen2.5:1.5b). Ollama runs the model on your GPU "
    "without sending data to the cloud."
)

pdf.section_title("class LLMConfig:")
pdf.body_text(
    "A dataclass holding model settings:\n"
    "- model: qwen2.5:1.5b (a 1.5B parameter model, small but capable)\n"
    "- base_url: http://localhost:11434 (Ollama's default port)\n"
    "- temperature: 0.3 (low = more focused answers)\n"
    "- top_p: 0.9 (nucleus sampling)\n"
    "- num_ctx: 4096 (max context length in tokens)"
)

pdf.section_title("class OllamaLLM:")
pdf.section_title("  probe()")
pdf.body_text(
    "Checks if Ollama is running by calling the /api/tags endpoint. "
    "Sets self._available to True or False. This is cached so we only "
    "check once."
)

pdf.section_title("  available (property)")
pdf.body_text(
    "Returns True if Ollama is reachable. On first access, it calls probe(). "
    "The assistant uses this to decide whether to use the LLM or fall back to "
    "template answers."
)

pdf.section_title("  generate(prompt, context, system, model)")
pdf.body_text(
    "The main generation method. Here is the flow:\n\n"
    "1. Builds a message list with system prompt + user message.\n"
    "2. The user message is: context + prompt + question.\n"
    "3. Calls Ollama's chat API with temperature=0.3.\n"
    "4. Returns the generated text.\n"
    "5. On failure (Ollama down, timeout), returns None so the system "
    "falls back to templates."
)

pdf.section_title("  has_model(model_name)")
pdf.body_text(
    "Checks if a specific model is loaded in Ollama. Used to check if "
    "the fine-tuned 'jobpulse-finetuned' model is available."
)

pdf.section_title("  pull_model(model_name)")
pdf.body_text(
    "Downloads a model from Ollama's registry. Used during the export "
    "pipeline to register the fine-tuned model."
)

# ============================================================
# 6. assistant.py
# ============================================================
pdf.add_page()
pdf.chapter_title("6. src/rag/assistant.py")
pdf.section_title("What it does:")
pdf.body_text(
    "This is the brain of the system. It coordinates retrieval (retriever.py) "
    "and generation (llm.py) to answer user questions. It also classifies "
    "questions, extracts skills, and builds conversational answers."
)

pdf.section_title("class AssistantAnswer:")
pdf.body_text(
    "A simple dataclass with three fields:\n"
    "- answer: The generated text\n"
    "- confidence: 'grounded' (high confidence), 'low' (weak matches)\n"
    "- sources: List of job postings used as references"
)

pdf.section_title("Question Type Detection:")
pdf.body_text(
    "The assistant classifies questions into 7 types using regex patterns:\n\n"
    "- market_intelligence: 'What skills are in demand?'\n"
    "- skill_inquiry: 'What Python frameworks should I learn?'\n"
    "- job_search: 'Find remote jobs in Kenya'\n"
    "- career_advice: 'How do I become a data scientist?'\n"
    "- salary_compensation: 'What do ML engineers earn?'\n"
    "- company_industry: 'Is Google hiring in Africa?'\n"
    "- location_geography: 'What tech jobs are in Nigeria?'\n\n"
    "Each question type gets a different answer format."
)

pdf.section_title("class JobPulseAssistant:")
pdf.section_title("  ask(question, top_k, market_data)")
pdf.body_text(
    "The main entry point. The flow is:\n\n"
    "1. ensure_ready() - make sure the index is loaded.\n"
    "2. Detect the question type using regex patterns.\n"
    "3. Extract any mentioned skills (python, docker, etc.).\n"
    "4. Query ChromaDB for the top 5 most similar job postings.\n"
    "5. Check if matches are strong enough (score > 0.15).\n"
    "6. If Ollama is available, generate an LLM answer.\n"
    "7. If not, use a template answer based on question type.\n"
    "8. Return AssistantAnswer with the answer, confidence, and sources."
)

pdf.section_title("Answer Templates (when LLM is unavailable):")
pdf.simple_list([
    "_compose_skill_answer: Lists top skills, matching roles, and locations.",
    "_compose_job_answer: Shows matching roles with company, location, and key skills.",
    "_compose_general_answer: Shows results with key skills and hiring companies.",
    "_compose_market_answer: Shows trending skills with counts and percentages.",
    "_compose_no_match_answer: Friendly message with search tips when no good matches found.",
])

pdf.section_title("Data Aggregation Helpers:")
pdf.simple_list([
    "_aggregate_skills: Counts how often each skill appears across results.",
    "_aggregate_locations: Counts which locations appear most.",
    "_aggregate_companies: Counts which companies appear most.",
])

# ============================================================
# 7. chunker.py
# ============================================================
pdf.add_page()
pdf.chapter_title("7. src/rag/chunker.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Splits long job posting texts into smaller, overlapping chunks. "
    "This is necessary because embedding models have a max input length "
    "(usually 512 tokens). If a job description is longer, we need to split it."
)

pdf.section_title("Why overlap?")
pdf.body_text(
    "When you split text at a fixed point, you might cut a sentence in half. "
    "Overlap ensures that important information at the boundary appears in "
    "both chunks. Default: 512 token chunks with 128 token overlap."
)

pdf.section_title("def count_tokens(text):")
pdf.body_text(
    "Counts how many tokens a text contains. Uses tiktoken (OpenAI's tokenizer) "
    "if available, otherwise approximates at 1 token = 4 characters."
)

pdf.section_title("def split_text(text, max_tokens, overlap_tokens):")
pdf.body_text(
    "The core splitting function. Two strategies:\n\n"
    "1. Token-based (with tiktoken): Splits into chunks of exactly max_tokens, "
    "with overlap_tokens of overlap between adjacent chunks.\n\n"
    "2. Character-based (fallback): Splits by character count, trying to break "
    "at sentence boundaries (periods)."
)

pdf.section_title("def chunk_rag_document(rag_document, metadata):")
pdf.body_text(
    "Chunks a single job posting. Returns a list of dicts:\n"
    "{'text': chunk_text, 'chunk_index': 0, 'total_chunks': 3, 'metadata': {...}}\n\n"
    "The metadata (job_id, title, company, etc.) is copied to every chunk "
    "so we know which job each chunk came from."
)

pdf.section_title("def chunk_job_records(records):")
pdf.body_text(
    "Processes multiple job records at once. For each record, it extracts "
    "the rag_document field, chunks it, and preserves the metadata. "
    "Returns a flat list of all chunks."
)

# ============================================================
# 8. prompts.py
# ============================================================
pdf.add_page()
pdf.chapter_title("8. src/rag/prompts.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Stores all the text templates used to communicate with the LLM. "
    "Having prompts in one file makes them easy to edit and test."
)

pdf.section_title("SYSTEM_PROMPT:")
pdf.body_text(
    "The system message sent to the LLM before every conversation. "
    "It tells the model:\n"
    "- You are JobPulse Assistant for the African tech job market\n"
    "- Answer ONLY based on provided context\n"
    "- If context is insufficient, say so honestly\n"
    "- Cite specific job postings\n"
    "- Be concise, use markdown formatting\n"
    "- End with a practical recommendation"
)

pdf.section_title("QUESTION_TYPE_HINTS:")
pdf.body_text(
    "A dict mapping each question type to specific guidance for the LLM. "
    "For example, 'skill_inquiry' tells the LLM to focus on skill demand "
    "and learning recommendations, while 'job_search' says to list relevant "
    "postings with company and location."
)

pdf.section_title("def build_rag_prompt(question, question_type, context):")
pdf.body_text(
    "Builds the user message sent to the LLM. Structure:\n\n"
    "Context:\n{formatted search results}\n\n"
    "Question type: skill_inquiry\n"
    "Guidance: Focus on skill demand, frequency across jobs...\n\n"
    "User question: What Python skills should I learn?\n\n"
    "Using the context above, provide a grounded, helpful answer."
)

pdf.section_title("def format_retrieved_context(results):")
pdf.body_text(
    "Converts the list of search results into a readable text block. "
    "Each result includes a header with score and metadata, followed by "
    "the full text. Results are separated by '---' dividers."
)

# ============================================================
# 9. data_generator.py
# ============================================================
pdf.add_page()
pdf.chapter_title("9. src/rag/fine_tune/data_generator.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Automatically generates question-answer training pairs from job postings. "
    "This is used to fine-tune the LLM on JobPulse-specific data so it gives "
    "better, more domain-specific answers."
)

pdf.section_title("How it works:")
pdf.body_text(
    "For each job posting, it generates 2-3 Q&A pairs using templates:\n\n"
    "Example job: 'Data Analyst at TechCorp in Nairobi, Python, SQL required'\n\n"
    "Generated questions:\n"
    "- 'What skills are required for a Data Analyst?' (skill_inquiry)\n"
    "- 'Find Data Analyst jobs in Nairobi' (job_search)\n"
    "- 'How do I become a Data Analyst?' (career_advice)\n"
    "- 'What are the most in-demand skills in Kenya?' (market_intelligence)\n\n"
    "The answer is built from the job's actual data (skills, title, location)."
)

pdf.section_title("Template types:")
pdf.simple_list([
    "_SKILL_TEMPLATES: 7 templates focused on skills and tech stack",
    "_JOB_SEARCH_TEMPLATES: 7 templates for finding jobs",
    "_CAREER_TEMPLATES: 7 templates for career progression",
    "_MARKET_TEMPLATES: 7 templates for market intelligence",
    "_SALARY_TEMPLATES: 4 templates for compensation",
    "_COMPANY_TEMPLATES: 4 templates for company queries",
    "_LOCATION_TEMPLATES: 4 templates for geographic questions",
])

pdf.section_title("class TrainingDataGenerator:")
pdf.body_text(
    "Main class. Methods:\n\n"
    "- generate_from_parquet(parquet_path): Reads job data, generates Q&A pairs, "
    "saves to data/rag/fine_tuning/auto_generated.jsonl\n\n"
    "- _generate_qa_pairs(row): For a single job, picks 2-3 random template types "
    "(weighted by importance), fills templates with actual job data, and builds "
    "grounded answers."
)

# ============================================================
# 10. training_data.py
# ============================================================
pdf.add_page()
pdf.chapter_title("10. src/rag/fine_tune/training_data.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Manages both auto-generated and manually-written training data. "
    "Auto-generated data comes from templates (data_generator.py). "
    "Manual data is hand-written expert Q&A pairs that teach the model "
    "nuanced responses."
)

pdf.section_title("class TrainingDataManager:")
pdf.body_text("Methods:")

pdf.section_title("  list_manual_pairs()")
pdf.body_text("Returns all manually-written Q&A pairs from manual.jsonl")

pdf.section_title("  add_manual_pair(question, answer, metadata)")
pdf.body_text("Adds a new expert-written Q&A pair to manual.jsonl")

pdf.section_title("  combine_training_data()")
pdf.body_text(
    "Merges auto-generated and manual data into a single training set. "
    "The combined file is saved to data/rag/fine_tuning/training_data.jsonl. "
    "Format for each line:\n"
    '{"messages": [{"role": "system", "content": "..."}, '
    '{"role": "user", "content": "..."}, '
    '{"role": "assistant", "content": "..."}]}'
)

pdf.section_title("  get_stats()")
pdf.body_text(
    "Returns statistics: count of auto-generated pairs, manual pairs, "
    "total, and the question type distribution."
)

# ============================================================
# 11. trainer.py
# ============================================================
pdf.add_page()
pdf.chapter_title("11. src/rag/fine_tune/trainer.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Fine-tunes qwen2.5:1.5b on the JobPulse training data using QLoRA "
    "(Quantized Low-Rank Adaptation). This is a technique that lets you "
    "fine-tune a large model on a single GPU by only training a small "
    "number of additional parameters."
)

pdf.section_title("Key concepts:")
pdf.bullet("QLoRA: Freezes the base model weights in 4-bit precision and trains small adapter layers. Uses only ~2GB of GPU RAM.")
pdf.bullet("LoRA adapters: Small trainable matrices inserted into the model. After training, they can be merged with the base model.")
pdf.bullet("SFT (Supervised Fine-Tuning): The model learns to generate answers in the JobPulse style by training on Q&A pairs.")

pdf.section_title("class JobPulseTrainer:")
pdf.section_title("  prepare_dataset(training_data_path)")
pdf.body_text(
    "Reads the JSONL training file and converts it to the format expected "
    "by the SFTTrainer. Each line becomes a training example with system, "
    "user, and assistant messages."
)

pdf.section_title("  train(output_dir, epochs, batch_size)")
pdf.body_text(
    "The training pipeline:\n\n"
    "1. Load qwen2.5:1.5b in 4-bit quantization (QLoRA).\n"
    "2. Add LoRA adapters to attention layers (rank=16, alpha=32).\n"
    "3. Prepare the training dataset.\n"
    "4. Configure SFTTrainer with the dataset and LoRA config.\n"
    "5. Train for the specified number of epochs.\n"
    "6. Save the LoRA adapter weights to the output directory.\n\n"
    "Output: A small adapter file (~17MB) that contains only the learned "
    "changes, not the full model."
)

# ============================================================
# 12. export_model.py
# ============================================================
pdf.add_page()
pdf.chapter_title("12. src/rag/fine_tune/export_model.py")
pdf.section_title("What it does:")
pdf.body_text(
    "Takes the trained LoRA adapter and merges it with the base qwen2.5:1.5b "
    "model, then registers the result in Ollama so it can be used for generation."
)

pdf.section_title("class ModelExporter:")
pdf.section_title("  merge_adapters(base_model, adapter_dir)")
pdf.body_text(
    "1. Loads the base qwen2.5:1.5b model in float16.\n"
    "2. Loads the LoRA adapter on top using PEFT library.\n"
    "3. Calls merge_and_unload() to fuse the adapter weights into the base.\n"
    "4. Saves the merged model to src/models/fine_tuned/merged/.\n\n"
    "The merged model is a full-sized language model that incorporates "
    "the JobPulse-specific knowledge from training."
)

pdf.section_title("  convert_to_gguf(merged_model_dir)")
pdf.body_text(
    "Converts the merged model to GGUF format (used by Ollama). "
    "Tries llama.cpp first, falls back to ctransformers. "
    "Output: jobpulse-finetuned-q4_k_m.gguf"
)

pdf.section_title("  register_in_ollama(gguf_path, model_name)")
pdf.body_text(
    "Creates an Ollama Modelfile and runs 'ollama create' to register "
    "the fine-tuned model as 'jobpulse-finetuned'. After this, you can "
    "use it just like any other Ollama model."
)

pdf.section_title("  export_full_pipeline()")
pdf.body_text(
    "Runs the complete pipeline: merge -> GGUF -> Ollama. "
    "If GGUF conversion fails (no llama.cpp), it saves the merged model "
    "and reports success."
)

# ============================================================
# 13. build_rag_index.py
# ============================================================
pdf.add_page()
pdf.chapter_title("13. scripts/build_rag_index.py")
pdf.section_title("What it does:")
pdf.body_text(
    "A command-line script that builds the ChromaDB index from the "
    "NLP-enriched job data. Run this after the NLP pipeline has processed "
    "new job data."
)

pdf.section_title("Usage:")
pdf.code_block(
    "# Build the index\n"
    "python scripts/build_rag_index.py\n\n"
    "# Check index stats\n"
    "python scripts/build_rag_index.py --stats\n\n"
    "# Force rebuild\n"
    "python scripts/build_rag_index.py --force"
)

pdf.section_title("What happens internally:")
pdf.simple_list([
    "Finds the latest NLP output parquet file.",
    "Reads it into a pandas DataFrame.",
    "Creates a JobPulseRAG instance.",
    "Calls ensure_ready() which triggers the build.",
    "ChromaDB indexes each job's rag_document as a 384-dim vector.",
    "The index is saved to data/rag/chromadb/ for persistence.",
])

# ============================================================
# 14. fine_tune_model.py
# ============================================================
pdf.add_page()
pdf.chapter_title("14. scripts/fine_tune_model.py")
pdf.section_title("What it does:")
pdf.body_text(
    "A command-line script that manages the fine-tuning pipeline. "
    "Can generate training data, train the model, or export to Ollama."
)

pdf.section_title("Usage:")
pdf.code_block(
    "# Generate training data from job postings\n"
    "python scripts/fine_tune_model.py --generate\n\n"
    "# Show training data stats\n"
    "python scripts/fine_tune_model.py --stats\n\n"
    "# Fine-tune the model (requires GPU)\n"
    "python scripts/fine_tune_model.py --train\n\n"
    "# Export to Ollama\n"
    "python scripts/fine_tune_model.py --export"
)

# ============================================================
# 15. DATA FLOW DIAGRAM
# ============================================================
pdf.add_page()
pdf.chapter_title("15. Data Flow Diagram")
pdf.section_title("Indexing flow (build_rag_index.py):")
pdf.code_block(
    "Job Parquet File\n"
    "      |\n"
    "      v\n"
    "pandas.read_parquet()\n"
    "      |\n"
    "      v\n"
    "JobVectorStore.build(df)\n"
    "      |\n"
    "      +-- for each row:\n"
    "      |     extract rag_document text\n"
    "      |     build metadata dict\n"
    "      |\n"
    "      v\n"
    "ChromaDB collection.add()\n"
    "      |\n"
    "      +-- SentenceTransformerEmbeddingFunction\n"
    "      |     encodes text -> 384-dim vector\n"
    "      |\n"
    "      v\n"
    "Saved to data/rag/chromadb/ on disk"
)

pdf.section_title("Query flow (user asks a question):")
pdf.code_block(
    "User question: 'What Python jobs are in Kenya?'\n"
    "      |\n"
    "      v\n"
    "JobPulseAssistant.ask()\n"
    "      |\n"
    "      +-- 1. _detect_question_type() -> 'job_search'\n"
    "      +-- 2. _extract_mentioned_skills() -> ['python']\n"
    "      +-- 3. JobPulseRAG.query()\n"
    "      |      |\n"
    "      |      v\n"
    "      |    JobVectorStore.search()\n"
    "      |      |\n"
    "      |      +-- encode query -> 384-dim vector\n"
    "      |      +-- find 5 nearest neighbors in ChromaDB\n"
    "      |      +-- return DataFrame with results\n"
    "      |\n"
    "      +-- 4. OllamaLLM.generate() [if available]\n"
    "      |      OR _compose_job_answer() [template fallback]\n"
    "      |\n"
    "      v\n"
    "AssistantAnswer(answer, confidence, sources)\n"
    "      |\n"
    "      v\n"
    "JSON response to frontend"
)

# ============================================================
# 16. QUICK REFERENCE
# ============================================================
pdf.add_page()
pdf.chapter_title("16. Quick Reference - All Files")

files_ref = [
    ("src/rag/__init__.py", "Module exports", "Import convenience"),
    ("src/rag/vector_store.py", "ChromaDB storage", "Embed, store, search vectors"),
    ("src/rag/retriever.py", "Query interface", "Build/load index, query with filters"),
    ("src/rag/llm.py", "Ollama wrapper", "Generate text with local LLM"),
    ("src/rag/assistant.py", "Orchestrator", "Classify question, retrieve, generate"),
    ("src/rag/chunker.py", "Text splitter", "Split docs into token-sized chunks"),
    ("src/rag/prompts.py", "Prompt templates", "System prompts, formatting"),
    ("src/rag/fine_tune/__init__.py", "Fine-tune exports", "Module convenience"),
    ("src/rag/fine_tune/data_generator.py", "Auto Q&A gen", "Templates -> training pairs"),
    ("src/rag/fine_tune/training_data.py", "Data manager", "Auto + manual training data"),
    ("src/rag/fine_tune/trainer.py", "QLoRA trainer", "Fine-tune qwen2.5 with LoRA"),
    ("src/rag/fine_tune/export_model.py", "Model export", "Merge adapters -> Ollama"),
    ("scripts/build_rag_index.py", "Index builder CLI", "Build ChromaDB from parquet"),
    ("scripts/fine_tune_model.py", "Fine-tune CLI", "Generate, train, export"),
]

pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(30, 80, 160)
pdf.set_text_color(255, 255, 255)
pdf.cell(70, 7, "File", fill=True, border=1)
pdf.cell(35, 7, "Role", fill=True, border=1)
pdf.cell(80, 7, "Purpose", fill=True, border=1)
pdf.ln()

pdf.set_font("Helvetica", "", 8)
pdf.set_text_color(40, 40, 40)
for i, (f, role, purpose) in enumerate(files_ref):
    if i % 2 == 0:
        pdf.set_fill_color(245, 245, 250)
    else:
        pdf.set_fill_color(255, 255, 255)
    pdf.cell(70, 6, f, fill=True, border=1)
    pdf.cell(35, 6, role, fill=True, border=1)
    pdf.cell(80, 6, purpose, fill=True, border=1)
    pdf.ln()

pdf.ln(8)
pdf.section_title("Dependencies:")
pdf.simple_list([
    "chromadb: Vector database for persistent storage",
    "sentence-transformers: Generates text embeddings (all-MiniLM-L6-v2)",
    "ollama: Local LLM inference (qwen2.5:1.5b)",
    "pandas: Data manipulation and DataFrame operations",
    "peft + transformers: QLoRA fine-tuning",
    "unsloth: Fast fine-tuning on consumer GPUs",
])

# Save
output_path = "/home/wairagu/Desktop/Moringa/DSF-FT16/module 6/jobpulse/JobPulse_RAG_Documentation.pdf"
pdf.output(output_path)
print(f"PDF saved to: {output_path}")
