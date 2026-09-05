from dataclasses import dataclass, field
from datetime import date
from typing import List, Set

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
    preferred_roles: List[str] = field(default_factory=list)
    locations: Set[str] = field(default_factory=set)
    work_modes: Set[str] = field(default_factory=set)

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
    application_deadline: str = ""
    vacancy_url: str = ""
    preferred_skills: Set[str] = field(default_factory=set)

    @property
    def required_skills(self) -> Set[str]:
        """`skills` remains the backwards-compatible required skill field."""
        return self.skills


@dataclass
class JobRecommendation:
    """
    Represents a scored job recommendation
    """

    job: Job
    score: float
    matched_skills: Set[str] = field(default_factory=set)
    missing_skills: Set[str] = field(default_factory=set)
    matched_preferred_skills: Set[str] = field(default_factory=set)
    missing_preferred_skills: Set[str] = field(default_factory=set)
    score_components: dict[str, float] = field(default_factory=dict)
    experience_gap_years: int = 0
    deadline: date | None = None
    days_to_deadline: int | None = None
    reasons: List[str] = field(default_factory=list)

    @property
    def match_percentage(self) -> float:
        """Return the match score as a percentage"""
        return round(self.score * 100, 2)


@dataclass(frozen=True)
class LearningRecommendation:
    """A learning resource selected for a high-impact missing skill."""

    skill: str
    title: str
    provider: str
    url: str
    reason: str
    priority: float


@dataclass(frozen=True)
class InterviewPracticeRecommendation:
    """A focused interview-practice action for a candidate skill."""

    skill: str
    title: str
    provider: str
    url: str
    reason: str


@dataclass
class RecommendationResult:
    """Complete, presentation-ready output for one candidate."""

    candidate: CandidateProfile
    jobs: List[JobRecommendation]
    courses: List[LearningRecommendation]
    interview_practice: List[InterviewPracticeRecommendation]
