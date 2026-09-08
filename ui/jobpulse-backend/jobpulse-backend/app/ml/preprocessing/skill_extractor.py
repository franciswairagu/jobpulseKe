"""
Skill extraction for job postings and CV text.

IMPORTANT PROVENANCE NOTE
--------------------------------------------------------------------
The original `src/nlp/skill_extractor.py` referenced by
`nlp_analysis.ipynb` and by `src/recommender/job_loader.py`
(`from src.nlp.skill_extractor import get_extractor`) was never
uploaded to this project. This module is a reconstruction built to
match the *interface* the notebook and job_loader.py actually call:

    extractor = get_extractor()
    extracted = extractor.extract_skills(text)        # -> dict[str, set[str]]
    years = extractor.extract_years_experience(text)  # -> int

It is deliberately transparent, keyword/regex based extraction - not
a trained model - because that is also what the notebook's own
description of skill extraction describes ("keyword matching against
a skill list"). If the real `src/nlp/skill_extractor.py` becomes
available, drop it in at this path/interface and nothing else in the
backend needs to change.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, Set


# Comprehensive skill taxonomy - maps skill name to category.
SKILL_TAXONOMY: Dict[str, str] = {
    # Programming Languages
    'python': 'programming_language',
    'javascript': 'programming_language',
    'typescript': 'programming_language',
    'java': 'programming_language',
    'go': 'programming_language',
    'golang': 'programming_language',
    'rust': 'programming_language',
    'c++': 'programming_language',
    'c#': 'programming_language',
    'csharp': 'programming_language',
    'php': 'programming_language',
    'ruby': 'programming_language',
    'kotlin': 'programming_language',
    'swift': 'programming_language',
    'scala': 'programming_language',
    'r': 'programming_language',
    'sql': 'programming_language',
    'bash': 'programming_language',
    'shell': 'programming_language',
    'perl': 'programming_language',
    'matlab': 'programming_language',
    'elixir': 'programming_language',
    'haskell': 'programming_language',
    'clojure': 'programming_language',
    'julia': 'programming_language',
    'dart': 'programming_language',
    'objective-c': 'programming_language',

    # Web Frameworks
    'django': 'web_framework',
    'fastapi': 'web_framework',
    'flask': 'web_framework',
    'react': 'web_framework',
    'vue': 'web_framework',
    'vuejs': 'web_framework',
    'angular': 'web_framework',
    'express': 'web_framework',
    'express.js': 'web_framework',
    'spring': 'web_framework',
    'spring boot': 'web_framework',
    'laravel': 'web_framework',
    'rails': 'web_framework',
    'ruby on rails': 'web_framework',
    'next.js': 'web_framework',
    'nextjs': 'web_framework',
    'nuxt': 'web_framework',
    'nuxt.js': 'web_framework',
    'svelte': 'web_framework',
    'sveltekit': 'web_framework',
    'asp.net': 'web_framework',
    'aspnet': 'web_framework',
    '.net': 'web_framework',
    'dotnet': 'web_framework',
    'node.js': 'web_framework',
    'nodejs': 'web_framework',

    # Cloud Platforms
    'aws': 'cloud_platform',
    'amazon web services': 'cloud_platform',
    'gcp': 'cloud_platform',
    'google cloud': 'cloud_platform',
    'azure': 'cloud_platform',
    'microsoft azure': 'cloud_platform',
    'heroku': 'cloud_platform',
    'digitalocean': 'cloud_platform',
    'cloudflare': 'cloud_platform',
    'netlify': 'cloud_platform',
    'vercel': 'cloud_platform',

    # Databases
    'postgresql': 'database',
    'postgres': 'database',
    'mysql': 'database',
    'mongodb': 'database',
    'redis': 'database',
    'elasticsearch': 'database',
    'dynamodb': 'database',
    'firestore': 'database',
    'cassandra': 'database',
    'oracle': 'database',
    'mssql': 'database',
    'sqlite': 'database',
    'mariadb': 'database',
    'neo4j': 'database',
    'prisma': 'database',
    'supabase': 'database',
    'firebase': 'database',
    'clickhouse': 'database',

    # AI/ML Tools
    'tensorflow': 'ai_ml',
    'keras': 'ai_ml',
    'pytorch': 'ai_ml',
    'scikit-learn': 'ai_ml',
    'sklearn': 'ai_ml',
    'xgboost': 'ai_ml',
    'pandas': 'ai_ml',
    'numpy': 'ai_ml',
    'opencv': 'ai_ml',
    'huggingface': 'ai_ml',
    'hugging face': 'ai_ml',
    'transformers': 'ai_ml',
    'openai': 'ai_ml',
    'langchain': 'ai_ml',
    'llm': 'ai_ml',
    'gpt': 'ai_ml',
    'bert': 'ai_ml',
    'spacy': 'ai_ml',
    'nltk': 'ai_ml',
    'mlflow': 'ai_ml',
    'jupyter': 'ai_ml',
    'jupyter notebook': 'ai_ml',
    'rag': 'ai_ml',
    'vector database': 'ai_ml',
    'pinecone': 'ai_ml',
    'chromadb': 'ai_ml',
    'machine learning': 'ai_ml',
    'deep learning': 'ai_ml',
    'data science': 'ai_ml',
    'data scientist': 'ai_ml',
    'data analysis': 'ai_ml',
    'data analytics': 'ai_ml',
    'data engineering': 'data_platform',
    'data engineer': 'data_platform',
    'data pipeline': 'data_platform',
    'etl': 'data_platform',
    'elt': 'data_platform',
    'statistical modeling': 'ai_ml',
    'statistics': 'ai_ml',
    'neural network': 'ai_ml',
    'neural networks': 'ai_ml',
    'natural language processing': 'ai_ml',
    'nlp': 'ai_ml',
    'computer vision': 'ai_ml',
    'time series': 'ai_ml',
    'predictive modeling': 'ai_ml',
    'predictive analytics': 'ai_ml',
    'reinforcement learning': 'ai_ml',
    'model training': 'ai_ml',
    'model deployment': 'ai_ml',
    'mlops': 'ai_ml',
    'feature engineering': 'ai_ml',
    'a/b testing': 'analytics',
    'ab testing': 'analytics',
    'regression': 'ai_ml',
    'classification': 'ai_ml',
    'clustering': 'ai_ml',
    'forecasting': 'ai_ml',
    'data mining': 'ai_ml',
    'big data': 'data_platform',
    'data warehouse': 'data_platform',
    'data lake': 'data_platform',
    'data lakehouse': 'data_platform',
    'business intelligence': 'analytics',
    'bi': 'analytics',
    'reporting': 'analytics',
    'dashboard': 'analytics',
    'scipy': 'ai_ml',
    'lightgbm': 'ai_ml',
    'catboost': 'ai_ml',
    'onnx': 'ai_ml',
    'tensorrt': 'ai_ml',
    'ray': 'ai_ml',
    'dask': 'ai_ml',
    'polars': 'data_platform',
    'pyarrow': 'data_platform',
    'great expectations': 'data_platform',
    'dbt': 'data_platform',
    'data quality': 'data_platform',
    'data governance': 'data_platform',
    'data modeling': 'data_platform',
    'dimensional modeling': 'data_platform',
    'star schema': 'data_platform',
    'olap': 'data_platform',
    'oltp': 'data_platform',
    'powerbi': 'analytics',
    'metabase': 'analytics',
    'superset': 'analytics',
    'looker': 'analytics',
    'quicksight': 'analytics',
    'redash': 'analytics',
    'jupyter lab': 'ai_ml',
    'colab': 'ai_ml',
    'google colab': 'ai_ml',

    # DevOps & Infrastructure
    'docker': 'devops',
    'kubernetes': 'devops',
    'k8s': 'devops',
    'jenkins': 'devops',
    'gitlab ci': 'devops',
    'github actions': 'devops',
    'terraform': 'devops',
    'ansible': 'devops',
    'helm': 'devops',
    'prometheus': 'devops',
    'grafana': 'devops',
    'ci/cd': 'devops',
    'cicd': 'devops',
    'git': 'devops',
    'github': 'devops',
    'gitlab': 'devops',
    'bitbucket': 'devops',
    'datadog': 'devops',
    'new relic': 'devops',
    'splunk': 'devops',

    # Data & Big Data
    'spark': 'data_platform',
    'apache spark': 'data_platform',
    'hadoop': 'data_platform',
    'kafka': 'data_platform',
    'airflow': 'data_platform',
    'dbt': 'data_platform',
    'snowflake': 'data_platform',
    'bigquery': 'data_platform',
    'redshift': 'data_platform',
    'databricks': 'data_platform',
    'delta lake': 'data_platform',
    'flink': 'data_platform',
    'looker': 'data_platform',
    'prefect': 'data_platform',
    'dagster': 'data_platform',

    # Analytics & Visualisation
    'tableau': 'analytics',
    'power bi': 'analytics',
    'powerbi': 'analytics',
    'excel': 'analytics',
    'google sheets': 'analytics',
    'matplotlib': 'analytics',
    'seaborn': 'analytics',
    'plotly': 'analytics',
    'd3.js': 'analytics',
    'metabase': 'analytics',
    'superset': 'analytics',

    # Frontend Technologies
    'html': 'frontend',
    'html5': 'frontend',
    'css': 'frontend',
    'css3': 'frontend',
    'scss': 'frontend',
    'sass': 'frontend',
    'webpack': 'frontend',
    'vite': 'frontend',
    'jest': 'frontend',
    'cypress': 'frontend',
    'playwright': 'frontend',
    'tailwind': 'frontend',
    'tailwindcss': 'frontend',
    'bootstrap': 'frontend',
    'material ui': 'frontend',
    'mui': 'frontend',
    'redux': 'frontend',
    'zustand': 'frontend',
    'jquery': 'frontend',
    'shadcn': 'frontend',

    # Testing & QA
    'pytest': 'testing',
    'selenium': 'testing',
    'jira': 'testing',
    'junit': 'testing',
    'postman': 'testing',
    'k6': 'testing',
    'jmeter': 'testing',
    'vitest': 'testing',

    # Architecture & Practices
    'rest': 'architecture',
    'restful': 'architecture',
    'rest api': 'architecture',
    'grpc': 'architecture',
    'graphql': 'architecture',
    'microservices': 'architecture',
    'api': 'architecture',
    'websockets': 'architecture',
    'serverless': 'architecture',
    'lambda': 'architecture',
    'aws lambda': 'architecture',

    # Methodologies & Practices
    'agile': 'methodology',
    'scrum': 'methodology',
    'kanban': 'methodology',
    'lean': 'methodology',
    'design patterns': 'methodology',
    'oop': 'methodology',
    'object-oriented': 'methodology',
    'solid': 'methodology',
    'tdd': 'methodology',
    'pair programming': 'methodology',

    # Mobile Development
    'react native': 'mobile',
    'flutter': 'mobile',
    'swiftui': 'mobile',
    'jetpack compose': 'mobile',
    'ionic': 'mobile',
    'xamarin': 'mobile',

    # Security
    'owasp': 'security',
    'penetration testing': 'security',
    'oauth': 'security',
    'jwt': 'security',
    'ssl': 'security',
    'tls': 'security',

    # Operating Systems & Infrastructure
    'linux': 'infrastructure',
    'ubuntu': 'infrastructure',
    'nginx': 'infrastructure',
    'apache': 'infrastructure',
}

# Short skills (<=3 chars) need stricter word-boundary matching
SHORT_SKILL_THRESHOLD = 3

# Context patterns for ambiguous short skills
CONTEXT_PATTERNS: Dict[str, list[str]] = {
    'r': [
        r'\br\b.*(?:program|language|studio|statistic|script|package|code|develop)',
        r'(?:program|language|studio|statistic|script|package|code|develop).*\br\b',
        r'(?:using|with|in|know)\s+r\b',
    ],
    'go': [
        r'\bgo\b.*(?:program|language|develop|backend|microservice|golang)',
        r'(?:program|language|develop|backend|microservice|golang).*\bgo\b',
        r'(?:using|with|in|know)\s+go\b',
    ],
    'api': [
        r'\bapi\b.*(?:design|develop|build|rest|graphql|endpoint|integrat)',
        r'(?:rest|graphql|build|design|develop|integrat).*\bapi\b',
    ],
    'sql': [
        r'\bsql\b.*(?:query|database|server|mysql|postgres|oracle|write)',
        r'(?:query|database|server|mysql|postgres|oracle|write).*\bsql\b',
    ],
}

# Known false-positive phrases
SKILL_FALSE_POSITIVES: Dict[str, list[str]] = {
    'go': ['go-to-market', 'go to market', 'gtm', 'go-live', 'go live'],
    'bi': ['big', 'bid', 'billion', 'bi-weekly', 'bi-monthly'],
}

# Role title -> inferred skills mapping
# When a job title contains a role keyword, these skills are automatically assigned
TITLE_ROLE_SKILLS: Dict[str, list[str]] = {
    'data scientist': ['data science', 'machine learning', 'python', 'statistics', 'data analysis'],
    'data science': ['data science', 'machine learning', 'python', 'statistics'],
    'machine learning': ['machine learning', 'deep learning', 'python', 'tensorflow', 'pytorch'],
    'ml engineer': ['machine learning', 'deep learning', 'python', 'mlops', 'model deployment'],
    'ml ': ['machine learning', 'python'],
    'deep learning': ['deep learning', 'neural networks', 'python', 'tensorflow', 'pytorch'],
    'ai engineer': ['machine learning', 'python', 'deep learning'],
    'ai ': ['machine learning', 'python'],
    'data engineer': ['data engineering', 'etl', 'python', 'sql', 'airflow'],
    'data engineering': ['data engineering', 'etl', 'python', 'sql', 'airflow'],
    'data analyst': ['data analysis', 'sql', 'python', 'excel', 'tableau'],
    'data analytics': ['data analysis', 'sql', 'python', 'excel'],
    'analytics engineer': ['data engineering', 'dbt', 'sql', 'python'],
    'business intelligence': ['business intelligence', 'sql', 'tableau', 'power bi'],
    'bi developer': ['business intelligence', 'sql', 'tableau', 'power bi'],
    'nlp': ['nlp', 'natural language processing', 'python', 'transformers'],
    'natural language': ['nlp', 'natural language processing', 'python'],
    'computer vision': ['computer vision', 'opencv', 'python', 'deep learning'],
    'cv ': ['computer vision', 'opencv', 'python'],
    'etl': ['etl', 'data pipeline', 'python', 'sql'],
    'data pipeline': ['data pipeline', 'etl', 'python', 'airflow'],
    'mlops': ['mlops', 'model deployment', 'docker', 'kubernetes', 'python'],
    'devops mlops': ['mlops', 'docker', 'kubernetes', 'terraform', 'ci/cd'],
    'cloud': ['aws', 'azure', 'gcp'],
    'backend': ['python', 'rest api', 'postgresql', 'docker'],
    'frontend': ['javascript', 'react', 'html', 'css'],
    'full stack': ['javascript', 'react', 'python', 'postgresql', 'docker'],
    'fullstack': ['javascript', 'react', 'python', 'postgresql', 'docker'],
    'software engineer': ['python', 'git', 'rest api', 'docker'],
    'devops': ['docker', 'kubernetes', 'ci/cd', 'terraform'],
    'site reliability': ['linux', 'docker', 'kubernetes', 'monitoring'],
    'sre': ['linux', 'docker', 'kubernetes', 'monitoring'],
    'security': ['owasp', 'penetration testing', 'oauth', 'jwt'],
    'cybersecurity': ['owasp', 'penetration testing', 'oauth', 'ssl', 'tls'],
}


def _build_patterns(taxonomy: Dict[str, str]) -> Dict[str, re.Pattern]:
    """Compile regex patterns with appropriate boundaries per skill length."""
    patterns: Dict[str, re.Pattern] = {}
    for skill in taxonomy.keys():
        escaped = re.escape(skill.lower())
        lowered_skill = skill.lower()
        if len(lowered_skill) <= SHORT_SKILL_THRESHOLD:
            patterns[skill] = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
        else:
            starts_alnum = bool(re.match(r"^[a-z0-9]", lowered_skill))
            ends_alnum = bool(re.search(r"[a-z0-9]$", lowered_skill))
            if starts_alnum and ends_alnum:
                patterns[skill] = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
            elif ends_alnum:
                patterns[skill] = re.compile(rf"(?<!\S){escaped}(?![a-z0-9])")
            else:
                patterns[skill] = re.compile(rf"(?<!\S){escaped}(?!\S)")
    return patterns


_YEARS_EXPERIENCE_PATTERNS = [
    re.compile(r"(\d{1,2})\s*\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE),
    re.compile(r"experience\s*[:\-]?\s*(\d{1,2})\s*\+?\s*years?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s*\+?\s*yrs?\b", re.IGNORECASE),
]

EDUCATION_KEYWORDS = {
    "bachelor": "Bachelor's degree",
    "b.sc": "Bachelor's degree",
    "bsc": "Bachelor's degree",
    "master": "Master's degree",
    "msc": "Master's degree",
    "m.sc": "Master's degree",
    "phd": "PhD",
    "doctorate": "PhD",
    "diploma": "Diploma",
}

CERTIFICATION_KEYWORDS = [
    "aws certified", "azure certified", "google cloud certified", "pmp",
    "ccna", "comptia", "scrum master", "cissp", "ckad", "cka",
]

SENIORITY_KEYWORDS = {
    "intern": "Intern",
    "junior": "Junior",
    "entry level": "Entry Level",
    "entry-level": "Entry Level",
    "mid level": "Mid Level",
    "mid-level": "Mid Level",
    "senior": "Senior",
    "lead": "Lead",
    "principal": "Principal",
    "head of": "Head",
    "manager": "Manager",
    "director": "Director",
}


class SkillExtractor:
    """Keyword/regex based skill and metadata extraction."""

    def __init__(self, taxonomy: Dict[str, str] | None = None):
        self.taxonomy = taxonomy or SKILL_TAXONOMY
        self._patterns = _build_patterns(self.taxonomy)

    def extract_title_skills(self, title: str) -> Dict[str, Set[str]]:
        """Extract skills inferred from job title role keywords.

        When a title contains 'Data Scientist', 'ML Engineer', etc.,
        the corresponding domain skills are returned even if the
        description is empty.
        """
        if not title or not isinstance(title, str):
            return {}
        lowered = title.lower()
        results: Dict[str, Set[str]] = {}
        for role_keyword, skills in TITLE_ROLE_SKILLS.items():
            if role_keyword in lowered:
                for skill in skills:
                    category = self.taxonomy.get(skill, 'ai_ml')
                    results.setdefault(category, set()).add(skill)
        return results

    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """Return {category: {skills found}} for the given free text."""
        if not text or not isinstance(text, str):
            return {}
        lowered = text.lower()
        results: Dict[str, Set[str]] = {}

        # Phase 1: standard regex matching
        for skill, pattern in self._patterns.items():
            if pattern.search(lowered):
                category = self.taxonomy[skill]
                results.setdefault(category, set()).add(skill)

        # Phase 2: context-aware rescue for ambiguous short skills
        for skill, ctx_list in CONTEXT_PATTERNS.items():
            if skill in {s for cats in results.values() for s in cats}:
                continue
            category = self.taxonomy.get(skill)
            if category is None:
                continue
            for ctx_re in ctx_list:
                if re.search(ctx_re, lowered):
                    results.setdefault(category, set()).add(skill)
                    break

        # Phase 3: reject known false-positive phrases
        for skill, fp_phrases in SKILL_FALSE_POSITIVES.items():
            for fp in fp_phrases:
                if fp in lowered:
                    for cat in list(results):
                        results[cat].discard(skill)
                        if not results[cat]:
                            del results[cat]
                    break

        return results

    def extract_years_experience(self, text: str) -> int:
        if not text or not isinstance(text, str):
            return 0
        best = 0
        for pattern in _YEARS_EXPERIENCE_PATTERNS:
            for match in pattern.finditer(text):
                try:
                    value = int(match.group(1))
                except (ValueError, IndexError):
                    continue
                if 0 < value <= 40:
                    best = max(best, value)
        return best

    def extract_education(self, text: str) -> list[str]:
        if not text:
            return []
        lowered = text.lower()
        found = {label for keyword, label in EDUCATION_KEYWORDS.items() if keyword in lowered}
        return sorted(found)

    def extract_certifications(self, text: str) -> list[str]:
        if not text:
            return []
        lowered = text.lower()
        return sorted({kw for kw in CERTIFICATION_KEYWORDS if kw in lowered})

    def extract_seniority(self, text: str) -> tuple[str | None, bool]:
        """Return (seniority_level, keyword_found)."""
        if not text:
            return None, False
        lowered = text.lower()
        for keyword, label in SENIORITY_KEYWORDS.items():
            if keyword in lowered:
                return label, True
        return None, False


@lru_cache(maxsize=1)
def get_extractor() -> SkillExtractor:
    """Process-wide singleton, mirroring the notebook's `get_extractor()` usage."""
    return SkillExtractor()
