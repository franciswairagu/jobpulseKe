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

__all__ = [
    'SkillExtractor',
    'MetadataExtractor', 
    'NLPPipeline',
    'get_extractor',
    'get_metadata_extractor',
    'run_stage_3_nlp_extraction'
]


def __getattr__(name):
    """Load the Polars-dependent pipeline only when a caller needs it.

    Skill extraction powers the CV recommender and should remain usable in a
    minimal API installation where the batch analytics extras are not present.
    """
    if name in {"NLPPipeline", "run_stage_3_nlp_extraction"}:
        from .nlp_pipeline import NLPPipeline, run_stage_3_nlp_extraction
        return {"NLPPipeline": NLPPipeline, "run_stage_3_nlp_extraction": run_stage_3_nlp_extraction}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
