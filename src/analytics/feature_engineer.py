"""
Feature Engineering Pipeline for JobPulse Analytics

Transforms raw NLP-enriched data into ML-ready features:
1. Standardizes experience years (categorical + continuous)
2. Converts all salaries to USD equivalents
3. Engineers remote eligibility flag
4. Creates pan-African opportunity indicator
5. Normalizes categorical fields
"""

import logging
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Exchange rates (as of 2026-08-31)
# In production, these should come from a real-time API
EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 1.10,  # 1 EUR = 1.10 USD
    'GBP': 1.27,  # 1 GBP = 1.27 USD
    'ZAR': 0.055,  # 1 ZAR = 0.055 USD
    'NGN': 0.0021,  # 1 NGN = 0.0021 USD
    'GHS': 0.11,  # 1 GHS = 0.11 USD
    'KES': 0.0078,  # 1 KES = 0.0078 USD
    'EGP': 0.021,  # 1 EGP = 0.021 USD
    'MAD': 0.10,  # 1 MAD = 0.10 USD
    'TND': 0.33,  # 1 TND = 0.33 USD
    'UGX': 0.00027,  # 1 UGX = 0.00027 USD
}

# Experience level buckets
EXPERIENCE_BUCKETS = [
    (0, 1, '0-1 years'),
    (1, 3, '1-3 years'),
    (3, 5, '3-5 years'),
    (5, 10, '5-10 years'),
    (10, float('inf'), '10+ years'),
]

# Seniority level ordering for progression analysis
SENIORITY_ORDER = {
    'Intern': 0,
    'Entry Level': 1,
    'Mid-Level': 2,
    'Senior': 3,
    'Lead': 4,
    'Executive': 5,
}


class FeatureEngineer:
    """Engineer features for analytics and ML"""
    
    def __init__(self):
        self.exchange_rates = EXCHANGE_RATES
        self.experience_buckets = EXPERIENCE_BUCKETS
        self.seniority_order = SENIORITY_ORDER
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer all analytical features for the dataset.
        
        Args:
            df: DataFrame with NLP-enriched features from Stage 3
            
        Returns:
            DataFrame with additional engineered features
        """
        df = df.copy()
        
        logger.info("Engineering features...")
        
        # 1. Standardize salary to USD
        df['salary_min_usd'] = df.apply(
            lambda row: self._convert_salary_to_usd(
                row.get('salary_min'),
                row.get('salary_currency')
            ),
            axis=1
        )
        df['salary_max_usd'] = df.apply(
            lambda row: self._convert_salary_to_usd(
                row.get('salary_max'),
                row.get('salary_currency')
            ),
            axis=1
        )
        df['salary_mid_usd'] = (df['salary_min_usd'] + df['salary_max_usd']) / 2
        
        # 2. Engineer remote flag
        df['is_remote'] = df['work_mode'].fillna('').str.lower() == 'remote'
        
        # 3. Engineer pan-African flag
        df['is_pan_african'] = df.apply(
            lambda row: self._is_pan_african(
                row.get('work_mode'),
                row.get('job_description', '')
            ),
            axis=1
        )
        
        # 4. Standardize experience years to buckets
        df['experience_bucket'] = df['years_experience'].apply(
            self._bucket_experience
        )
        
        # 5. Normalize seniority level
        df['seniority_order'] = df['seniority_level'].map(
            self.seniority_order
        ).fillna(2)  # Default to Mid-Level (2)
        
        # 6. Flag high-salary positions (>$100k USD equivalent)
        df['is_high_salary'] = (df['salary_max_usd'] > 100000) | (df['salary_min_usd'] > 100000)
        
        # 7. Has explicit salary data
        df['has_salary_data'] = df['salary_min_usd'].notna() & (df['salary_min_usd'] > 0)
        
        # 8. Skill richness score (number of unique skill categories present)
        if 'skill_summary' in df.columns:
            df['skill_richness'] = df['skill_summary'].apply(
                lambda x: len(x) if isinstance(x, dict) else 0
            )
        else:
            df['skill_richness'] = 0
        
        # 9. Requires certification flag
        if 'certifications' in df.columns:
            df['requires_certification'] = df['certifications'].apply(
                lambda x: len(x) > 0 if isinstance(x, list) else False
            )
        else:
            df['requires_certification'] = False
        
        logger.info("✓ Feature engineering complete")
        
        return df
    
    def _convert_salary_to_usd(self, salary: Optional[float], 
                               currency: Optional[str]) -> Optional[float]:
        """Convert salary to USD equivalent"""
        if pd.isna(salary) or salary == 0:
            return None
        
        if not currency or currency not in self.exchange_rates:
            # Default to USD if currency unknown
            currency = 'USD'
        
        rate = self.exchange_rates.get(currency, 1.0)
        return salary * rate
    
    def _bucket_experience(self, years: int) -> str:
        """Bucket years of experience into categories"""
        if pd.isna(years) or years == 0:
            return 'Not specified'
        
        for min_yr, max_yr, label in self.experience_buckets:
            if min_yr <= years < max_yr:
                return label
        
        return '10+ years'
    
    def _is_pan_african(self, work_mode: Optional[str], 
                       description: Optional[str]) -> bool:
        """
        Determine if job is pan-African opportunity.
        
        Rules:
        - Explicitly remote jobs are pan-African eligible
        - Jobs mentioning "Africa" or "diaspora" are pan-African
        - Multiple countries in location suggest pan-African
        """
        if pd.isna(work_mode):
            work_mode = ''
        if pd.isna(description):
            description = ''
        
        # Check work mode
        if 'remote' in str(work_mode).lower():
            return True
        
        # Check description for Africa/diaspora keywords
        desc_lower = str(description).lower()
        pan_african_keywords = ['africa', 'diaspora', 'pan-african', 'panafrican']
        if any(keyword in desc_lower for keyword in pan_african_keywords):
            return True
        
        return False


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Entry point for feature engineering"""
    engineer = FeatureEngineer()
    return engineer.engineer_features(df)
