from __future__ import annotations

import uuid

from sqlalchemy.orm import Session, joinedload

from app.ml.adapters.recommendation import RecommendationEngine
from app.models.enums import JobStatus, RecommendationPriority, RecommendationType
from app.models.job import Job as JobModel
from app.models.recommendation import ModelPrediction, Recommendation
from app.models.resume import ResumeAnalysis
from app.models.job import JobSkill
from app.models.skill import UserSkill
from app.models.user import Profile, User
from app.recommender import CandidateProfile
from app.recommender.models import Job as RecommenderJob


def build_candidate_profile(db: Session, user: User, resume_analysis: ResumeAnalysis | None) -> CandidateProfile:
    profile: Profile | None = user.profile
    user_skills = db.query(UserSkill).options(joinedload(UserSkill.skill)).filter(UserSkill.user_id == user.id).all()
    skill_names = {link.skill.name for link in user_skills if link.skill}

    years_experience = 0
    education: list[str] = []
    certifications: list[str] = []
    if resume_analysis:
        years_experience = resume_analysis.years_experience
        education = resume_analysis.education
        certifications = resume_analysis.certifications
    if profile and profile.years_experience:
        years_experience = max(years_experience, profile.years_experience)

    return CandidateProfile(
        name=profile.name if profile and profile.name else "",
        skills=skill_names,
        years_experience=years_experience,
        education=education,
        certifications=certifications,
        preferred_roles=[profile.career_interest] if profile and profile.career_interest else [],
        locations={profile.country} if profile and profile.country else set(),
        work_modes={profile.preferred_work_mode} if profile and profile.preferred_work_mode else set(),
    )


def db_jobs_to_recommender_jobs(db: Session, limit: int = 500) -> list[RecommenderJob]:
    jobs = (
        db.query(JobModel)
        .options(joinedload(JobModel.skill_links).joinedload(JobSkill.skill))
        .filter(JobModel.status == JobStatus.AVAILABLE)
        .limit(limit)
        .all()
    )
    result = []
    for job in jobs:
        required = {link.skill.name for link in job.skill_links if link.skill and not link.is_preferred}
        preferred = {link.skill.name for link in job.skill_links if link.skill and link.is_preferred}
        result.append(RecommenderJob(
            job_id=str(job.id),
            title=job.title,
            company=job.company or "",
            description=job.description or "",
            skills=required,
            years_experience=0,
            country=job.country or "",
            work_mode=job.work_mode or "",
            employment_type=job.employment_type or "",
            application_deadline=job.expires_at.isoformat() if job.expires_at else "",
            vacancy_url=job.source_url or "",
            preferred_skills=preferred,
        ))
    return result


def generate_recommendations(db: Session, user: User, resume_analysis: ResumeAnalysis | None, top_k: int = 10) -> dict:
    engine = RecommendationEngine()
    candidate = build_candidate_profile(db, user, resume_analysis)
    jobs = db_jobs_to_recommender_jobs(db)
    plan = engine.recommend(candidate, jobs, top_k=top_k)

    db.query(Recommendation).filter(Recommendation.user_id == user.id).delete()

    persisted: list[Recommendation] = []
    for course in plan.courses:
        priority = RecommendationPriority.HIGH if course.priority >= 0.6 else (
            RecommendationPriority.MEDIUM if course.priority >= 0.3 else RecommendationPriority.LOW
        )
        rec = Recommendation(
            user_id=user.id,
            resume_analysis_id=resume_analysis.id if resume_analysis else None,
            type=RecommendationType.COURSE,
            title=course.title,
            provider=course.provider,
            url=course.url,
            reason=course.reason,
            related_skill=course.skill,
            priority=priority,
            score=round(course.priority, 3),
        )
        db.add(rec)
        persisted.append(rec)

    for practice in plan.interview_practice:
        rec = Recommendation(
            user_id=user.id,
            resume_analysis_id=resume_analysis.id if resume_analysis else None,
            type=RecommendationType.INTERVIEW_PLATFORM,
            title=practice.title,
            provider=practice.provider,
            url=practice.url,
            reason=practice.reason,
            related_skill=practice.skill,
            priority=RecommendationPriority.MEDIUM,
            score=None,
        )
        db.add(rec)
        persisted.append(rec)

    db.add(ModelPrediction(
        user_id=user.id,
        model_name=engine.MODEL_NAME,
        model_version=engine.MODEL_VERSION,
        prediction_type="job_recommendations",
        input_reference=str(resume_analysis.id) if resume_analysis else None,
        output={
            "top_job_ids": [rec.job.job_id for rec in plan.jobs[:10]],
            "top_job_scores": [rec.match_percentage for rec in plan.jobs[:10]],
        },
    ))

    db.commit()

    return {
        "job_recommendations": plan.jobs,
        "courses": [r for r in persisted if r.type == RecommendationType.COURSE],
        "interview_platforms": [r for r in persisted if r.type == RecommendationType.INTERVIEW_PLATFORM],
    }
