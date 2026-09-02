"""
NLP Pipeline and Skill Extraction Module

Handles:
- Job description parsing and tokenization
- Skill extraction (languages, frameworks, tools, cloud, databases, AI tooling)
- Metadata extraction (years of experience, education, certifications)
- Deterministic skill matching against comprehensive taxonomy
"""

from .skill_extractor import SkillExtractor, get_extractor
from .metadata_extractor import MetadataExtractor, get_metadata_extractor
from .nlp_pipeline import NLPPipeline, run_stage_3_nlp_extraction

__all__ = [
    'SkillExtractor',
    'MetadataExtractor', 
    'NLPPipeline',
    'get_extractor',
    'get_metadata_extractor',
    'run_stage_3_nlp_extraction'
]
