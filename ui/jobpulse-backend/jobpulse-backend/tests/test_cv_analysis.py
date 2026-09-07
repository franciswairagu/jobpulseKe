from app.ml.adapters.cv_analyzer import CVExtraction
from app.ml.preprocessing.skill_extractor import SkillExtractor
from app.services.cv_service import compute_cv_score, derive_strengths_weaknesses


def test_extract_skills_finds_known_terms_around_punctuation():
    extractor = SkillExtractor()
    text = "Skilled in Python, Django, PostgreSQL, and AWS. Also know React.js basics."
    found = extractor.extract_skills(text)
    all_skills = {s for group in found.values() for s in group}
    assert "python" in all_skills
    assert "django" in all_skills
    assert "postgresql" in all_skills
    assert "aws" in all_skills


def test_extract_skills_no_false_positive_on_empty_text():
    extractor = SkillExtractor()
    assert all(len(v) == 0 for v in extractor.extract_skills("").values())


def test_extract_years_experience_recognizes_common_phrasing():
    extractor = SkillExtractor()
    assert extractor.extract_years_experience("I have 5 years of experience in backend development.") == 5
    assert extractor.extract_years_experience("3+ years experience required") == 3
    assert extractor.extract_years_experience("No experience mentioned here") == 0


def test_extract_education_and_certifications():
    extractor = SkillExtractor()
    text = "Bachelor of Science in Computer Science. AWS Certified Solutions Architect."
    assert "Bachelor's degree" in extractor.extract_education(text)
    assert "aws certified" in extractor.extract_certifications(text)


def test_cv_score_is_bounded_0_to_100():
    rich = CVExtraction(
        skills_found=["python"] * 15,
        years_experience=10,
        education=["Bachelor's degree"],
        certifications=["aws certified", "pmp", "ccna"],
        seniority_level="Senior",
        tech_category=None,
        tech_category_confidence=None,
        classifier_available=False,
        classifier_model_version=None,
    )
    empty = CVExtraction(
        skills_found=[], years_experience=0, education=[], certifications=[],
        seniority_level=None, tech_category=None, tech_category_confidence=None,
        classifier_available=False, classifier_model_version=None,
    )
    assert compute_cv_score(rich) == 100
    assert compute_cv_score(empty) == 0


def test_derive_strengths_and_weaknesses_reflect_extraction():
    weak = CVExtraction(
        skills_found=["python"], years_experience=0, education=[], certifications=[],
        seniority_level=None, tech_category=None, tech_category_confidence=None,
        classifier_available=False, classifier_model_version=None,
    )
    strengths, weaknesses = derive_strengths_weaknesses(weak)
    assert any("experience" in w.lower() for w in weaknesses)
    assert any("certification" in w.lower() for w in weaknesses)
