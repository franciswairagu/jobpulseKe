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
    
    # Web Frameworks
    'django': 'web_framework',
    'fastapi': 'web_framework',
    'flask': 'web_framework',
    'react': 'web_framework',
    'vue': 'web_framework',
    'angular': 'web_framework',
    'express': 'web_framework',
    'spring': 'web_framework',
    'spring boot': 'web_framework',
    'laravel': 'web_framework',
    'rails': 'web_framework',
    'next.js': 'web_framework',
    'nextjs': 'web_framework',
    'svelte': 'web_framework',
    'nuxt': 'web_framework',
    'asp.net': 'web_framework',
    'aspnet': 'web_framework',
    
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
    'sqlite': 'database',
    'mariadb': 'database',
    'cockroachdb': 'database',
    'neo4j': 'database',
    'graphql': 'database',
    
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
    'transformers': 'ai_ml',
    'openai': 'ai_ml',
    'langchain': 'ai_ml',
    'llm': 'ai_ml',
    'gpt': 'ai_ml',
    'bert': 'ai_ml',
    'spacy': 'ai_ml',
    'nltk': 'ai_ml',
    
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
    'elk': 'devops',
    'ci/cd': 'devops',
    'cicd': 'devops',
    'git': 'devops',
    'github': 'devops',
    'gitlab': 'devops',
    'bitbucket': 'devops',
    
    # Data & Big Data
    'spark': 'data_platform',
    'hadoop': 'data_platform',
    'kafka': 'data_platform',
    'airflow': 'data_platform',
    'dbt': 'data_platform',
    'snowflake': 'data_platform',
    'bigquery': 'data_platform',
    'redshift': 'data_platform',
    'databricks': 'data_platform',
    'delta lake': 'data_platform',
    'hive': 'data_platform',
    
    # Frontend Technologies
    'html': 'frontend',
    'css': 'frontend',
    'scss': 'frontend',
    'sass': 'frontend',
    'webpack': 'frontend',
    'babel': 'frontend',
    'jest': 'frontend',
    'cypress': 'frontend',
    'tailwind': 'frontend',
    'bootstrap': 'frontend',
    
    # Testing & QA
    'pytest': 'testing',
    'unittest': 'testing',
    'selenium': 'testing',
    'jira': 'testing',
    'qc': 'testing',
    'junit': 'testing',
    'mocha': 'testing',
    'rspec': 'testing',
    
    # Soft Skills & Practices
    'agile': 'methodology',
    'scrum': 'methodology',
    'kanban': 'methodology',
    'rest': 'architecture',
    'grpc': 'architecture',
    'microservices': 'architecture',
    'api': 'architecture',
    'design patterns': 'methodology',
    'oop': 'methodology',
    'solid': 'methodology',
    'tdd': 'methodology',
    'bdd': 'methodology',
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
        """Compile regex patterns for each skill for efficient matching"""
        patterns = {}
        for skill in self.taxonomy.keys():
            # Escape special characters and create word boundary pattern
            escaped = re.escape(skill)
            patterns[skill] = re.compile(
                rf'\b{escaped}\b',
                re.IGNORECASE
            )
        return patterns
    
    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """
        Extract skills from job description text.
        
        Returns dict mapping skill_category -> set of extracted skills
        """
        if not text or not isinstance(text, str):
            return {}
        
        text_lower = text.lower()
        skills_by_category = {}
        
        # Match each skill in the taxonomy
        for skill, category in self.taxonomy.items():
            if self.skill_patterns[skill].search(text_lower):
                if category not in skills_by_category:
                    skills_by_category[category] = set()
                skills_by_category[category].add(skill)
        
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
        
        education_map = {
            'phd': 'PhD',
            'master': "Master's Degree",
            'bachelor': "Bachelor's Degree",
            'associate': "Associate Degree",
            'diploma': "Diploma/High School",
        }
        
        for pattern in EDUCATION_PATTERNS:
            if re.search(pattern, text_lower):
                # Extract education level
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
        
        return list(set(education))  # Remove duplicates
    
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
        
        return list(set(certs))  # Remove duplicates
    
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
