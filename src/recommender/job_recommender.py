from typing import List

from src.recommender.models import (
    CandidateProfile,
    Job,
    JobRecommendation
)

from src.recommender.skills_matcher import SkillMatcher

class JobRecommender:
    """
    Recommends jobs based on candidate skill compatibility
    """

    def __init__(self, skill_matcher: SkillMatcher | None = None):
        self.skill_matcher = skill_matcher or SkillMatcher()

    def recommend(
            self, candidate:CandidateProfile,
            jobs: List[Job], top_k: int = 10
    ) -> List[JobRecommendation]:
        """
        Ranks jobs according to candidate skill compatibility
        """

        recommendations = []

        for job in jobs:
            matched, missing = self. skill_matcher.find_matches(
                candidate.skills, job.skills
            )

            score = self.skill_matcher.calculate_score(candidate.skills, job.skills)

            recommendation = JobRecommendation(
                job=job,
                score=score,
                matched_skills=matched,
                missing_skills=missing
            )   

            recommendations.append(recommendation)

        recommendations.sort(
            key=lambda recommendation: recommendation.score, reverse=True
        )

        return recommendations[:top_k]