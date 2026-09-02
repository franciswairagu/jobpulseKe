# JobPulse — African Tech Job Market Intelligence Platform

**A large-scale data engineering & AI systems project analyzing tech job postings across African markets.**

---

## 🎯 Project Vision

JobPulse is a comprehensive intelligence platform that collects, cleans, and analyzes African tech job market data to provide:
- **Market Intelligence**: Regional skills demand, salary distributions, career pathways
- **Career Insights**: Seniority level predictions, required experience, professional certifications
- **Job Discovery**: Intelligent search, filtering, and matching across clean records
- **AI-Powered Assistance**: RAG-based AI assistant answering market questions grounded in real data

---

## 🏗️ Architecture

```
jobpulseKe/
├── data/                       # Data pipeline artifacts
│   ├── raw/                    # Individually scraped/collected CSV sources
│   ├── processed/              # Ingested & cleaned Parquet files (Stages 1–2)
│   ├── external/               # Datasets pulled in from sibling projects
│   └── archive/                # Older/superseded master datasets
├── notebooks/                  # Exploratory analysis
├── reports/                    # Historical run reports (see "Reports" below)
├── scripts/                    # Command-line entry points
│   ├── run_scrapers.py         # Scraper suite orchestrator
│   ├── merge_csvs.py           # Merge schema-conformant CSVs, dedup on job_id
│   ├── merge_jobpulseke.py     # Merge in the sister jobpulseKe Kenya dataset
│   ├── merge_public_datasets.py# Merge in public HuggingFace job datasets
│   ├── run_stage1_ingestion.py # Stage 1: load + validate + filter -> Parquet
│   └── run_stage2_cleaning.py  # Stage 2: geo-normalize, dedupe -> Parquet
└── src/                        # Core application logic (all installable as `src.*`)
    ├── config.py                # Pipeline config (Stages 1–4): paths, schema, taxonomies
    ├── scraping_config.py       # Scraper-suite config: schema, crawl politeness, keywords
    ├── collectors/               # Site-specific scrapers (Stage 0 — data collection)
    ├── utils/                    # Shared helpers for collectors (record building, HTML parsing)
    ├── ingestion/                 # Stage 1: Data Loading & Ingestion
    ├── processing/                 # Stage 2: Cleaning, Geo-Normalization & Deduplication
    ├── nlp/                        # Stage 3: Skill & Metadata Extraction
    ├── analytics/                   # Stage 4: Feature Engineering & Aggregations
    ├── pipeline/                     # Orchestration scripts for the Kenya-specific collectors
    ├── models/                        # ML classifiers (Stage 5, planned)
    ├── api/                            # FastAPI backend (Stage 7, planned)
    └── rag/                             # Vector search & LLM (Stage 8, planned)
```

Every module under `src/` is imported with an absolute `src.` prefix (e.g. `from src.collectors.brightermonday import BrighterMondayScraper`), and every script in `scripts/` adds the project root to `sys.path` on startup — so all commands below can be run from the project root regardless of which script you're invoking.

---

## 📋 Execution Stages

### **STAGE 0: Data Collection (Scraping)**
Site-specific scrapers under `src/collectors/`, orchestrated by `scripts/run_scrapers.py`. Each scraper saves its own `<source>.csv` and everything is merged/deduplicated into a master CSV.

### **STAGE 1: Data Loading & Ingestion Schema Setup**
- Load the merged master CSV
- Validate against the standard schema
- Fill empty descriptions, filter to African/remote-eligible jobs
- Save to timestamped Parquet files under `data/processed/`

**Entry point**: `python scripts/run_stage1_ingestion.py`

### **STAGE 2: Data Cleaning, Geo-Normalization & Deduplication**
- Standardize country/city names
- ISO-8601 date format standardization
- Fuzzy-match deduplication
- Export clean dataset to `data/processed/jobpulse_cleaned_*.parquet`

**Entry point**: `python scripts/run_stage2_cleaning.py`

### **STAGE 3: NLP Pipeline & Skill Extraction Engine**
- Batched skill extraction (languages, frameworks, cloud, DBs, AI tools)
- Structured metadata extraction (years of experience, education, certifications, seniority)

**Usage**: `from src.nlp import run_stage_3_nlp_extraction` (no CLI wrapper yet — call it from a notebook or your own script, passing an input/output Parquet path)

### **STAGE 4: Feature Engineering & Analytics Aggregations**
- Engineers `salary_min/max_usd`, `is_remote`, `experience_bucket`, `seniority_order`, etc.
- Generates Skill×Region matrix, salary distributions, career pathways, and exports them as JSON/CSV under `data/analytics/`

**Usage**: `from src.analytics.stage4_orchestrator import run_stage_4_analytics` (no CLI wrapper yet)

### **STAGE 5–9 (planned)**
ML classification, BI/visualization exports, the FastAPI + Streamlit full-stack app, a RAG-powered assistant, and Dockerized deployment. Scaffolding exists under `src/models/`, `src/api/`, `src/rag/` but these stages aren't implemented yet.

---

## 🚀 Quick Start

```bash
cd jobpulseKe
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

Collect fresh data:
```bash
python scripts/run_scrapers.py --list          # see available sources
python scripts/run_scrapers.py                 # run every scraper
python scripts/merge_jobpulseke.py              # fold in the sister Kenya dataset
python scripts/merge_public_datasets.py          # (optional) supplement with public datasets
```

Run the pipeline on the merged dataset:
```bash
python scripts/run_stage1_ingestion.py
python scripts/run_stage2_cleaning.py
```

Each stage prints a summary to the console as it runs (records in/out, columns, reduction rate, etc.) — no separate report files are written (see below).

---

## 📊 Reports

Earlier versions of Stages 1–4 wrote a timestamped JSON "report" file into `reports/` on every run, and Stage 1 additionally produced ad-hoc Markdown/`.txt` verification write-ups after each revision. That report-writing logic has been removed from the pipeline code — each stage still prints its summary statistics to the console (and Stage 4 still exports its real analytics tables as JSON/CSV data), it just no longer persists a separate run-report file.

The `reports/` folder here still contains the JSON reports generated by earlier runs, kept for reference. Nothing was deleted from previous runs; going forward, new runs simply won't add to that folder.

---

## 📊 Dataset Info

**Source**: `data/external/jobpulseke_master_africa_tech_jobs.csv` (merged master feeding Stage 1)
**Schema**: 22 columns including `job_title`, `company`, `job_description`, `country`, `work_mode`, `salary`, etc. — defined in `src/config.py` (`EXPECTED_COLUMNS`) and `src/scraping_config.py` (`SCHEMA_COLUMNS`)

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Scraping** | Requests, BeautifulSoup, Tenacity |
| **Data Processing** | Pandas, Polars, PyArrow |
| **NLP** | SpaCy, Sentence-Transformers, Hugging Face |
| **ML** | Scikit-learn, LightGBM |
| **Database** | PostgreSQL, PGVector (planned) |
| **Vector Store** | ChromaDB / Qdrant (planned) |
| **API** | FastAPI + Uvicorn (planned) |
| **Frontend** | Streamlit (planned) |
| **Deployment** | Docker, Docker Compose (planned) |

---

## ⚠️ Known Issues

This project was assembled by merging an earlier "scraper suite" project into the current analytics pipeline, and a few rough edges from that merge predate this reorganization — flagged here rather than silently papered over:

- **`src/pipeline/run_collection.py` does not currently run.** It expects a module-level `collect()` function from each collector and imports `myjobmag_historical`, `fuzu_historical`, `brightermonday_historical`, and `remotive` collector modules that no longer exist as source files. The functional path for collecting fresh data today is `scripts/run_scrapers.py`, which uses the class-based scrapers in `src/collectors/`.
- **Two config files exist on purpose**: `src/config.py` (paths, schema, and taxonomies used by Stages 1–4) and `src/scraping_config.py` (schema and crawl settings used by the scraper suite). They predate this reorganization as separate systems with separate schemas and haven't been unified.
- **Stages 3 and 4 don't have CLI entry points** (`scripts/run_stage3_*.py` / `run_stage4_*.py`) — only the importable `run_stage_3_nlp_extraction()` / `run_stage_4_analytics()` functions exist. The `reports/stage3_*.json` and `stage4_*.json` files in this repo were produced by earlier ad-hoc invocations (e.g. from the notebook), not a script that ships in this repo.

---

## 📝 Development Notes

- **Step Gating Rule**: Each stage is designed to be completed and spot-checked before proceeding to the next.
- **Geographic Scope**: African countries + remote-eligible roles.
- **Performance Target**: Handle 100k+ records efficiently without memory overhead.

---

## 📄 License

Proprietary - African Tech Jobs Intelligence Platform
