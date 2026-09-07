# JobPulse Backend

A FastAPI backend integrating the JobPulseKE recommendation engine and CV
analysis pipeline into a single career-intelligence API.

**Read this before assuming any field is "AI output"** - the sections below
are explicit about what's real model output, what's reconstructed logic, and
what's deterministic scoring dressed up to look like the field the original
spec asked for. Nothing here fabricates a prediction.

---

## 1. Integration map (what's real, what isn't)

| Component | Status | What it actually is |
|---|---|---|
| **Skill/metadata extraction** (skills, years experience, education, certifications, seniority) | ✅ Real, rule-based | `app/ml/preprocessing/skill_extractor.py` - regex/keyword matching. The original `src/nlp/skill_extractor.py` was never uploaded; this is a reconstruction matching the interface `nlp_analysis.ipynb` and `job_loader.py` call (`get_extractor().extract_skills()/.extract_years_experience()`). Swap in the real file at the same path/interface if it becomes available - nothing else changes. |
| **Tech-category classification** | ⚠️ Conditionally real | The actual TF-IDF+LogisticRegression classifier from the notebook, loaded from `CV_CATEGORY_MODEL_PATH` **only if that `.joblib` artifact exists**. It doesn't exist in this project right now (never uploaded/trained here), so `tech_category`/`tech_category_confidence` are `null` and `classifier_available: false` on every response. This is never faked. |
| **CV score (0-100)** | ❌ Not a model output | The notebook's CV analysis never produced a score, strengths, or weaknesses. `cv_score` is a documented, deterministic composite (`app/services/cv_service.py::compute_cv_score`) built from real extracted signals (skill breadth, experience, education, certs). Every API response marks it `score_type: "deterministic_composite"` so it can't be mistaken for ML output. |
| **Recommendation engine** | ✅ Real, uploaded verbatim | `app/recommender/` = your uploaded `src/recommender/` package (`JobRecommender`, `CandidateProfile`, `SkillMatcher`, `resources.py`) with only import paths adjusted for this layout. It's a deterministic hybrid weighted scorer (skills/experience/location), not a trained ML model, and is used exactly as provided - no rescoring, no retraining. |
| **Time-series / job-availability model** | ❌ Descoped (your decision) | No forecasting model exists - the pipeline's own `run_time_series_component.py` says it was rescoped to a reliability audit + market composition report because `date_posted` coverage wasn't trustworthy. Per your decision, job availability is tracked via **CRUD status + `JobStatusHistory`** only. `market_insights` are real DB aggregates, never predictions. |
| **Salary parsing** | ✅ Fixed | The known pipeline bug (African currency symbols like KSh/₦ not recognized) is fixed in `app/services/salary_parser.py`, which recognizes KES, NGN, GHS, ZAR, UGX, TZS alongside USD/EUR/GBP. A parsed salary is only marked `salary_reliable: true` when a currency was unambiguously detected. |
| **AI Assistant (spec section 24)** | Not built | Out of scope for this pass - no LLM wrapper included. The architecture (`ModelPrediction` audit table, clean adapter interfaces) is ready for one to sit on top later without touching the three components above. |

Runtime status of every component is visible at `GET /health` and `GET /api/models`.

---

## 2. Architecture

```
React Frontend
      |
   FastAPI  ── PostgreSQL (users, resumes, jobs, skills, recommendations, model_predictions)
      |     ── Redis + Celery (CV analysis, job ingestion, stale-job sweep)
      |
      ├── app/ml/adapters/cv_analyzer.py        (skill_extractor + optional classifier)
      ├── app/ml/adapters/recommendation.py      (wraps app/recommender/, real package)
      └── app/services/job_service.py            (CRUD job status, no forecasting)
```

- `app/ml/registry/registry.py` loads each model/adapter once at startup and records its real status (`READY` / `DEGRADED` / `NOT_AVAILABLE`).
- `app/models/*` — SQLAlchemy models, portable between PostgreSQL (prod) and SQLite (tests) via `app/models/types.py`.

---

## 3. Running locally

```bash
cp .env.example .env          # edit SECRET_KEY at minimum
docker compose up --build     # api (8000), worker, beat, postgres, redis
```

API docs: `http://localhost:8000/docs`

### Without Docker
```bash
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./dev.db   # or a real Postgres URL
export SECRET_KEY=dev-secret
uvicorn app.main:app --reload
```

### Tests
```bash
pytest tests/ -v
```
Tests run against a fresh SQLite DB per test (no Postgres/Redis required).

---

## 4. Key endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/register`, `/login`, `/refresh`, `/me` | Auth |
| `POST /api/cv/upload` → `POST /api/cv/{id}/analyze` → `GET /api/cv/{id}/status` → `GET /api/cv/{id}` | CV pipeline |
| `GET /api/recommendations` | Courses + interview-platform recommendations, derived from the latest CV analysis's skill gaps |
| `GET /api/jobs/recommended` | Personalized job matches from `JobRecommender` |
| `GET /api/jobs`, `/api/jobs/{id}`, `/api/jobs/{id}/history` | Job search/detail/status history |
| `PATCH /api/jobs/{id}/status` | Manually record an observed status change |
| `POST /api/jobs/ingest` | Ingest a CSV/Parquet in the pipeline's `STANDARD_COLUMNS` schema (or from `JOB_DATASET_PATH` if no file attached) |
| `GET /api/dashboard` | Aggregated view: cv_score, skills, recommendations, available jobs, market insights |
| `GET /health`, `GET /api/models` | Model registry status |

---

## 5. What to plug in later

1. **Trained classifier artifact** → drop the `.joblib` at `CV_CATEGORY_MODEL_PATH`. No code changes needed; `classifier_available` flips to `true` automatically.
2. **Real `src/nlp/skill_extractor.py`** (if it exists) → replace `app/ml/preprocessing/skill_extractor.py`, keeping the `get_extractor().extract_skills()/.extract_years_experience()` interface.
3. **Real time-series model**, if one gets built later → add a new adapter under `app/ml/adapters/`, register it in `app/ml/registry/registry.py`, and extend `market_insights()` - the CRUD status system underneath doesn't need to change.
4. **Alembic migrations** - currently using `Base.metadata.create_all()` for simplicity; swap to Alembic before this touches a real production database with existing data.
5. **Token revocation** - `/api/auth/logout` is currently a no-op (stateless JWT). Add a Redis blacklist if server-side revocation is required.
