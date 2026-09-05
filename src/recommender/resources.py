"""Curated, provider-owned resources for common technical skill gaps.

URLs are deliberately stored as data so an API or UI can render them without
hard-coding career advice in a view.  Unknown skills still receive a useful
provider search link rather than being silently omitted.
"""

from urllib.parse import quote_plus

from .models import InterviewPracticeRecommendation, LearningRecommendation


COURSES = {
    "python": ("Python learning path", "Microsoft Learn", "https://learn.microsoft.com/training/paths/beginner-python/"),
    "sql": ("SQL courses", "Khan Academy", "https://www.khanacademy.org/computing/computer-programming/sql"),
    "aws": ("AWS Skill Builder", "AWS", "https://skillbuilder.aws/"),
    "azure": ("Azure fundamentals learning path", "Microsoft Learn", "https://learn.microsoft.com/training/paths/azure-fundamentals-describe-cloud-concepts/"),
    "gcp": ("Google Cloud Skills Boost", "Google Cloud", "https://www.cloudskillsboost.google/"),
    "docker": ("Docker getting started", "Docker", "https://docs.docker.com/get-started/"),
    "kubernetes": ("Kubernetes Basics", "Kubernetes", "https://kubernetes.io/docs/tutorials/kubernetes-basics/"),
    "react": ("Quick Start", "React", "https://react.dev/learn"),
    "django": ("Writing your first Django app", "Django", "https://docs.djangoproject.com/en/stable/intro/tutorial01/"),
    "fastapi": ("FastAPI Tutorial", "FastAPI", "https://fastapi.tiangolo.com/tutorial/"),
    "pandas": ("Getting started tutorials", "pandas", "https://pandas.pydata.org/docs/getting_started/intro_tutorials/"),
    "scikit-learn": ("Getting Started", "scikit-learn", "https://scikit-learn.org/stable/getting_started.html"),
    "tensorflow": ("Tutorials", "TensorFlow", "https://www.tensorflow.org/tutorials"),
    "pytorch": ("Learn the Basics", "PyTorch", "https://pytorch.org/tutorials/beginner/basics/intro.html"),
    "tableau": ("Free Training Videos", "Tableau", "https://www.tableau.com/learn/training"),
    "git": ("Learn Git Branching", "Learn Git Branching", "https://learngitbranching.js.org/"),
}


def course_for_skill(skill: str, priority: float, reason: str) -> LearningRecommendation:
    key = skill.lower()
    title, provider, url = COURSES.get(
        key,
        (f"Learn {skill}", "Coursera", f"https://www.coursera.org/search?query={quote_plus(skill)}"),
    )
    return LearningRecommendation(skill, title, provider, url, reason, priority)


def interview_practice_for_skill(skill: str) -> InterviewPracticeRecommendation:
    key = skill.lower()
    if key in {"python", "java", "javascript", "typescript", "c++", "c#", "go", "sql"}:
        return InterviewPracticeRecommendation(
            skill, f"Practice {skill} interview questions", "Pramp",
            "https://www.pramp.com/", "Schedule a timed peer mock interview and practise explaining your approach.",
        )
    if key in {"aws", "azure", "gcp", "docker", "kubernetes", "terraform"}:
        return InterviewPracticeRecommendation(
            skill, f"Prepare for {skill} technical interviews", "Interviewing.io",
            "https://interviewing.io/", "Use a technical mock interview, then review the systems and trade-offs behind your answer.",
        )
    return InterviewPracticeRecommendation(
        skill, f"Practise explaining {skill}", "Interviewing.io",
        "https://interviewing.io/", "Book a mock interview and prepare one concrete project example using this skill.",
    )
