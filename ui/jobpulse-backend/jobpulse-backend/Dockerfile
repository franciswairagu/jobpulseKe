FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY ui/jobpulse-backend/jobpulse-backend/requirements.txt .
# Image-only RAG runtime (ONNX embeddings + Ollama client) — no torch
COPY ui/jobpulse-backend/jobpulse-backend/requirements-image.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    -r requirements.txt -r requirements-image.txt

# Copy backend application code
COPY ui/jobpulse-backend/jobpulse-backend/ .
RUN rm -f .env .env.local .env.production *.db

# Copy src/ for RAG assistant (retriever, ONNX encoder, etc.)
COPY src/ /app/src/

# Bake the ONNX all-MiniLM-L6-v2 weights into the image so the semantic
# index loads offline (torch/sentence-transformers are intentionally absent)
RUN python -c "from src.rag.onnx_encoder import prefetch_model; prefetch_model('/app/onnx_model')"

# Copy data for auto-ingestion (backend loads this if DB is empty)
RUN mkdir -p /app/data/processed /app/data/external /app/data/uploads /app/data/models /app/data/nlp /app/data/analytics /app/logs
COPY data/external/jobpulseke_master_africa_tech_jobs.csv /app/data/external/
COPY data/processed/master_full.csv /app/data/processed/
COPY data/analytics/ /app/data/analytics/
COPY src/models/tech_category_classifier.joblib /app/data/models/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/docs')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
