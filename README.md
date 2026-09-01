# JobPulse — African Tech Job Market Intelligence Platform

**A large-scale data engineering & AI systems project analyzing 100k+ historical and live tech job postings across African markets.**

---

## 🎯 Project Vision

JobPulse is a comprehensive intelligence platform that collects, cleans, and analyzes African tech job market data to provide:
- **Market Intelligence**: Regional skills demand, salary distributions, career pathways
- **Career Insights**: Seniority level predictions, required experience, professional certifications
- **Job Discovery**: Intelligent search, filtering, and matching across 100k+ clean records
- **AI-Powered Assistance**: RAG-based AI assistant answering market questions grounded in real data

---

## 🏗️ Architecture Overview

```
jobpulse/
├── data/                   # Data pipeline artifacts
│   ├── raw/                # Ingested raw datasets (CSV sources)
│   ├── processed/          # Cleaned, deduplicated Parquet files
│   ├── analytics/          # Pre-aggregated tables for BI
│   └── exports/            # Export formats for Tableau/Metabase
├── src/                    # Core application logic
│   ├── ingestion/          # Data loaders (Stage 1)
│   ├── processing/         # Cleaning & deduplication (Stage 2)
│   ├── nlp/                # Skill extraction (Stage 3)
│   ├── analytics/          # Feature engineering (Stage 4)
│   ├── models/             # ML classifiers (Stage 5)
│   ├── api/                # FastAPI backend (Stage 7)
│   └── rag/                # Vector search & LLM (Stage 8)
├── frontend/               # Streamlit interactive UI
├── reports/                # Quality audits & metrics
├── docker-compose.yml      # Full-stack deployment
└── requirements.txt        # Python dependencies
```

---

## 📋 Execution Stages (Step Gating)

### ✅ **STAGE 1: Data Loading & Ingestion Schema Setup**
- Load local CSV dataset (`master_africa_tech_jobs.csv`)
- Validate against standard schema
- Filter to rich descriptions (>100 chars) & African/remote jobs
- Save to partitioned Parquet files under `data/raw/`

**Status**: Ready for execution  
**Entry Point**: `python run_stage1.py`

---

### **STAGE 2: Data Cleaning, Geo-Normalization & Deduplication**
- High-performance deduplication (MinHash LSH or fuzzy matching)
- Standardize country/city names (lookup tables)
- ISO-8601 date format standardization
- Generate comprehensive quality audit report
- Export clean dataset to `data/processed/jobpulse_cleaned.parquet`

---

### **STAGE 3: NLP Pipeline & Skill Extraction Engine**
- Batched NLP pipeline (SpaCy / Polars) for 100k+ records
- Skill extraction (languages, frameworks, cloud, DBs, AI tools)
- Structured metadata extraction (years of experience, education, certifications)

---

### **STAGE 4: Feature Engineering & Analytics Aggregations**
- Engineer key features: `experience_years`, `salary_min`, `salary_max`, `seniority_level`
- Generate aggregation datasets (Skill × Region matrix, salary distributions)

---

### **STAGE 5: Machine Learning (Category & Seniority Classification)**
- Job category classifier (SGDClassifier / LightGBM on TF-IDF)
- Seniority level classifier
- Model evaluation & artifact export

---

### **STAGE 6: BI & Visualization Layer**
- Export pre-structured datasets for Tableau/Metabase
- Pan-African market overview dataset
- Regional skills intelligence matrix
- Salary & seniority intelligence tables
- Career pathways & profile matching data

---

### **STAGE 7: Full-Stack Application**
- PostgreSQL + pgvector configuration
- FastAPI endpoints (search, analytics, career matching)
- Streamlit interactive UI

---

### **STAGE 8: RAG-Powered AI Assistant**
- Embed descriptions with `sentence-transformers`
- Vector store indexing (ChromaDB / Qdrant)
- BM25 + semantic search pipeline
- LLM integration (Gemini / Claude)

---

### **STAGE 9: Deployment & Automated Refresh**
- Docker containers & `docker-compose.yml`
- Scheduled updaters (APScheduler / GitHub Actions)
- Incremental data refresh without full re-runs

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd jobpulse
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### 2. Run Stage 1 (Data Ingestion)
```bash
python run_stage1.py
```

Expected output:
```
================================================================================
STAGE 1: DATA LOADING & INGESTION SCHEMA SETUP
================================================================================

[STEP 1/4] Loading raw data...
✓ Loaded 12,516 rows, 22 columns

[STEP 2/4] Validating schema...
✓ Schema validation complete

[STEP 3/4] Filtering rich descriptions & geographic relevance...
✓ Filtering complete: 12,516 → [N] rows retained

[STEP 4/4] Saving to Parquet...
✓ Saved [N] rows to data/processed/ingested_raw_YYYYMMDD_HHMMSS.parquet

================================================================================
STAGE 1 COMPLETE
================================================================================
```

### 3. Check Report
```bash
cat reports/stage1_ingestion_report_*.json
```

---

## 📊 Dataset Info

**Source**: `data/raw/master_africa_tech_jobs.csv`  
**Format**: CSV (12,516 rows)  
**Schema**: 22 columns including job_title, company, job_description, country, etc.

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Data Processing** | Pandas, Polars, PyArrow |
| **NLP** | SpaCy, Sentence-Transformers, Hugging Face |
| **ML** | Scikit-learn, LightGBM, TensorFlow |
| **Database** | PostgreSQL, PGVector |
| **Vector Store** | ChromaDB / Qdrant |
| **API** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **Deployment** | Docker, Docker Compose |
| **Scheduling** | APScheduler |

---

## 📝 Development Notes

- **Step Gating Rule**: Each stage must be 100% complete and verified before proceeding to the next
- **Data Quality**: Minimum description length = 100 characters
- **Geographic Scope**: African countries (51) + remote-eligible roles
- **Performance Target**: Handle 100k+ records efficiently without memory overhead

---

## 📄 License

Proprietary - African Tech Jobs Intelligence Platform

---

**Ready for Stage 1 Execution** ✅
