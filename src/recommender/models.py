from dataclasses import dataclass, field
from typing import List, Set, Optional

@dataclass
class CandidateProfile:
    """
    Represents the skills and background of a job candidate
    """

    name:str = ""
    skills: Set[str] = field(default_factory=set)
    years_experience: int = 0
    education: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    def add_skill(self, skill:str) -> None:
        """Add a normalized skill to the candidate profile"""
        if skill:
            self.skills.add(skill.lower().strip())

    def has_skill(self, skill: str) -> bool:
        """Check whether the candidate possesses a skill"""
        return skill.lower().strip() in self.skills


@dataclass
class Job:
    """
    Represents a job Posting
    """

    job_id: str
    title: str
    company: str = ""
    description: str = ""
    skills: Set[str] = field(default_factory=set)
    years_experience: int = 0
    country: str = ""
    work_mode: str = ""
    employment_type: str = ""


@dataclass
class JobRecommendation:
    """
    Represents a scored job recommendation
    """

    job: Job
    score: float
    matched_skills: Set[str] = field(default_factory=set)
    missing_skills: Set[str] = field(default_factory=set)

    @property
    def match_percentage(self) -> float:
        """Return the match score as a percentage"""
        return round(self.score * 100, 2)
    