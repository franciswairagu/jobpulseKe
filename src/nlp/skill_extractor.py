"""
Deterministic Skill Extraction Engine

Maps job descriptions to standardized skill taxonomy:
- Programming Languages (Python, JavaScript, Java, Go, Rust, etc.)
- Frameworks & Libraries (Django, FastAPI, React, Vue, Spring, etc.)
- Cloud Platforms (AWS, GCP, Azure)
- Databases (PostgreSQL, MongoDB, Redis, etc.)
- AI/ML Tools (TensorFlow, PyTorch, Scikit-learn, etc.)
- DevOps & Infrastructure (Docker, Kubernetes, Terraform, etc.)
- Other Technologies

v2 — Improved word-boundary handling for short/ambiguous skills,
    context-aware patterns, and expanded taxonomy.
"""

import re
import logging
from typing import Dict, Set, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# Comprehensive skill taxonomy - each skill maps to skill category
SKILL_TAXONOMY = {
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
    'assembly': 'programming_language',

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
    'gin': 'web_framework',
    'fiber': 'web_framework',
    'actix': 'web_framework',

    # Cloud Platforms
    'aws': 'cloud_platform',
    'amazon web services': 'cloud_platform',
    'gcp': 'cloud_platform',
    'google cloud': 'cloud_platform',
    'azure': 'cloud_platform',
    'microsoft azure': 'cloud_platform',
    'heroku': 'cloud_platform',
    'digitalocean': 'cloud_platform',
    'linode': 'cloud_platform',
    'cloudflare': 'cloud_platform',
    'netlify': 'cloud_platform',
    'vercel': 'cloud_platform',
    'openstack': 'cloud_platform',

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
    'sqlserver': 'database',
    'mssql': 'database',
    'sqlite': 'database',
    'mariadb': 'database',
    'cockroachdb': 'database',
    'neo4j': 'database',
    'graphql': 'database',
    'prisma': 'database',
    'sequelize': 'database',
    'typeorm': 'database',
    'mongoose': 'database',
    'couchdb': 'database',
    'memcached': 'database',
    'clickhouse': 'database',
    'timescaledb': 'database',
    'supabase': 'database',
    'firebase': 'database',

    # AI/ML Tools
    'tensorflow': 'ai_ml',
    'keras': 'ai_ml',
    'pytorch': 'ai_ml',
    'scikit-learn': 'ai_ml',
    'sklearn': 'ai_ml',
    'xgboost': 'ai_ml',
    'lightgbm': 'ai_ml',
    'catboost': 'ai_ml',
    'pandas': 'ai_ml',
    'numpy': 'ai_ml',
    'opencv': 'ai_ml',
    'huggingface': 'ai_ml',
    'hugging face': 'ai_ml',
    'transformers': 'ai_ml',
    'openai': 'ai_ml',
    'langchain': 'ai_ml',
    'llamaindex': 'ai_ml',
    'llm': 'ai_ml',
    'gpt': 'ai_ml',
    'bert': 'ai_ml',
    'spacy': 'ai_ml',
    'nltk': 'ai_ml',
    'mlflow': 'ai_ml',
    'kubeflow': 'ai_ml',
    'wandb': 'ai_ml',
    'jupyter': 'ai_ml',
    'jupyter notebook': 'ai_ml',
    'colab': 'ai_ml',
    'huggingface hub': 'ai_ml',
    'dall-e': 'ai_ml',
    'midjourney': 'ai_ml',
    'stable diffusion': 'ai_ml',
    'rag': 'ai_ml',
    'vector database': 'ai_ml',
    'pinecone': 'ai_ml',
    'weaviate': 'ai_ml',
    'chromadb': 'ai_ml',
    'milvus': 'ai_ml',
    'langgraph': 'ai_ml',
    'crewai': 'ai_ml',
    'autogen': 'ai_ml',

    # DevOps & Infrastructure
    'docker': 'devops',
    'kubernetes': 'devops',
    'k8s': 'devops',
    'jenkins': 'devops',
    'gitlab ci': 'devops',
    'gitlab ci/cd': 'devops',
    'github actions': 'devops',
    'terraform': 'devops',
    'pulumi': 'devops',
    'ansible': 'devops',
    'chef': 'devops',
    'puppet': 'devops',
    'helm': 'devops',
    'prometheus': 'devops',
    'grafana': 'devops',
    'elk': 'devops',
    'elasticsearch logstash kibana': 'devops',
    'ci/cd': 'devops',
    'cicd': 'devops',
    'git': 'devops',
    'github': 'devops',
    'gitlab': 'devops',
    'bitbucket': 'devops',
    'nagios': 'devops',
    'datadog': 'devops',
    'new relic': 'devops',
    'splunk': 'devops',
    'vault': 'devops',
    'consul': 'devops',
    'nomad': 'devops',
    'vagrant': 'devops',

    # Data & Big Data
    'spark': 'data_platform',
    'apache spark': 'data_platform',
    'hadoop': 'data_platform',
    'kafka': 'data_platform',
    'apache kafka': 'data_platform',
    'airflow': 'data_platform',
    'apache airflow': 'data_platform',
    'dbt': 'data_platform',
    'snowflake': 'data_platform',
    'bigquery': 'data_platform',
    'google bigquery': 'data_platform',
    'redshift': 'data_platform',
    'amazon redshift': 'data_platform',
    'databricks': 'data_platform',
    'delta lake': 'data_platform',
    'hive': 'data_platform',
    'apache hive': 'data_platform',
    'flink': 'data_platform',
    'apache flink': 'data_platform',
    'looker': 'data_platform',
    'Looker': 'data_platform',
    'prefect': 'data_platform',
    'dagster': 'data_platform',
    'luigi': 'data_platform',

    # Analytics & Visualisation
    'tableau': 'analytics',
    'power bi': 'analytics',
    'powerbi': 'analytics',
    'excel': 'analytics',
    'google sheets': 'analytics',
    'looker studio': 'analytics',
    'matplotlib': 'analytics',
    'seaborn': 'analytics',
    'plotly': 'analytics',
    'd3.js': 'analytics',
    'd3': 'analytics',
    'kibana': 'analytics',
    'metabase': 'analytics',
    'superset': 'analytics',
    'apache superset': 'analytics',
    'quicksight': 'analytics',
    'aws quicksight': 'analytics',

    # Frontend Technologies
    'html': 'frontend',
    'html5': 'frontend',
    'css': 'frontend',
    'css3': 'frontend',
    'scss': 'frontend',
    'sass': 'frontend',
    'less': 'frontend',
    'webpack': 'frontend',
    'vite': 'frontend',
    'babel': 'frontend',
    'jest': 'frontend',
    'cypress': 'frontend',
    'playwright': 'frontend',
    'puppeteer': 'frontend',
    'tailwind': 'frontend',
    'tailwindcss': 'frontend',
    'bootstrap': 'frontend',
    'material ui': 'frontend',
    'mui': 'frontend',
    'chakra ui': 'frontend',
    'styled components': 'frontend',
    'redux': 'frontend',
    'zustand': 'frontend',
    'recoil': 'frontend',
    'jquery': 'frontend',
    'daisyui': 'frontend',
    'shadcn': 'frontend',

    # Testing & QA
    'pytest': 'testing',
    'unittest': 'testing',
    'selenium': 'testing',
    'jira': 'testing',
    'qc': 'testing',
    'junit': 'testing',
    'mocha': 'testing',
    'rspec': 'testing',
    'postman': 'testing',
    'soapui': 'testing',
    'k6': 'testing',
    'jmeter': 'testing',
    'gatling': 'testing',
    'testcafe': 'testing',
    'vitest': 'testing',
    'mocha.js': 'testing',
    'chai': 'testing',
    'coverage.py': 'testing',
    'tox': 'testing',

    # Architecture & Practices
    'rest': 'architecture',
    'restful': 'architecture',
    'rest api': 'architecture',
    'grpc': 'architecture',
    'gRPC': 'architecture',
    'graphql': 'architecture',
    'microservices': 'architecture',
    'api': 'architecture',
    'websockets': 'architecture',
    'websocket': 'architecture',
    'message queue': 'architecture',
    'event driven': 'architecture',
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
    'bdd': 'methodology',
    'pair programming': 'methodology',
    'code review': 'methodology',

    # Mobile Development
    'react native': 'mobile',
    'flutter': 'mobile',
    'swiftui': 'mobile',
    'jetpack compose': 'mobile',
    'ionic': 'mobile',
    'xamarin': 'mobile',
    'kotlin multiplatform': 'mobile',

    # Security
    'owasp': 'security',
    'penetration testing': 'security',
    'security audit': 'security',
    'oauth': 'security',
    'jwt': 'security',
    'ssl': 'security',
    'tls': 'security',
    'firewall': 'security',

    # Operating Systems & Infrastructure
    'linux': 'infrastructure',
    'ubuntu': 'infrastructure',
    'centos': 'infrastructure',
    'debian': 'infrastructure',
    'windows server': 'infrastructure',
    'macos': 'infrastructure',
    'freebsd': 'infrastructure',
    'nginx': 'infrastructure',
    'apache': 'infrastructure',
    'caddy': 'infrastructure',
}

# Short skills (1-3 chars) need stricter word-boundary matching to avoid
# false positives inside words like "remote" (r), "going" (go), "rapid" (api).
SHORT_SKILL_THRESHOLD = 3

# Context patterns for ambiguous short skills — if any of these phrases
# appear near the skill word, it's a legitimate match even with strict
# boundaries.  Checked as a secondary pass after the primary regex.
CONTEXT_PATTERNS: Dict[str, List[str]] = {
    'r': [
        r'\br\b.*(?:program|language|studio|statistic|script|package|code|develop)',
        r'(?:program|language|studio|statistic|script|package|code|develop).*\br\b',
        r'\br\b.*(?:data scien|analy|visuali|comput|model|stat)',
        r'(?:using|with|in|know)\s+r\b',
    ],
    'go': [
        r'\bgo\b.*(?:program|language|develop|backend|microservice|golang)',
        r'(?:program|language|develop|backend|microservice|golang).*\bgo\b',
        r'\bgo\b.*(?:goroutine|concurrent|channel)',
        r'(?:using|with|in|know)\s+go\b',
    ],
    'api': [
        r'\bapi\b.*(?:design|develop|build|rest|graphql|endpoint|integrat)',
        r'(?:rest|graphql|build|design|develop|integrat).*\bapi\b',
        r'\bapi\b.*(?:gateway|management|version|documentation)',
    ],
    'rest': [
        r'\brest\b.*(?:api|ful|service|endpoint|architect)',
        r'(?:api|ful|service|endpoint|architect).*\brest\b',
    ],
    'git': [
        r'\bgit\b.*(?:version|control|repository|branch|merge|commit|push|pull|clone)',
        r'(?:version|control|repository|branch|merge|commit|push|pull|clone).*\bgit\b',
        r'(?:using|with|in|know)\s+git\b',
    ],
    'sql': [
        r'\bsql\b.*(?:query|database|server|mysql|postgres|oracle|write)',
        r'(?:query|database|server|mysql|postgres|oracle|write).*\bsql\b',
    ],
}

# Known false-positive phrases where a short skill word appears but does
# NOT refer to the technology (e.g. "Go-to-Market" for "go").
SKILL_FALSE_POSITIVES: Dict[str, List[str]] = {
    'go': ['go-to-market', 'go to market', 'gtm', 'go-live', 'go live'],
}

# Patterns to match years of experience
EXPERIENCE_PATTERNS = [
    r'(\d+)\+?\s*years?\s+of\s+experience',
    r'(\d+)\s*-\s*(\d+)\s*years?\s+experience',
    r'(?:at least|minimum)\s+(\d+)\s*years?',
    r'(\d+)\+\s*years',
]

# Patterns to match education requirements
EDUCATION_PATTERNS = [
    r"(?:bachelor|b\.?s\.?|b\.?a\.?|bachelors?)\s+(?:degree|in)?",
    r"(?:master|m\.?s\.?|m\.?a\.?|masters?)\s+(?:degree|in)?",
    r"(?:phd|ph\.?d\.?|doctorate)",
    r"(?:associate|a\.?s\.?|associates?)",
    r"(?:high school|hs|diploma)",
]

# Patterns to match certifications
CERTIFICATION_PATTERNS = [
    r"(?:aws|certified|certification|cert)",
    r"(?:kubernetes|ckad|cka)",
    r"(?:gcp|google cloud certification)",
    r"(?:azure|az-\d+)",
    r"(?:cissp|oscp|security\+)",
    r"(?:pmp|scrum master|csm)",
]


class SkillExtractor:
    """Deterministic skill extraction from job descriptions"""

    def __init__(self):
        self.taxonomy = SKILL_TAXONOMY
        self.skill_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns with appropriate boundaries per skill length.

        Short skills (<=3 chars) use \\b word boundaries to prevent matching
        inside words.  Longer skills use the lighter (?<![a-z0-9])..(?![a-z0-9])
        boundary which is sufficient for multi-character tokens.
        """
        patterns = {}
        for skill in self.taxonomy.keys():
            escaped = re.escape(skill)
            if len(skill) <= SHORT_SKILL_THRESHOLD:
                # Strict word-boundary matching for short/ambiguous skills
                patterns[skill] = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
            else:
                # Lighter boundary — only blocks adjacency to alphanumerics
                patterns[skill] = re.compile(
                    rf'(?<![a-z0-9]){escaped}(?![a-z0-9])',
                    re.IGNORECASE,
                )
        return patterns

    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """
        Extract skills from job description text.

        Returns dict mapping skill_category -> set of extracted skills.
        """
        if not text or not isinstance(text, str):
            return {}

        text_lower = text.lower()
        skills_by_category: Dict[str, Set[str]] = {}

        # Phase 1: standard regex matching
        for skill, category in self.taxonomy.items():
            if self.skill_patterns[skill].search(text_lower):
                skills_by_category.setdefault(category, set()).add(skill)

        # Phase 2: context-aware rescue for ambiguous short skills that
        # the strict \b pattern may have legitimately excluded.
        for skill, ctx_list in CONTEXT_PATTERNS.items():
            if skill in {s for cats in skills_by_category.values() for s in cats}:
                continue  # already matched
            category = self.taxonomy.get(skill)
            if category is None:
                continue
            for ctx_re in ctx_list:
                if re.search(ctx_re, text_lower):
                    skills_by_category.setdefault(category, set()).add(skill)
                    break

        # Phase 3: reject known false-positive phrases
        for skill, fp_phrases in SKILL_FALSE_POSITIVES.items():
            for fp in fp_phrases:
                if fp in text_lower:
                    # Remove the skill from all categories if found
                    for cat in list(skills_by_category):
                        skills_by_category[cat].discard(skill)
                        if not skills_by_category[cat]:
                            del skills_by_category[cat]
                    break

        return skills_by_category

    def extract_years_experience(self, text: str) -> int:
        """Extract minimum years of experience from text"""
        if not text or not isinstance(text, str):
            return 0

        text_lower = text.lower()
        max_years = 0

        for pattern in EXPERIENCE_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    years = int(match.group(1))
                    max_years = max(max_years, years)
                except (ValueError, IndexError):
                    pass

        return max_years

    def extract_education(self, text: str) -> List[str]:
        """Extract education requirements from text"""
        if not text or not isinstance(text, str):
            return []

        text_lower = text.lower()
        education = []

        for pattern in EDUCATION_PATTERNS:
            if re.search(pattern, text_lower):
                if 'phd' in pattern or re.search(pattern, text_lower).group(0).lower().__contains__('phd'):
                    education.append('PhD')
                elif 'master' in pattern.lower():
                    education.append("Master's Degree")
                elif 'bachelor' in pattern.lower():
                    education.append("Bachelor's Degree")
                elif 'associate' in pattern.lower():
                    education.append("Associate Degree")
                else:
                    education.append("Diploma/High School")

        return list(set(education))

    def extract_certifications(self, text: str) -> List[str]:
        """Extract relevant certifications from text"""
        if not text or not isinstance(text, str):
            return []

        text_lower = text.lower()
        certs = []

        cert_map = {
            'aws': 'AWS Certification',
            'kubernetes': 'Kubernetes Certification',
            'gcp': 'GCP Certification',
            'azure': 'Azure Certification',
            'cissp': 'CISSP',
            'oscp': 'OSCP',
            'pmp': 'PMP',
            'scrum master': 'Scrum Master',
        }

        for cert_key, cert_label in cert_map.items():
            if cert_key in text_lower:
                certs.append(cert_label)

        return list(set(certs))

    def get_skill_summary(self, skills_by_category: Dict[str, Set[str]]) -> Dict[str, int]:
        """Get count of skills by category"""
        return {
            category: len(skills)
            for category, skills in skills_by_category.items()
        }


# Singleton instance
_extractor = None


def get_extractor() -> SkillExtractor:
    """Get or create the skill extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = SkillExtractor()
    return _extractor


def reset_extractor() -> None:
    """Reset the singleton — useful after taxonomy changes."""
    global _extractor
    _extractor = None
