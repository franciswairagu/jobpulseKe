"""
JobPulse Configuration
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ANALYTICS_DATA_DIR = DATA_DIR / "analytics"
NLP_DATA_DIR = DATA_DIR / "nlp"
RAG_DATA_DIR = DATA_DIR / "rag"
EXPORTS_DATA_DIR = DATA_DIR / "exports"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "src" / "models"
# Where analyzed CVs (extracted skills/metadata + predicted category, never
# the raw uploaded document itself) are persisted by TechCategoryClassifier.
ANALYZED_CV_DIR = NLP_DATA_DIR / "analyzed_cvs"

# Ensure directories exist
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ANALYTICS_DATA_DIR, NLP_DATA_DIR, RAG_DATA_DIR, EXPORTS_DATA_DIR, REPORTS_DIR, MODELS_DIR, ANALYZED_CV_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Schema definition for ingested records
EXPECTED_COLUMNS = {
    "job_id": str,
    "source": str,
    "source_job_id": str,
    "job_title": str,
    "company": str,
    "job_description": str,
    "location": str,
    "country": str,
    "work_mode": str,
    "remote_scope": str,
    "job_field": str,
    "industry": str,
    "employment_type": str,
    "experience_required": str,
    "education_required": str,
    "salary": str,
    "currency": str,
    "date_posted": str,
    "application_deadline": str,
    "tech_category": str,
    "vacancy_url": str,
    "scraped_at": str,
}

# African countries ISO codes for filtering
AFRICAN_COUNTRIES = {
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
    "Cameroon", "Cape Verde", "Central African Republic", "Chad", "Comoros",
    "Congo", "Democratic Republic of the Congo", "Côte d'Ivoire", "Djibouti",
    "Egypt", "Equatorial Guinea", "Eritrea", "Ethiopia", "Gabon", "Gambia",
    "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho", "Liberia",
    "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius",
    "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
    "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone",
    "Somalia", "South Africa", "South Sudan", "Sudan", "Eswatini",
    "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
}

AFRICAN_COUNTRY_CODES = {
    "DZ", "AO", "BJ", "BW", "BF", "BI", "CM", "CV", "CF", "TD", "KM", "CG", "CD",
    "CI", "DJ", "EG", "GQ", "ER", "ET", "GA", "GM", "GH", "GN", "GW", "KE", "LS",
    "LR", "LY", "MG", "MW", "ML", "MR", "MU", "MA", "MZ", "NA", "NE", "NG", "RW",
    "ST", "SN", "SC", "SL", "SO", "ZA", "SS", "SD", "SZ", "TZ", "TG", "TN", "UG",
    "ZM", "ZW",
}

# Skill taxonomy for extraction
TECH_SKILLS_TAXONOMY = {
    "programming_languages": [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++",
        "C#", "PHP", "Ruby", "Swift", "Kotlin", "R", "Scala", "Haskell",
        "Perl", "Elixir", "Clojure", "Lua",
    ],
    "frameworks": [
        "React", "Vue", "Angular", "Next.js", "Django", "Flask", "FastAPI",
        "Spring", "Spring Boot", "Express", "Node.js", "Ruby on Rails",
        "Laravel", "ASP.NET", "Nest.js", "Svelte", "Flutter", "React Native",
    ],
    "cloud_platforms": [
        "AWS", "Google Cloud", "Azure", "Heroku", "DigitalOcean", "Linode",
        "Netlify", "Vercel", "Firebase", "GCP",
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "Oracle", "SQL Server", "MariaDB",
        "Neo4j", "SQLite", "CouchDB",
    ],
    "devops_tools": [
        "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
        "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
    ],
    "ai_ml": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost",
        "LightGBM", "OpenAI", "BERT", "GPT", "Hugging Face", "LLM",
    ],
}

# Seniority level mappings
SENIORITY_LEVELS = ["Intern", "Entry-Level", "Mid-Level", "Senior", "Lead", "Executive"]

# Quality thresholds
MIN_JOB_DESCRIPTION_LENGTH = 0  # No minimum - keep all descriptions
DEDUPLICATION_THRESHOLD = 0.85  # For fuzzy matching

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
