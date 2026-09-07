from datetime import date, timedelta

from src.cv.skill_extractor import profile_from_text
from src.recommender import JobRecommender, jobs_from_records
from src.recommender.models import CandidateProfile, Job
from src.recommender.skills_matcher import SkillMatcher


def test_cv_profile_uses_shared_skill_taxonomy_and_aliases():
    profile = profile_from_text("JANE DOE\nPython, SQL, sklearn, Docker\n3 years of experience")

    assert profile.name == "Jane Doe"
    assert {"python", "sql", "scikit-learn", "docker"} <= profile.skills
    assert profile.years_experience == 3


def test_job_record_adapter_extracts_skills_from_jobpulse_schema():
    jobs = jobs_from_records([{
        "job_id": "42", "job_title": "Data Engineer", "company": "JobPulse",
        "job_description": "Use Python, PostgreSQL, Docker and AWS.",
        "application_deadline": "2030-06-20",
    }])

    assert jobs[0].job_id == "42"
    assert {"python", "postgresql", "docker", "aws"} <= jobs[0].skills


def test_plan_prioritises_shared_gaps_and_deadline_practice():
    deadline = (date.today() + timedelta(days=2)).isoformat()
    candidate = CandidateProfile(name="Amina", skills={"Python", "SQL"}, years_experience=1)
    jobs = [
        Job("1", "Data analyst", skills={"python", "sql", "tableau"}, application_deadline=deadline),
        Job("2", "ML engineer", skills={"python", "tensorflow", "kubernetes"}),
    ]

    plan = JobRecommender().build_plan(candidate, jobs)

    assert plan.jobs[0].job.job_id == "1"
    assert plan.jobs[0].days_to_deadline == 2
    assert any(course.skill == "tableau" for course in plan.courses)
    assert {item.skill for item in plan.interview_practice} >= {"python", "sql"}


def test_skill_matcher_handles_aliases_and_symbol_skills():
    matched, missing = SkillMatcher().find_matches({"C++", "sklearn"}, {"c++", "scikit-learn", "aws"})

    assert matched == {"c++", "scikit-learn"}
    assert missing == {"aws"}


def test_hybrid_score_weights_required_preferred_experience_and_work_preferences():
    candidate = CandidateProfile(
        skills={"python", "aws"}, years_experience=2,
        locations={"Kenya"}, work_modes={"Remote"},
    )
    jobs = [
        Job("better", "Backend engineer", skills={"python"}, preferred_skills={"aws"},
            years_experience=2, country="Kenya", work_mode="Remote"),
        Job("worse", "Backend engineer", skills={"python"}, preferred_skills={"aws"},
            years_experience=5, country="Uganda", work_mode="On-site"),
    ]

    recommendations = JobRecommender().recommend(candidate, jobs)

    assert recommendations[0].job.job_id == "better"
    assert recommendations[0].score == 1.0
    assert recommendations[0].score_components == {
        "required_skills": 1.0, "preferred_skills": 1.0,
        "experience": 1.0, "location_work_mode": 1.0,
    }


def test_loader_separates_optional_skills_from_required_skills():
    job = jobs_from_records([{
        "job_id": "43", "job_title": "Platform Engineer",
        "job_description": "Python and Docker are required. Kubernetes is nice to have.",
    }])[0]

    assert {"python", "docker"} <= job.required_skills
    assert job.preferred_skills == {"kubernetes"}
