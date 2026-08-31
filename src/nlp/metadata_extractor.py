"""
Metadata Extraction Module

Extracts structured metadata from job postings:
- Years of experience required
- Education level requirements
- Professional certifications
- Employment type
- Work mode (remote, on-site, hybrid)
- Seniority level inference
"""

import re
import logging
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class SeniorityLevel(Enum):
    """Career level classification"""
    INTERN = "Intern"
    ENTRY = "Entry Level"
    MID = "Mid-Level"
    SENIOR = "Senior"
    LEAD = "Lead"
    EXECUTIVE = "Executive"


class MetadataExtractor:
    """Extract structured metadata from job descriptions and titles"""
    
    # Seniority level keywords
    SENIORITY_KEYWORDS = {
        'intern': SeniorityLevel.INTERN,
        'internship': SeniorityLevel.INTERN,
        'graduate': SeniorityLevel.ENTRY,
        'entry level': SeniorityLevel.ENTRY,
        'junior': SeniorityLevel.ENTRY,
        'mid-level': SeniorityLevel.MID,
        'mid level': SeniorityLevel.MID,
        'intermediate': SeniorityLevel.MID,
        'senior': SeniorityLevel.SENIOR,
        'principal': SeniorityLevel.SENIOR,
        'lead': SeniorityLevel.LEAD,
        'manager': SeniorityLevel.LEAD,
        'director': SeniorityLevel.EXECUTIVE,
        'vp': SeniorityLevel.EXECUTIVE,
        'vice president': SeniorityLevel.EXECUTIVE,
        'executive': SeniorityLevel.EXECUTIVE,
        'c-level': SeniorityLevel.EXECUTIVE,
        'cto': SeniorityLevel.EXECUTIVE,
        'cfo': SeniorityLevel.EXECUTIVE,
        'ceo': SeniorityLevel.EXECUTIVE,
    }
    
    # Employment type keywords
    EMPLOYMENT_KEYWORDS = {
        'full-time': 'Full-Time',
        'full time': 'Full-Time',
        'fulltime': 'Full-Time',
        'part-time': 'Part-Time',
        'part time': 'Part-Time',
        'contract': 'Contract',
        'temporary': 'Temporary',
        'freelance': 'Freelance',
        'internship': 'Internship',
    }
    
    # Work mode keywords
    WORKMODE_KEYWORDS = {
        'remote': 'Remote',
        'fully remote': 'Remote',
        'work from home': 'Remote',
        'hybrid': 'Hybrid',
        'on-site': 'On-Site',
        'on site': 'On-Site',
        'onsite': 'On-Site',
        'in-office': 'On-Site',
        'in office': 'On-Site',
    }
    
    def __init__(self):
        pass
    
    def extract_seniority_level(self, title: str, description: str = "") -> SeniorityLevel:
        """
        Infer seniority level from job title and description.
        
        Priority: title keywords > description keywords > default to MID
        """
        combined_text = f"{title} {description}".lower()
        
        # Check title first (more reliable)
        title_lower = title.lower() if title else ""
        for keyword, level in self.SENIORITY_KEYWORDS.items():
            if keyword in title_lower:
                return level
        
        # Check description
        for keyword, level in self.SENIORITY_KEYWORDS.items():
            if keyword in combined_text:
                return level
        
        # Default to Mid-Level for unknown roles
        return SeniorityLevel.MID
    
    def extract_employment_type(self, text: str) -> Optional[str]:
        """Extract employment type from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        for keyword, emp_type in self.EMPLOYMENT_KEYWORDS.items():
            if keyword in text_lower:
                return emp_type
        
        return None
    
    def extract_work_mode(self, text: str) -> Optional[str]:
        """Extract work mode (remote/hybrid/on-site) from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Check for remote first (highest priority)
        for keyword in ['fully remote', 'work from home', 'remote']:
            if keyword in text_lower:
                return 'Remote'
        
        # Check for hybrid
        if 'hybrid' in text_lower:
            return 'Hybrid'
        
        # Check for on-site
        for keyword in ['on-site', 'on site', 'onsite', 'in-office', 'in office']:
            if keyword in text_lower:
                return 'On-Site'
        
        return None
    
    def extract_salary_range(self, text: str) -> Dict[str, Optional[float]]:
        """
        Extract salary range from text.
        
        Returns: {'min': float, 'max': float, 'currency': str}
        """
        if not text:
            return {'min': None, 'max': None, 'currency': None}
        
        # Patterns for salary ranges
        salary_patterns = [
            # $50,000 - $70,000
            r'\$?([\d,]+(?:\.\d{2})?)\s*-\s*\$?([\d,]+(?:\.\d{2})?)',
            # $50k - $70k
            r'\$?([\d.]+)k?\s*-\s*\$?([\d.]+)k?',
            # from $50,000 to $70,000
            r'(?:from|starting at)?\s*\$?([\d,]+(?:\.\d{2})?)',
        ]
        
        result = {'min': None, 'max': None, 'currency': None}
        
        text_lower = text.lower()
        
        # Detect currency
        if '$' in text or 'usd' in text_lower or 'dollar' in text_lower:
            result['currency'] = 'USD'
        elif '€' in text or 'eur' in text_lower:
            result['currency'] = 'EUR'
        elif '£' in text or 'gbp' in text_lower:
            result['currency'] = 'GBP'
        elif 'zar' in text_lower or 'rand' in text_lower:
            result['currency'] = 'ZAR'
        elif 'ngn' in text_lower or 'naira' in text_lower:
            result['currency'] = 'NGN'
        else:
            result['currency'] = 'USD'  # Default to USD
        
        # Extract salary amounts
        for pattern in salary_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    if len(match.groups()) == 2:
                        min_val = float(match.group(1).replace(',', '').replace('k', '000'))
                        max_val = float(match.group(2).replace(',', '').replace('k', '000'))
                        result['min'] = min(result['min'] or float('inf'), min_val)
                        result['max'] = max(result['max'] or 0, max_val)
                    elif len(match.groups()) == 1:
                        val = float(match.group(1).replace(',', '').replace('k', '000'))
                        if result['min'] is None:
                            result['min'] = val
                        else:
                            result['max'] = val
                except (ValueError, AttributeError):
                    pass
        
        return result
    
    def infer_seniority_from_experience(self, years: int) -> SeniorityLevel:
        """Infer seniority level from years of experience"""
        if years == 0:
            return SeniorityLevel.INTERN
        elif years < 2:
            return SeniorityLevel.ENTRY
        elif years < 5:
            return SeniorityLevel.MID
        elif years < 10:
            return SeniorityLevel.SENIOR
        elif years < 15:
            return SeniorityLevel.LEAD
        else:
            return SeniorityLevel.EXECUTIVE
    
    def extract_key_requirements(self, text: str) -> List[str]:
        """Extract key requirements from job description"""
        if not text:
            return []
        
        requirements = []
        text_lower = text.lower()
        
        # Common required patterns
        requirement_triggers = [
            r'must have\s+([^.!?]+)',
            r'requires?\s+([^.!?]+)',
            r'need(?:s)?\s+([^.!?]+)',
            r'essential\s+([^.!?]+)',
            r'key\s+qualifications?\s*:?\s*([^.!?]+)',
        ]
        
        for pattern in requirement_triggers:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                req = match.group(1).strip()
                if len(req) > 10 and len(req) < 200:
                    requirements.append(req)
        
        return list(set(requirements[:10]))  # Return top 10 unique
    
    def is_remote_eligible(self, text: str, country: str = "") -> bool:
        """Check if job is remote or remote-eligible"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for explicit remote keywords
        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed']
        for keyword in remote_keywords:
            if keyword in text_lower:
                return True
        
        # African diaspora companies often accept remote applications
        # even if position is on-site
        remote_company_keywords = ['diaspora', 'global', 'international']
        for keyword in remote_company_keywords:
            if keyword in text_lower:
                return True
        
        return False


def get_metadata_extractor() -> MetadataExtractor:
    """Singleton instance getter"""
    return MetadataExtractor()
