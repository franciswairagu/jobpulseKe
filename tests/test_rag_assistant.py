import pandas as pd

from src.rag.assistant import _compose_answer


def test_grounded_answer_names_only_retrieved_job_data():
    results = pd.DataFrame([{
        "job_title": "Python Developer", "company": "JobPulse", "location": "Nairobi",
        "country": "Kenya", "work_mode": "Remote", "skills": ["python", "django"],
    }])

    answer = _compose_answer("remote python jobs", results)

    assert "Python Developer at JobPulse" in answer
    assert "Nairobi; Remote" in answer
    assert "python, django" in answer
