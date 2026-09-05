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

### CV-driven job recommender

The recommender turns an uploaded `.txt`, `.pdf`, or `.docx` CV into a normalised
candidate skill profile, ranks current JobPulse records by required-skill coverage,
and returns the most important skill gaps, learning resources, and mock-interview
actions. Jobs with a deadline in the next seven days are flagged for application
and interview preparation.

```bash
python scripts/recommend_from_cv.py \
  --cv path/to/candidate.pdf \
  --jobs data/external/jobpulseke_master_africa_tech_jobs.csv \
  --top-k 10
```

Output is JSON so it can be consumed by Streamlit or another client. To expose the
same workflow as an upload endpoint, run:

```bash
uvicorn src.api.recommender_api:app --reload
```

`POST /recommend` accepts a `cv` upload, `jobs_path`, and optional `top_k`. The
uploaded CV is placed in a temporary file only for text extraction and is removed
before the response is returned.

---

## 🚀 Quick Start

```bash
cd jobpulse
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### Run JobPulse step by step

All common workflows are available through one command. It always uses the
currently activated Python environment, which makes the instructions work with
either `venv` or Conda.

1. Create and activate an environment, then install dependencies.

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

2. Confirm available actions.

   ```bash
   python scripts/jobpulse.py --help
   ```

3. Fetch current job listings and automatically run the complete pipeline:
   ingestion, cleaning, NLP enrichment, feature engineering, and analytics.

   ```bash
   python scripts/jobpulse.py refresh --max-pages 5
   ```

   Start with one source while testing if desired:

   ```bash
   python scripts/jobpulse.py refresh --sources remoteok --max-pages 2
   ```

4. Generate CV-based job, skill-gap, course, and interview-prep recommendations.

   ```bash
   python scripts/jobpulse.py recommend \
     --cv path/to/candidate.pdf \
     --jobs output/master_africa_tech_jobs.csv \
     --top-k 10
   ```

5. To automate the same full refresh every six hours, copy and configure
   `cron/jobpulse-scrapers.cron.example`, then register it with `crontab`.
   See [Scheduled scraping (cron)](#scheduled-scraping-cron) below.

6. Ask the RAG assistant a grounded question after the first refresh. The
   refresh automatically rebuilds its index from the latest NLP-enriched jobs.

   ```bash
   python scripts/jobpulse.py ask "Which remote Python jobs are available in Kenya?"
   ```

Collect fresh data:
```bash
python scripts/run_scrapers.py --list          # see available sources
python scripts/run_scrapers.py                 # run every scraper
python scripts/merge_jobpulseke.py              # fold in the sister Kenya dataset
python scripts/merge_public_datasets.py          # (optional) supplement with public datasets
```

### Scheduled scraping (cron)

Use the lock-protected wrapper for scheduled collection; it skips a run rather
than allowing a second scrape to overlap an active one. Each successful scrape
automatically runs Stage 1 ingestion, Stage 2 cleaning/deduplication, Stage 3
NLP enrichment, and Stage 4 feature engineering plus analytics exports. It logs
to `logs/scraper-schedule.log`.

```bash
python scripts/run_scheduled_scrape.py --max-pages 5
```

An every-six-hours Nairobi-time cron template is available at
`cron/jobpulse-scrapers.cron.example`. Copy it, set `JOBPULSE_ROOT` and
`JOBPULSE_PYTHON` to the target machine's absolute project and virtual-
environment paths, then install it with `crontab <your-file>`. Cron does not
load an interactive shell, so using the virtual environment's Python executable
is required for reproducible dependencies.

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
