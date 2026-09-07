"""Job Recommender evaluation — ranking accuracy and score analysis."""

import logging
from typing import Any, Dict, List

from src.recommender.models import CandidateProfile, Job
from src.recommender.job_recommender import JobRecommender

logger = logging.getLogger(__name__)

SYNTHETIC_CANDIDATES = [
    CandidateProfile(
        name="Python Backend Dev",
        skills={"python", "django", "fastapi", "postgresql", "redis", "docker"},
        years_experience=5,
        locations={"kenya", "nigeria"},
        work_modes={"remote", "hybrid"},
    ),
    CandidateProfile(
        name="Frontend React Dev",
        skills={"javascript", "typescript", "react", "css", "html", "git"},
        years_experience=3,
        locations={"south africa"},
        work_modes={"remote"},
    ),
    CandidateProfile(
        name="DevOps Engineer",
        skills={"docker", "kubernetes", "terraform", "aws", "ci/cd", "python"},
        years_experience=7,
        locations={"kenya"},
        work_modes={"remote", "on-site"},
    ),
    CandidateProfile(
        name="Data Scientist",
        skills={"python", "sql", "tensorflow", "pytorch", "pandas", "scikit-learn"},
        years_experience=4,
        locations={"nigeria", "ghana"},
        work_modes={"remote"},
    ),
    CandidateProfile(
        name="Junior Full Stack",
        skills={"javascript", "react", "node.js", "html", "css"},
        years_experience=1,
        locations={"kenya"},
        work_modes={"on-site", "hybrid"},
    ),
]

SYNTHETIC_JOBS = [
    Job(
        job_id="j1",
        title="Senior Python Developer",
        company="TechCo",
        description="Build APIs with Django and FastAPI",
        skills={"python", "django", "fastapi", "postgresql", "redis"},
        years_experience=5,
        country="kenya",
        work_mode="remote",
    ),
    Job(
        job_id="j2",
        title="React Frontend Developer",
        company="StartupInc",
        description="Build modern UIs with React",
        skills={"javascript", "typescript", "react", "css"},
        years_experience=3,
        country="south africa",
        work_mode="remote",
    ),
    Job(
        job_id="j3",
        title="DevOps Lead",
        company="CloudFirst",
        description="Manage infrastructure with K8s and Terraform",
        skills={"docker", "kubernetes", "terraform", "aws", "ci/cd"},
        years_experience=6,
        country="kenya",
        work_mode="hybrid",
    ),
    Job(
        job_id="j4",
        title="ML Engineer",
        company="DataCorp",
        description="Build ML pipelines with TensorFlow",
        skills={"python", "tensorflow", "pytorch", "sql", "docker"},
        years_experience=4,
        country="nigeria",
        work_mode="remote",
    ),
    Job(
        job_id="j5",
        title="Junior JavaScript Developer",
        company="WebAgency",
        description="Build websites with React and JavaScript",
        skills={"javascript", "react", "html", "css"},
        years_experience=1,
        country="kenya",
        work_mode="on-site",
    ),
    Job(
        job_id="j6",
        title="Backend Go Developer",
        company="ScaleUp",
        description="Microservices in Go and gRPC",
        skills={"go", "grpc", "postgresql", "docker"},
        years_experience=4,
        country="ghana",
        work_mode="remote",
    ),
    Job(
        job_id="j7",
        title="Data Analyst",
        company="InsightCo",
        description="Analyze data with SQL and Python",
        skills={"sql", "python", "excel", "tableau"},
        years_experience=2,
        country="nigeria",
        work_mode="hybrid",
    ),
    Job(
        job_id="j8",
        title="Senior Cloud Architect",
        company="EnterpriseLtd",
        description="Design AWS and Azure cloud infrastructure",
        skills={"aws", "azure", "terraform", "docker", "kubernetes"},
        years_experience=10,
        country="south africa",
        work_mode="remote",
    ),
]

# For each candidate, the job_id that SHOULD rank highest
EXPECTED_BEST_JOB = {
    "Python Backend Dev": "j1",
    "Frontend React Dev": "j2",
    "DevOps Engineer": "j3",
    "Data Scientist": "j4",
    "Junior Full Stack": "j5",
}


def evaluate_job_recommender() -> Dict[str, Any]:
    """Evaluate the job recommender with synthetic candidate-job pairs.

    Checks:
      - Top-1 accuracy: does the expected best job rank #1?
      - Mean rank of the expected best job across candidates
      - Score distribution analysis
      - Component coverage (do all score components fire?)
    """
    recommender = JobRecommender()
    per_candidate = []
    top1_correct = 0
    total_rank = 0
    total_candidates = 0
    component_counts = {"required_skills": 0, "preferred_skills": 0, "experience": 0, "location_work_mode": 0}

    for candidate in SYNTHETIC_CANDIDATES:
        recs = recommender.recommend(candidate, SYNTHETIC_JOBS, top_k=len(SYNTHETIC_JOBS))
        expected_job_id = EXPECTED_BEST_JOB.get(candidate.name)

        # Find rank of expected best job
        expected_rank = None
        for i, rec in enumerate(recs):
            if rec.job.job_id == expected_job_id:
                expected_rank = i + 1
                break

        if expected_rank == 1:
            top1_correct += 1
        if expected_rank:
            total_rank += expected_rank
        total_candidates += 1

        # Track component usage
        for rec in recs[:3]:
            for comp in rec.score_components:
                if comp in component_counts:
                    component_counts[comp] += 1

        per_candidate.append({
            "candidate": candidate.name,
            "expected_best_job": expected_job_id,
            "actual_rank_of_best": expected_rank,
            "top3_jobs": [
                {"job_id": r.job.job_id, "title": r.job.title, "score": round(r.score, 3)}
                for r in recs[:3]
            ],
            "top1_score": round(recs[0].score, 3) if recs else 0,
            "score_range": (
                round(recs[-1].score, 3) if recs else 0,
                round(recs[0].score, 3) if recs else 0,
            ),
        })

    return {
        "model": "job_recommender",
        "n_candidates": total_candidates,
        "n_jobs": len(SYNTHETIC_JOBS),
        "top1_accuracy": round(top1_correct / total_candidates, 3) if total_candidates else 0,
        "mean_rank_of_best": round(total_rank / total_candidates, 3) if total_candidates else 0,
        "top1_correct": top1_correct,
        "component_coverage": component_counts,
        "per_candidate": per_candidate,
    }
