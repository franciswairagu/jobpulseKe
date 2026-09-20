FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY ui/jobpulse-backend/jobpulse-backend/requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

# Copy backend application code
COPY ui/jobpulse-backend/jobpulse-backend/ .
RUN rm -f .env .env.local .env.production

# Copy src/ for RAG assistant (sentence-transformers, retriever, etc.)
COPY src/ /app/src/

# Copy data for auto-ingestion (backend loads this if DB is empty)
RUN mkdir -p /app/data/processed /app/data/external /app/data/uploads /app/data/models /app/data/nlp /app/logs
COPY data/external/jobpulseke_master_africa_tech_jobs.csv /app/data/external/
COPY data/processed/master_full.csv /app/data/processed/
COPY data/nlp/jobs_nlp_enriched_20260918_200334.parquet /app/data/nlp/
COPY src/models/tech_category_classifier.joblib /app/data/models/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/docs')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
