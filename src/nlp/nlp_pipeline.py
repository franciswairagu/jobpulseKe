"""
NLP Pipeline Orchestrator

Batched processing of job descriptions using Polars for memory efficiency.
Combines skill extraction and metadata extraction into unified pipeline.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

import pandas as pd
import polars as pl

from src.nlp.skill_extractor import SkillExtractor, get_extractor
from src.nlp.metadata_extractor import MetadataExtractor, get_metadata_extractor

logger = logging.getLogger(__name__)


class NLPPipeline:
    """
    Orchestrates batched NLP processing of job postings.
    
    Processes:
    - Skill extraction (tools, languages, frameworks, databases, AI, DevOps)
    - Metadata extraction (experience, education, certifications, seniority)
    - Aggregations by region, skill category, employment type
    """
    
    def __init__(self, batch_size: int = 1000):
        """
        Initialize NLP pipeline.
        
        Args:
            batch_size: Number of records to process per batch (for memory efficiency)
        """
        self.batch_size = batch_size
        self.skill_extractor = get_extractor()
        self.metadata_extractor = get_metadata_extractor()
        
        # Aggregation containers
        self.skill_counts = defaultdict(lambda: defaultdict(int))  # skill_category -> skill -> count
        self.skill_by_region = defaultdict(lambda: defaultdict(int))  # region -> skill_category -> count
        self.seniority_distribution = defaultdict(int)
        self.experience_stats = {'min': float('inf'), 'max': 0, 'total': 0, 'count': 0}
        self.work_mode_distribution = defaultdict(int)
        self.employment_type_distribution = defaultdict(int)
    
    def process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single job record through NLP pipeline.
        
        Returns enriched record with extracted skills and metadata
        """
        job_desc = record.get('job_description', '')
        job_title = record.get('title', '')
        country = record.get('country', '')
        
        # Extract skills
        skills = self.skill_extractor.extract_skills(job_desc)
        skills_summary = self.skill_extractor.get_skill_summary(skills)
        
        # Extract metadata
        years_exp = self.skill_extractor.extract_years_experience(job_desc)
        education = self.skill_extractor.extract_education(job_desc)
        certifications = self.skill_extractor.extract_certifications(job_desc)
        
        seniority = self.metadata_extractor.extract_seniority_level(job_title, job_desc)
        employment_type = self.metadata_extractor.extract_employment_type(job_desc)
        work_mode = self.metadata_extractor.extract_work_mode(job_desc)
        salary_range = self.metadata_extractor.extract_salary_range(job_desc)
        is_remote_eligible = self.metadata_extractor.is_remote_eligible(job_desc, country)
        
        # Update aggregations
        self._update_aggregations(skills, seniority, years_exp, work_mode, 
                                 employment_type, country)
        
        # Return enriched record
        return {
            **record,
            'extracted_skills': skills,  # {skill_category: [skill1, skill2, ...]}
            'skill_summary': skills_summary,  # {skill_category: count}
            'years_experience': years_exp,
            'education_required': education,
            'certifications': certifications,
            'seniority_level': seniority.value,
            'employment_type': employment_type,
            'work_mode': work_mode,
            'is_remote_eligible': is_remote_eligible,
            'salary_min': salary_range.get('min'),
            'salary_max': salary_range.get('max'),
            'salary_currency': salary_range.get('currency'),
        }
    
    def _update_aggregations(self, skills: Dict[str, set], seniority, years_exp: int,
                            work_mode: Optional[str], employment_type: Optional[str],
                            country: str):
        """Update aggregation counters"""
        # Update skill counts
        for category, skill_set in skills.items():
            for skill in skill_set:
                self.skill_counts[category][skill] += 1
                if country:
                    self.skill_by_region[country][category] += 1
        
        # Update seniority
        self.seniority_distribution[seniority.value] += 1
        
        # Update experience stats
        if years_exp > 0:
            self.experience_stats['min'] = min(self.experience_stats['min'], years_exp)
            self.experience_stats['max'] = max(self.experience_stats['max'], years_exp)
            self.experience_stats['total'] += years_exp
            self.experience_stats['count'] += 1
        
        # Update work mode
        if work_mode:
            self.work_mode_distribution[work_mode] += 1
        
        # Update employment type
        if employment_type:
            self.employment_type_distribution[employment_type] += 1
    
    def run_pipeline(self, input_parquet: Path, output_parquet: Path) -> Dict[str, Any]:
        """
        Execute full NLP pipeline on parquet dataset.
        
        Args:
            input_parquet: Path to cleaned dataset
            output_parquet: Path to save enriched dataset
        
        Returns:
            In-memory summary of the pipeline run (skills extracted,
            distributions, etc.) — not written to disk.
        """
        logger.info("\n" + "="*80)
        logger.info("STAGE 3: NLP PIPELINE & SKILL EXTRACTION")
        logger.info("="*80)
        
        logger.info("\n[STEP 1/4] Loading cleaned dataset...")
        df = pd.read_parquet(input_parquet)
        input_count = len(df)
        logger.info(f"✓ Loaded {input_count:,} records")
        
        logger.info("\n[STEP 2/4] Processing records through NLP pipeline...")
        
        # Process in batches
        enriched_records = []
        for i in range(0, input_count, self.batch_size):
            batch_end = min(i + self.batch_size, input_count)
            batch = df.iloc[i:batch_end].to_dict('records')
            
            for record in batch:
                enriched = self.process_record(record)
                enriched_records.append(enriched)
            
            # Log progress
            progress_pct = (batch_end / input_count) * 100
            logger.info(f"  Processing: {batch_end:,}/{input_count:,} ({progress_pct:.1f}%)")
        
        logger.info(f"✓ Processed {len(enriched_records):,} records")
        
        logger.info("\n[STEP 3/4] Generating aggregations...")
        aggregations = self._generate_aggregations()
        logger.info(f"✓ Generated aggregation tables")
        
        logger.info("\n[STEP 4/4] Saving enriched dataset...")
        
        # Convert to DataFrame and save
        enriched_df = pd.DataFrame(enriched_records)
        enriched_df.to_parquet(output_parquet)
        logger.info(f"✓ Saved enriched dataset: {output_parquet}")
        
        # In-memory run summary (returned to the caller, not written to disk)
        summary = {
            'stage': 'Stage 3: NLP Pipeline & Skill Extraction',
            'timestamp': datetime.now().isoformat(),
            'input': {
                'records': input_count,
                'columns': len(df.columns),
                'source': str(input_parquet),
            },
            'output': {
                'records': len(enriched_records),
                'columns': len(enriched_df.columns),
                'path': str(output_parquet),
            },
            'skills': {
                'categories': list(self.skill_counts.keys()),
                'total_unique_skills': sum(
                    len(skills) for skills in self.skill_counts.values()
                ),
                'top_skills_by_category': {
                    category: sorted(
                        [(skill, count) for skill, count in skills.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                    for category, skills in self.skill_counts.items()
                },
            },
            'metadata': {
                'seniority_distribution': dict(self.seniority_distribution),
                'experience_stats': {
                    'min': self.experience_stats['min'] if self.experience_stats['count'] > 0 else 0,
                    'max': self.experience_stats['max'],
                    'avg': self.experience_stats['total'] / self.experience_stats['count'] 
                           if self.experience_stats['count'] > 0 else 0,
                    'records_with_exp': self.experience_stats['count'],
                },
                'work_mode_distribution': dict(self.work_mode_distribution),
                'employment_type_distribution': dict(self.employment_type_distribution),
            },
            'regional_skill_distribution': {
                country: {
                    category: count
                    for category, count in skills.items()
                }
                for country, skills in self.skill_by_region.items()
            },
        }
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 3 COMPLETE")
        logger.info(f"  Input Records: {input_count:,}")
        logger.info(f"  Output Records: {len(enriched_records):,}")
        logger.info(f"  Skills Extracted: {summary['skills']['total_unique_skills']}")
        logger.info(f"  Skill Categories: {len(summary['skills']['categories'])}")
        logger.info("="*80 + "\n")
        
        return summary
    
    def _generate_aggregations(self) -> Dict[str, Any]:
        """Generate aggregation tables for BI consumption"""
        aggregations = {
            'skill_matrix': {},  # skill_category x region matrix
            'seniority_distribution': dict(self.seniority_distribution),
            'regional_distribution': {},
        }
        
        return aggregations


def run_stage_3_nlp_extraction(
    input_parquet: Path,
    output_parquet: Path,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Execute Stage 3 NLP pipeline.
    
    Entry point for stage execution.
    """
    pipeline = NLPPipeline(batch_size=batch_size)
    return pipeline.run_pipeline(input_parquet, output_parquet)
