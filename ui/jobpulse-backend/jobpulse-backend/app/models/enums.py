import enum


class JobStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    EXPIRED = "EXPIRED"
    FILLED = "FILLED"
    REMOVED = "REMOVED"
    UNKNOWN = "UNKNOWN"


class ResumeStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    EXTRACTING_TEXT = "EXTRACTING_TEXT"
    PREPROCESSING = "PREPROCESSING"
    NLP_ANALYSIS = "NLP_ANALYSIS"
    SKILL_ANALYSIS = "SKILL_ANALYSIS"
    GENERATING_RECOMMENDATIONS = "GENERATING_RECOMMENDATIONS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RecommendationType(str, enum.Enum):
    COURSE = "COURSE"
    INTERVIEW_PLATFORM = "INTERVIEW_PLATFORM"


class RecommendationPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SkillSource(str, enum.Enum):
    CV = "CV"
    MANUAL = "MANUAL"
