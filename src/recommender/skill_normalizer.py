"""One canonical representation for skills from CVs and job records."""

from typing import Iterable, Set


SKILL_ALIASES = {
    "golang": "go", "csharp": "c#", "nextjs": "next.js", "aspnet": "asp.net",
    "postgres": "postgresql", "amazon web services": "aws", "google cloud": "gcp",
    "microsoft azure": "azure", "sklearn": "scikit-learn", "k8s": "kubernetes",
    "cicd": "ci/cd", "hugging face": "huggingface", "powerbi": "power bi",
}


class SkillNormalizer:
    """Normalise spelling, casing, whitespace, and known skill aliases."""

    def normalize(self, skill: str) -> str:
        if not isinstance(skill, str):
            return ""
        value = " ".join(skill.lower().strip().split())
        return SKILL_ALIASES.get(value, value)

    def normalize_many(self, skills: Iterable[str] | None) -> Set[str]:
        return {normalised for skill in skills or () if (normalised := self.normalize(skill))}
