from src.recommender.models import CandidateProfile, Job
from src.recommender.job_recommender import JobRecommender

candidate = CandidateProfile(
    name="Francis",
    skills = {
        "python",
        "SQL",
        "Pandas",
        "Scikit-learn",
        "Git"
    }
)

jobs = [
    Job(
        job_id="001",
        title="Junior Data Scientist",
        company="Company A",
        skills={
            "Python",
            "SQL",
            "Pandas",
            "Scikit-learn",
            "Git",
            "AWS"
        }
    ),

    Job(
        job_id="002",
        title="Machine Learning Engineer",
        company="Company B",
        skills={
            "Python",
            "TensorFlow",
            "Docker",
            "AWS",
            "Kubernetes"
        }
    ),

    Job(
        job_id="003",
        title="Data Analyst",
        company="Company C",
        skills={
            "Python",
            "SQL",
            "Pandas",
            "Tableau"
        }
    )
]

recommender = JobRecommender()

recommendations = recommender.recommend(
    candidate=candidate,
    jobs=jobs,
    top_k=3
)

for recommendation in recommendations:
    print("=" * 50)
    print(f"{recommendation.job.title} at {recommendation.job.company}")

    print(f"Match: {recommendation.match_percentage}%")
    print(f"Matched: {recommendation.matched_skills}")
    print(f"Missing: {recommendation.missing_skills}")