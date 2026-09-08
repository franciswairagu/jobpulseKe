# JobPulse

### African Tech Job Market Intelligence Platform

> Turning fragmented job data across 54 African countries into actionable career intelligence.

---

## The Problem

Africa's tech job market is invisible.

Not because jobs don't exist — there are thousands of them — but because they're scattered across dozens of disconnected job boards, each serving a single country or niche. A developer in Nairobi checks BrighterMonday and Fuzu. Someone in Lagos browses Jobberman and HotNigerianJobs. A Capetown-based engineer scans Careers24 and PNet. Remote-friendly roles live on LinkedIn, RemoteOK, and WeWorkRemotely, buried under global noise.

There is no unified view of what African tech employers are actually hiring for. No single source that answers:

- Which skills are in demand across the continent?
- How does the Kenyan market differ from Nigeria's or South Africa's?
- What does a data engineer in Ghana need to know vs. one in Rwanda?
- Where are the gaps — and what should a developer learn next?

Job seekers waste hours scanning multiple boards, unable to quantify their skill gaps or find personalized guidance. Recruiters and analysts lack a single source of truth for African tech hiring trends. Educators and policymakers operate without workforce data.

**JobPulse exists to change that.**

---

## What JobPulse Does

JobPulse is a full-stack data engineering and AI platform that scrapes, cleans, analyzes, and serves African tech job market data as a unified intelligence platform.

It operates as a four-stage pipeline:

```
Scrape → Clean → Extract → Analyze → Serve
```

### Stage 0: Data Collection

16 site-specific scrapers collect job postings from across the continent and global remote boards:

| Source | Region Focus |
|--------|-------------|
| BrighterMonday | East Africa (Kenya, Tanzania, Uganda, Rwanda) |
| Fuzu | East Africa |
| JobWeb Kenya | Kenya |
| MyJobMag | Africa-wide |
| Jobberman | Nigeria |
| HotNigerianJobs | Nigeria |
| Careers24 | South Africa |
| PNet | South Africa |
| Indeed | Global (African filters) |
| LinkedIn | Global (guest scraping) |
| RemoteOK | Remote tech jobs |
| WeWorkRemotely | Remote jobs |
| Jobicy | Remote jobs |
| Talent.com | Global aggregator |
| CareerJet | Global aggregator |
| HuggingFace datasets | Public datasets |

Each scraper respects polite crawling practices — configurable delays, retries, timeouts, and page caps. A broad matrix of 50+ tech search terms drives volume across search-based boards.

### Stage 1: Ingestion

The merged master dataset (10,379 records from 14+ sources) is validated against a standard 22-column schema, filtered to African countries and remote-eligible roles, and exported as timestamped Parquet files.

### Stage 2: Cleaning & Deduplication

Country and city names are standardized. Dates are normalized to ISO-8601. Fuzzy-match deduplication (threshold: 0.85) removes cross-source duplicates. The result: 9,549 clean records.

### Stage 3: NLP & Skill Extraction

A deterministic extraction engine maps job descriptions to a standardized taxonomy of 600+ skills across 8 categories:

- **Programming Languages**: Python, JavaScript, Java, Go, Rust, C++, SQL, Bash, and 20+ more
- **Web Frameworks**: Django, Flask, FastAPI, React, Vue, Angular, Spring Boot, Laravel, Rails
- **Cloud Platforms**: AWS, Azure, GCP, Heroku, DigitalOcean
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
- **AI/ML**: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy, Hugging Face
- **DevOps**: Docker, Kubernetes, Terraform, Jenkins, GitHub Actions
- **Data Platforms**: Spark, Kafka, Airflow, Snowflake, dbt
- **Analytics**: Tableau, Power BI, Excel, Metabase

Alongside skills, the pipeline extracts years of experience, education level, certifications, employment type, and seniority level (Intern through Executive).

### Stage 4: Feature Engineering

Engineered features include salary normalization to USD, remote eligibility flags, Pan-African role detection, experience bucketing, skill richness scoring, and certification requirements. The output: 42 columns of structured intelligence per job posting.

---

## The Platform

### For Job Seekers

**CV Analysis** — Upload a PDF or DOCX. The system extracts your skills, experience, education, and certifications, then scores your market match against real job data. A radar chart shows where you stand vs. market demand across 7 skill categories.

**Skill Gap Analysis** — See exactly which skills employers want that you're missing, ranked by learning priority. Each gap shows demand percentage, posting count, and difficulty level.

**Job Recommendations** — A hybrid weighted scorer (skills 65%, preferred skills 15%, experience 15%, location 5%) ranks jobs by fit. Every recommendation explains why — which skills match, which are missing, and whether a deadline is approaching.

**Course Recommendations** — Each skill gap maps to a curated course from Coursera, Udemy, Microsoft Learn, or platform-specific tutorials. Every course shows duration and difficulty level so you can plan your learning.

**Interview Preparation** — Skill-specific mock interview recommendations: coding interviews on Pramp, system design on Interviewing.io, with session duration estimates.

**Career Paths** — Derives potential career roles from job data and scores each by your current skill overlap, showing exactly which skills to build for each path.

**AI Assistant** — A RAG-powered chatbot grounded in the actual job database. Ask "What Python roles are available in Kenya?" and get sourced answers with match scores — never hallucinated market facts.

### For the Market

**Market Intelligence Dashboard** — Most demanded skill, fastest growing skill, remote opportunity percentage, trending skills bar charts, and demand trend lines — filterable by 23 African countries and time periods.

**Skills Explorer** — A searchable, sortable table of every tracked skill with demand percentage, growth rate, job count, popular role, and trend status (Growing / Stable / Declining).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Scraping | Python, Requests, BeautifulSoup4, Cloudscraper, Tenacity |
| Data Processing | Pandas, Polars, PyArrow, NumPy |
| NLP | SpaCy, Sentence-Transformers, Hugging Face, custom regex extractors |
| ML | Scikit-learn, TF-IDF + LogisticRegression classifier |
| Database | PostgreSQL (production), SQLite (development), SQLAlchemy ORM |
| Backend API | FastAPI, Uvicorn, Pydantic v2, Celery + Redis |
| Frontend | React 18, Vite, TailwindCSS, Recharts, Lucide Icons |
| Auth | JWT (python-jose), bcrypt |
| Deployment | Docker, Docker Compose |
| Testing | Pytest, httpx |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                   │
│  Dashboard · CV Analyzer · Skills · Assistant        │
└──────────────────────┬──────────────────────────────┘
                       │ Vite proxy
┌──────────────────────▼──────────────────────────────┐
│               Backend API (FastAPI)                   │
│  Auth · Jobs · CV · Recommendations · RAG · Dashboard│
└──────────┬──────────────────────────────┬───────────┘
           │                              │
┌──────────▼──────────┐    ┌──────────────▼───────────┐
│   PostgreSQL DB     │    │    Celery Workers (Redis)  │
│  users · jobs ·     │    │  CV analysis · scraping    │
│  skills · recs      │    │  pipeline scheduling       │
└─────────────────────┘    └──────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│              Data Pipeline (Python)                   │
│  Scrapers → Ingestion → Cleaning → NLP → Analytics   │
└─────────────────────────────────────────────────────┘
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Total job records | 10,379 |
| Clean records after dedup | 9,549 |
| Scraper implementations | 16 |
| Data sources | 14+ |
| Skills in taxonomy | 600+ |
| Curated courses | 100+ |
| African countries covered | 54 |
| Database tables | 11 |
| API endpoints | 20+ |
| Frontend pages | 5 |
| Output columns per job | 42 |

---

## Context

JobPulse was built as a capstone project for the **Moringa School Data Science & Full-Stack Bootcamp (DSF-FT16)**, Module 6. It combines data engineering, natural language processing, machine learning, and full-stack web development into a single production-oriented platform.

The project started with a simple question: *What are African tech companies actually hiring for?* The answer required building an end-to-end system — from scraping job boards across the continent to serving personalized career intelligence through a web application.

Every design decision was made with real-world constraints in mind: polite crawling practices, handling incomplete data from inconsistent sources, extracting meaning from unstructured job descriptions, and presenting actionable insights rather than raw statistics.

---

## License

Built with care in Nairobi, Kenya.
