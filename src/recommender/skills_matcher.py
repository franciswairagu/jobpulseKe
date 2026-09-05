from typing import Iterable, Set, Tuple

from .skill_normalizer import SkillNormalizer

class SkillMatcher:
    """
    Calculates how well a candidate's skills match
    the skills required by a job
    """

    def __init__(self, required_skill_weight: float = 1.0, normalizer: SkillNormalizer | None = None):
        self.required_skill_weight = required_skill_weight
        self.normalizer = normalizer or SkillNormalizer()

    def normalize_skills(self, skills: Iterable[str] | None) -> Set[str]:
        """
        Normalize skill names for reliable comparison
        """
        return self.normalizer.normalize_many(skills)

    def find_matches(
            self,
            candidate_skills: Set[str],
            job_skills: Set[str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Find skills the candidate has and skills they are missing
        """

        candidate_skills = self.normalize_skills(candidate_skills)
        job_skills = self.normalize_skills(job_skills)

        matched = candidate_skills.intersection(job_skills)
        missing = job_skills.difference(candidate_skills)

        return matched, missing

    def calculate_score(self, candidate_skills: Set[str], job_skills: Set[str]) -> float:
        """
        Calculate the proportion of required job skills
        possessed by the candidate
        """

        candidate_skills = self.normalize_skills(candidate_skills)
        job_skills = self.normalize_skills(job_skills)

        if not job_skills:
            return 0.0

        matched = candidate_skills.intersection(job_skills)

        return len(matched) / len(job_skills)
