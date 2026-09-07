from collections import defaultdict
from datetime import date, datetime
from typing import List

from .models import (
    CandidateProfile,
    Job,
    JobRecommendation,
    RecommendationResult,
)

from .skills_matcher import SkillMatcher
from .resources import course_for_skill, interview_practice_for_skill

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
            matched, missing = self.skill_matcher.find_matches(candidate.skills, job.required_skills)
            preferred_matched, preferred_missing = self.skill_matcher.find_matches(candidate.skills, job.preferred_skills)
            score, components = self._hybrid_score(candidate, job)

            deadline = self._parse_deadline(job.application_deadline)
            days_to_deadline = (deadline - date.today()).days if deadline else None
            experience_gap = max(0, job.years_experience - candidate.years_experience)
            reasons = [f"Matches {len(matched)} of {len(self.skill_matcher.normalize_skills(job.required_skills))} required skills."]
            if job.preferred_skills:
                reasons.append(f"Matches {len(preferred_matched)} of {len(self.skill_matcher.normalize_skills(job.preferred_skills))} preferred skills.")
            if missing:
                reasons.append("Build: " + ", ".join(sorted(missing)[:4]) + ".")
            if experience_gap:
                reasons.append(f"Role asks for {experience_gap} more year(s) of experience.")
            if days_to_deadline is not None and 0 <= days_to_deadline <= 7:
                reasons.append(f"Deadline is in {days_to_deadline} day(s); prioritise application and interview practice.")

            recommendation = JobRecommendation(
                job=job,
                score=score,
                matched_skills=matched,
                missing_skills=missing,
                matched_preferred_skills=preferred_matched,
                missing_preferred_skills=preferred_missing,
                score_components=components,
                experience_gap_years=experience_gap,
                deadline=deadline,
                days_to_deadline=days_to_deadline,
                reasons=reasons,
            )   

            recommendations.append(recommendation)

        recommendations.sort(key=lambda r: (r.score, -(r.experience_gap_years), self._urgency(r)), reverse=True)

        return recommendations[:top_k]

    def _hybrid_score(self, candidate: CandidateProfile, job: Job) -> tuple[float, dict[str, float]]:
        """Score available signals only, so incomplete job records are neutral."""
        components: dict[str, float] = {}
        required = self.skill_matcher.normalize_skills(job.required_skills)
        if required:
            components["required_skills"] = self.skill_matcher.calculate_score(candidate.skills, required)
        preferred = self.skill_matcher.normalize_skills(job.preferred_skills)
        if preferred:
            components["preferred_skills"] = self.skill_matcher.calculate_score(candidate.skills, preferred)
        if job.years_experience > 0:
            components["experience"] = min(1.0, candidate.years_experience / job.years_experience)
        location_score = self._location_score(candidate, job)
        if location_score is not None:
            components["location_work_mode"] = location_score

        weights = {"required_skills": 0.65, "preferred_skills": 0.15, "experience": 0.15, "location_work_mode": 0.05}
        available_weight = sum(weights[key] for key in components)
        if not available_weight:
            return 0.0, components
        return sum(components[key] * weights[key] for key in components) / available_weight, components

    @staticmethod
    def _location_score(candidate: CandidateProfile, job: Job) -> float | None:
        locations = {value.strip().lower() for value in candidate.locations if value.strip()}
        modes = {value.strip().lower() for value in candidate.work_modes if value.strip()}
        job_location = job.country.strip().lower()
        job_mode = job.work_mode.strip().lower()
        signals = []
        if locations and job_location:
            signals.append(1.0 if job_location in locations else 0.0)
        if modes and job_mode:
            signals.append(1.0 if job_mode in modes else 0.0)
        return sum(signals) / len(signals) if signals else None

    def build_plan(self, candidate: CandidateProfile, jobs: List[Job], top_k: int = 10) -> RecommendationResult:
        """Rank jobs and select learning/practice actions from their shared gaps."""
        recommendations = self.recommend(candidate, jobs, top_k)
        gap_priority: dict[str, float] = defaultdict(float)
        for recommendation in recommendations:
            # Near deadlines should favour application prep; learning is still
            # shown, but it must not displace a role that is ready to apply for.
            urgency = 1.25 if recommendation.days_to_deadline is not None and 0 <= recommendation.days_to_deadline <= 7 else 1.0
            if recommendation.score > 0:
                for skill in recommendation.missing_skills:
                    gap_priority[skill] += recommendation.score * urgency
        courses = [course_for_skill(skill, priority, "Required by your best-matching jobs.") for skill, priority in gap_priority.items()]
        courses.sort(key=lambda item: (-item.priority, item.skill))

        interview_skills = self.skill_matcher.normalize_skills(candidate.skills)
        for recommendation in recommendations:
            if recommendation.days_to_deadline is not None and 0 <= recommendation.days_to_deadline <= 7:
                interview_skills.update(recommendation.matched_skills)
        practice = [interview_practice_for_skill(skill) for skill in sorted(interview_skills)[:5]]
        return RecommendationResult(candidate, recommendations, courses[:5], practice)

    @staticmethod
    def _parse_deadline(value: str) -> date | None:
        if not value or not isinstance(value, str):
            return None
        for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value.strip()[:10], pattern).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _urgency(recommendation: JobRecommendation) -> int:
        days = recommendation.days_to_deadline
        return 1 if days is not None and 0 <= days <= 7 else 0
