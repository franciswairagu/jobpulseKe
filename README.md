# JobPulse — African Tech Job Market Intelligence Platform

**A full-stack data engineering & AI platform analyzing tech job postings across African markets.**

---

## 🎯 Project Vision

JobPulse is a comprehensive intelligence platform that collects, cleans, and analyzes African tech job market data to provide:

- **Market Intelligence**: Regional skills demand, salary distributions, career pathways
- **CV Analysis**: Upload your CV, extract skills, identify gaps, get personalized job matches
- **Job Recommendations**: Hybrid weighted scoring matching skills, experience, and location
- **Course & Interview Prep**: Personalized learning resources and interview practice platforms
- **Career Insights**: Skill distribution by seniority, geographic demand, remote opportunity scores
- **AI-Powered Assistant**: RAG-based chatbot answering market questions grounded in real data

---

## 🏗️ Architecture

```
jobpulse/
├── data/                       # Data pipeline artifacts
│   ├── raw/                    # Individually scraped/collected CSV sources
│   ├── processed/              # Ingested, cleaned & feature-engineered Parquet files
│   ├── analytics/              # Pre-computed analytics JSON (career pathways, skill matrices)
│   ├── external/               # Datasets pulled in from sibling projects
│   └── archive/                # Older/superseded master datasets
├── notebooks/                  # CRISP-DM analysis notebook with EDA visualizations
├── reports/                    # Historical run reports
├── scripts/                    # Command-line entry points
│   ├── run_scrapers.py         # Scraper suite orchestrator
│   ├── merge_csvs.py           # Merge schema-conformant CSVs, dedup on job_id
│   ├── merge_jobpulseke.py     # Merge in the sister jobpulseKe Kenya dataset
│   ├── merge_public_datasets.py# Merge in public HuggingFace job datasets
│   ├── run_stage1_ingestion.py # Stage 1: load + validate + filter -> Parquet
│   ├── run_stage2_cleaning.py  # Stage 2: geo-normalize, dedupe -> Parquet
│   └── run_full_pipeline.py    # Run all stages sequentially
├── src/                        # Core application logic
│   ├── config.py               # Pipeline config (Stages 1–4): paths, schema, taxonomies
│   ├── scraping_config.py      # Scraper-suite config: schema, crawl politeness, keywords
│   ├── collectors/              # Site-specific scrapers (Stage 0 — data collection)
│   ├── utils/                   # Shared helpers for collectors
│   ├── ingestion/               # Stage 1: Data Loading & Ingestion
│   ├── processing/              # Stage 2: Cleaning, Geo-Normalization & Deduplication
│   ├── nlp/                     # Stage 3: Skill & Metadata Extraction
│   ├── analytics/               # Stage 4: Feature Engineering & Aggregations
│   ├── pipeline/                # Orchestration scripts for Kenya-specific collectors
│   └── rag/                     # RAG assistant (vector search + answer composition)
│       ├── assistant.py         # Question type detection + grounded answer composition
│       ├── retriever.py         # TF-IDF / sentence-transformers retrieval
│       ├── vector_store.py      # numpy-based vector store
│       └── validation.py        # Query validation
├── ui/
│   ├── jobpulse-backend/        # FastAPI backend
│   │   └── jobpulse-backend/
│   │       ├── app/
│   │       │   ├── main.py      # FastAPI app with all routers
│   │       │   ├── api/         # API endpoints (auth, jobs, cv, rag, career-insights)
│   │       │   ├── models/      # SQLAlchemy models (User, Job, Skill, Resume)
│   │       │   ├── schemas/     # Pydantic request/response schemas
│   │       │   ├── services/    # Business logic (job_service, cv_service, recommender)
│   │       │   ├── ml/          # ML components (skill extractor, metadata extractor)
│   │       │   └── recommender/ # Job recommender + course/interview recommendations
│   │       └── .env             # Configuration (SQLite, CORS, JWT)
│   └── jobpulse-unified-app2.0/ # React frontend
│       ├── src/
│       │   ├── App.jsx          # Router with all pages
│       │   ├── pages/           # Dashboard, CVAnalyzer, SkillsExplorer, CareerInsights, Assistant
│       │   ├── components/      # Reusable UI components
│       │   ├── api/             # API client functions
│       │   └── state/           # React Context (AppContext, AuthContext)
│       └── vite.config.js       # Vite config with proxy to backend
└── start.sh                     # One-command launcher (backend + frontend)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ (Conda `deepLearning` env or venv)
- Node.js 18+ (for frontend)

### One-Command Launch

```bash
./start.sh
```

This starts both backend (port 8000) and frontend (port 5173).

### Manual Setup

**Backend:**

```bash
cd ui/jobpulse-backend/jobpulse-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=sqlite:///./jobpulse.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:5173"]
ALLOWED_HOSTS=["*"]
EOF

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd ui/jobpulse-unified-app2.0
npm install
npm run dev
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React application |
| Backend API | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Swagger UI documentation |
| ReDoc | http://localhost:8000/redoc | Alternative API documentation |

---

## 📋 Data Pipeline Stages

### Stage 0: Data Collection (Scraping)

Site-specific scrapers under `src/collectors/`, orchestrated by `scripts/run_scrapers.py`.

| Source | Records | Region |
|--------|---------|--------|
| BrighterMonday | ~1,200 | East Africa (Kenya, Tanzania, Uganda, Rwanda) |
| Jobberman | ~1,500 | Nigeria |
| Careers24 | ~1,100 | South Africa |
| Fuzu | ~800 | East Africa |
| HotNigerianJobs | ~600 | Nigeria |
| MyJobMag | ~900 | Africa-wide |
| LinkedIn | ~1,200 | Global (African filters) |
| Indeed | ~800 | Global (African filters) |
| RemoteOK | ~700 | Remote tech jobs |
| WeWorkRemotely | ~400 | Remote jobs |
| Talent.com | ~600 | Global aggregator |
| CareerJet | ~500 | Global aggregator |
| Jobicy | ~300 | Remote jobs |
| HuggingFace datasets | ~2,400 | Public datasets |

### Stage 1: Data Loading & Ingestion

```bash
python scripts/run_stage1_ingestion.py
```

- Loads merged master CSV
- Validates against 22-column schema
- Fills empty descriptions, filters to African/remote-eligible jobs
- Exports to timestamped Parquet files

### Stage 2: Data Cleaning & Deduplication

```bash
python scripts/run_stage2_cleaning.py
```

- Standardizes country/city names
- ISO-8601 date format standardization
- Fuzzy-match deduplication (threshold: 0.85)
- Exports cleaned dataset

### Stage 3: NLP Pipeline & Skill Extraction

```python
from src.nlp import run_stage_3_nlp_extraction
```

- **600+ skills** across 8 categories (programming, frameworks, cloud, databases, AI/ML, etc.)
- Context-aware matching to avoid false positives
- Title-based extraction when descriptions are empty
- Metadata extraction (experience, education, certifications, seniority)

### Stage 4: Feature Engineering & Analytics

```python
from src.analytics.stage4_orchestrator import run_stage_4_analytics
```

- Salary normalization to USD
- Remote eligibility flags
- Experience bucketing (Entry/Mid/Senior/Lead)
- Skill × Region matrix generation
- Career pathway analysis

### Run Full Pipeline

```bash
python scripts/run_full_pipeline.py
```

---

## 🖥️ Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Market overview with top skills, geographic demand, remote trends |
| CV Analyzer | `/cv` | Upload CV, view extracted skills, skill gaps, job matches, courses, interview prep |
| Skills Explorer | `/skills` | Searchable/filterable table of all skills with demand %, growth rate |
| Career Insights | `/career-insights` | Career progression paths, skills by seniority, geographic demand, remote scores |
| AI Assistant | `/assistant` | RAG-powered chatbot for market questions |
| Auth | `/auth` | Login/Register with JWT |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get JWT |
| `/api/auth/me` | GET | Get current user profile |
| `/api/cv/upload` | POST | Upload CV for analysis |
| `/api/cv/{id}/analyze` | POST | Trigger CV analysis |
| `/api/recommendations` | GET | Get course/interview recommendations |
| `/api/jobs/recommended` | GET | Get personalized job matches |
| `/api/jobs` | GET | Search and filter jobs |
| `/api/jobs/skills/demand` | GET | Skill demand analytics |
| `/api/dashboard` | GET | Market intelligence data |
| `/api/career-insights` | GET | Career progression & skill distribution |
| `/api/rag/ask` | POST | Query the AI assistant |

---

## 🤖 RAG Assistant

The AI assistant uses **question type detection** to provide relevant answers:

| Question Type | Example | Response |
|---------------|---------|----------|
| Market Intelligence | "What are the most in-demand skills in Kenya?" | Ranked skill list with job counts and percentages |
| Role Demand | "What are the most needed roles in Nigeria?" | Top job titles with posting counts |
| Skill Inquiry | "What skills do I need for machine learning?" | Relevant skills, locations, learning recommendations |
| Job Search | "Find remote Python developer jobs" | Structured job listings with companies and locations |
| Career Advice | "How do I become a senior data engineer?" | Career levels, key skills, next steps |

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Scraping** | Python, BeautifulSoup4, Cloudscraper, Tenacity |
| **Data Processing** | Pandas, Polars, PyArrow |
| **NLP** | SpaCy, Sentence-Transformers, TF-IDF, Regex |
| **ML** | Scikit-learn (LogisticRegression for tech category classification) |
| **Backend** | FastAPI, SQLAlchemy, SQLite (production: PostgreSQL) |
| **Auth** | JWT (python-jose), bcrypt password hashing |
| **Frontend** | React 19, Vite 8, TailwindCSS 4, React Router 7 |
| **RAG** | TF-IDF / Sentence-Transformers, cosine similarity |
| **Deployment** | Uvicorn, npm, `start.sh` launcher |

---

## 📊 Dataset Info

- **Total Records**: 10,379 jobs (after merge), 9,549 (after cleaning)
- **Schema**: 22 columns including `job_title`, `company`, `job_description`, `country`, `work_mode`, etc.
- **Countries Covered**: 10 (Nigeria, Ghana, Kenya, South Africa, Egypt, Rwanda, Uganda, Morocco, Global Remote)
- **Skills Extracted**: 600+ across 8 categories
- **Analytics Files**: Pre-computed JSON under `data/analytics/` (career pathways, skill matrices, remote trends)

---

## 📓 Notebook

The CRISP-DM analysis notebook at `notebooks/notebook.ipynb` includes:

- **Business Understanding**: Problem statement, objectives, success criteria
- **Data Understanding**: Collection summary, schema definition, quality assessment
- **Data Preparation**: Pipeline stages, execution instructions
- **EDA Visualizations**: 13 sections with charts covering:
  - Geographic distribution (country, work mode)
  - Source distribution
  - Employment type & experience analysis
  - Tech category distribution
  - Top hiring companies
  - Seniority level analysis
  - Skill analysis (top skills, categories)
  - Skill demand heatmap by country
  - Work mode by country
  - Skill richness analysis
  - Job posting trends over time
  - Correlation analysis
  - EDA summary dashboard
- **NLP & Skill Extraction**: Engine overview, metadata extraction
- **Modeling**: Classifier, recommender, RAG engine descriptions
- **Evaluation**: Data quality metrics, skill extraction metrics
- **Deployment**: Running instructions, API endpoints, frontend pages

---

## ⚠️ Known Issues

- **Work mode data**: ~90% of records have `unknown` work mode (inferred from descriptions when available)
- **Employment type**: Only ~5% of records have explicit employment type data
- **Date coverage**: ~50% of records have posting dates (inconsistent formats across sources)
- **Skill taxonomy**: Some niche skills may not be captured in the 600+ taxonomy

---

## 📝 Development Notes

- **Step Gating Rule**: Each stage is designed to be completed and spot-checked before proceeding to the next
- **Geographic Scope**: African countries + remote-eligible roles
- **Performance Target**: Handle 100k+ records efficiently without memory overhead
- **Backend Environment**: Uses Conda `deepLearning` env (not `.venv`) for ML dependencies
- **Data Auto-Ingest**: Backend auto-ingests latest `jobpulse_cleaned_*.parquet` on startup

---

## 📄 License

Proprietary — African Tech Jobs Intelligence Platform

**Moringa School DSF-FT16 Capstone Project**
