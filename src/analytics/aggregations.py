"""
Analytics Aggregations Module

Generates pre-computed aggregation tables for BI consumption:
1. Skill × Region Matrix
2. Salary Distributions
3. Career Pathways
4. Remote Availability Trends
5. Skills by Seniority Level
"""

import logging
from typing import Dict, List, Any
from collections import defaultdict
import pandas as pd
import numpy as np
import json

logger = logging.getLogger(__name__)


class AnalyticsAggregator:
    """Generate aggregation tables for BI dashboards"""
    
    def __init__(self):
        pass
    
    def generate_skill_region_matrix(self, df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """
        Generate Skill × Region matrix showing skill demand by geography.
        
        Returns: {skill: {region: count}}
        """
        logger.info("Generating Skill × Region matrix...")
        
        matrix = defaultdict(lambda: defaultdict(int))
        
        # Iterate through records
        for idx, row in df.iterrows():
            country = row.get('country', 'Unknown')
            
            # Try extracted_skills first (dict of sets), fallback to skill_summary
            extracted_skills = row.get('extracted_skills', {})
            if isinstance(extracted_skills, dict) and extracted_skills:
                # extracted_skills format: {category: set/list of skills}
                for category, skills in extracted_skills.items():
                    if isinstance(skills, (set, list)) and skills:
                        for skill in skills:
                            matrix[skill][country] += 1
            else:
                # Fallback to skill_summary which is {category: count}
                skill_summary = row.get('skill_summary', {})
                if isinstance(skill_summary, dict):
                    for category, count in skill_summary.items():
                        if count and count > 0:
                            matrix[category][country] += count
        
        # Convert defaultdicts to regular dicts
        result = {skill: dict(regions) for skill, regions in matrix.items()}
        logger.info(f"✓ Generated matrix: {len(result)} skills × {len(set(df['country']))} regions")
        
        return result
    
    def generate_salary_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate salary statistics grouped by:
        - Region (country)
        - Skill category
        - Seniority level
        """
        logger.info("Generating salary distributions...")
        
        distributions = {
            'by_country': {},
            'by_seniority': {},
            'by_skill_category': {},
            'overall': self._compute_salary_stats(df[df['has_salary_data']])
        }
        
        # By country
        for country in df['country'].unique():
            country_df = df[df['country'] == country]
            if len(country_df) > 0:
                distributions['by_country'][country] = {
                    'stats': self._compute_salary_stats(country_df[country_df['has_salary_data']]),
                    'records_total': len(country_df),
                    'records_with_salary': len(country_df[country_df['has_salary_data']]),
                }
        
        # By seniority
        for seniority in df['seniority_level'].unique():
            seniority_df = df[df['seniority_level'] == seniority]
            if len(seniority_df) > 0:
                distributions['by_seniority'][seniority] = {
                    'stats': self._compute_salary_stats(seniority_df[seniority_df['has_salary_data']]),
                    'records_total': len(seniority_df),
                    'records_with_salary': len(seniority_df[seniority_df['has_salary_data']]),
                }
        
        # By skill category
        skill_categories = set()
        for summary in df['skill_summary'].dropna():
            if isinstance(summary, dict):
                skill_categories.update(summary.keys())
        
        for category in skill_categories:
            # Find records that have this skill category
            mask = df['skill_summary'].apply(
                lambda x: isinstance(x, dict) and category in x
            )
            category_df = df[mask]
            if len(category_df) > 0:
                distributions['by_skill_category'][category] = {
                    'stats': self._compute_salary_stats(category_df[category_df['has_salary_data']]),
                    'records_total': len(category_df),
                    'records_with_salary': len(category_df[category_df['has_salary_data']]),
                }
        
        logger.info(f"✓ Generated distributions for {len(distributions['by_country'])} countries")
        
        return distributions
    
    def _compute_salary_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compute salary statistics (min, max, mean, median, quartiles)"""
        if len(df) == 0:
            return {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'q25': None,
                'q75': None,
                'count': 0,
            }
        
        # Get salary data, filtering for non-null and positive values
        salary_data = df['salary_mid_usd'].dropna()
        salary_data = salary_data[salary_data > 0]
        
        if len(salary_data) == 0:
            return {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'q25': None,
                'q75': None,
                'count': 0,
            }
        
        return {
            'min': float(salary_data.min()),
            'max': float(salary_data.max()),
            'mean': float(salary_data.mean()),
            'median': float(salary_data.median()),
            'q25': float(salary_data.quantile(0.25)),
            'q75': float(salary_data.quantile(0.75)),
            'count': len(salary_data),
        }
    
    def generate_remote_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze remote job availability by:
        - Country
        - Skill category
        - Seniority level
        """
        logger.info("Generating remote availability trends...")
        
        trends = {
            'by_country': {},
            'by_seniority': {},
            'by_skill_category': {},
            'overall': self._compute_remote_stats(df),
        }
        
        # By country
        for country in df['country'].unique():
            country_df = df[df['country'] == country]
            trends['by_country'][country] = self._compute_remote_stats(country_df)
        
        # By seniority
        for seniority in df['seniority_level'].unique():
            seniority_df = df[df['seniority_level'] == seniority]
            trends['by_seniority'][seniority] = self._compute_remote_stats(seniority_df)
        
        # By skill category
        skill_categories = set()
        for summary in df['skill_summary'].dropna():
            if isinstance(summary, dict):
                skill_categories.update(summary.keys())
        
        for category in skill_categories:
            mask = df['skill_summary'].apply(
                lambda x: isinstance(x, dict) and category in x
            )
            category_df = df[mask]
            trends['by_skill_category'][category] = self._compute_remote_stats(category_df)
        
        logger.info(f"✓ Generated remote trends for {len(trends['by_country'])} countries")
        
        return trends
    
    def _compute_remote_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute remote availability statistics"""
        total = len(df)
        if total == 0:
            return {'remote': 0, 'hybrid': 0, 'on_site': 0, 'total': 0, 'remote_pct': 0}
        
        remote = len(df[df['is_remote']])
        hybrid = len(df[df['work_mode'] == 'Hybrid'])
        on_site = len(df[df['work_mode'] == 'On-Site'])
        
        return {
            'remote': remote,
            'hybrid': hybrid,
            'on_site': on_site,
            'not_specified': total - remote - hybrid - on_site,
            'total': total,
            'remote_pct': round(100.0 * remote / total, 2) if total > 0 else 0,
            'pan_african_pct': round(100.0 * len(df[df['is_pan_african']]) / total, 2) if total > 0 else 0,
        }
    
    def generate_career_pathways(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze career progression patterns:
        - Skills progression from Entry → Senior → Lead
        - Experience distribution by seniority
        - Salary progression
        """
        logger.info("Generating career pathway analysis...")
        
        pathways = {
            'seniority_progression': {},
            'skills_by_seniority': {},
            'salary_by_seniority': {},
            'experience_by_seniority': {},
        }
        
        seniority_levels = ['Intern', 'Entry Level', 'Mid-Level', 'Senior', 'Lead', 'Executive']
        
        for seniority in seniority_levels:
            seniority_df = df[df['seniority_level'] == seniority]
            
            if len(seniority_df) == 0:
                continue
            
            # Record count
            pathways['seniority_progression'][seniority] = len(seniority_df)
            
            # Top skills for this level
            skill_counts = defaultdict(int)
            for summary in seniority_df['skill_summary'].dropna():
                if isinstance(summary, dict):
                    for category, count in summary.items():
                        skill_counts[category] += 1
            
            pathways['skills_by_seniority'][seniority] = dict(
                sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            
            # Salary progression
            pathways['salary_by_seniority'][seniority] = self._compute_salary_stats(
                seniority_df[seniority_df['has_salary_data']]
            )
            
            # Experience distribution
            exp_dist = seniority_df['experience_bucket'].value_counts().to_dict()
            pathways['experience_by_seniority'][seniority] = {
                str(k): int(v) for k, v in exp_dist.items()
            }
        
        logger.info(f"✓ Generated career pathways for {len(pathways['seniority_progression'])} levels")
        
        return pathways
    
    def generate_skills_by_seniority(self, df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """
        Generate top skills for each seniority level.
        
        Returns: {seniority_level: {skill_category: count}}
        """
        logger.info("Generating skills by seniority level...")
        
        skills_by_seniority = {}
        
        for seniority in df['seniority_level'].unique():
            seniority_df = df[df['seniority_level'] == seniority]
            
            skill_counts = defaultdict(int)
            for summary in seniority_df['skill_summary'].dropna():
                if isinstance(summary, dict):
                    for category, count in summary.items():
                        if count is not None:
                            skill_counts[category] += count
            
            skills_by_seniority[seniority] = dict(
                sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
            )
        
        logger.info(f"✓ Generated skill rankings for {len(skills_by_seniority)} seniority levels")
        
        return skills_by_seniority
    
    def run_full_aggregation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute all aggregations"""
        logger.info("\nGenerating all analytics aggregations...")
        
        aggregations = {
            'skill_region_matrix': self.generate_skill_region_matrix(df),
            'salary_distribution': self.generate_salary_distribution(df),
            'remote_trends': self.generate_remote_trends(df),
            'career_pathways': self.generate_career_pathways(df),
            'skills_by_seniority': self.generate_skills_by_seniority(df),
        }
        
        logger.info("✓ All aggregations complete")
        
        return aggregations


def run_aggregations(df: pd.DataFrame) -> Dict[str, Any]:
    """Entry point for aggregations"""
    aggregator = AnalyticsAggregator()
    return aggregator.run_full_aggregation(df)
