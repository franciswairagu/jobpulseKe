import re
import hashlib
import requests
import pandas as pd

from datetime import datetime, timezone


API_URL = "https://jobicy.com/api/v2/remote-jobs"

TECH_INDUSTRIES = {
    "software",
    "software development",
    "devops",
    "infrastructure",
    "engineering",
    "data science",
    "data analytics",
    "information technology",
    "technology",
    "product",
}


def clean_text(text):
    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text).replace("\xa0", " ")
    ).strip()


def generate_job_id(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:16]


def classify_category(
    title,
    industries
):
    text = title.lower()

    industries_text = " ".join(
        str(x).lower()
        for x in industries
    )

    combined = f"{text} {industries_text}"

    if any(
        x in combined
        for x in [
            "data scientist",
            "data analyst",
            "data engineer",
            "machine learning",
            "artificial intelligence",
            "ai engineer",
            "data science",
        ]
    ):
        return "Data & AI"

    if any(
        x in combined
        for x in [
            "cybersecurity",
            "cyber security",
            "security engineer",
            "security analyst",
        ]
    ):
        return "Cybersecurity"

    if any(
        x in combined
        for x in [
            "devops",
            "cloud engineer",
            "cloud architect",
            "site reliability",
            "infrastructure",
        ]
    ):
        return "Cloud & DevOps"

    if any(
        x in combined
        for x in [
            "network engineer",
            "network administrator",
            "network",
        ]
    ):
        return "Networking"

    if any(
        x in combined
        for x in [
            "qa engineer",
            "qa analyst",
            "software tester",
            "quality assurance",
        ]
    ):
        return "QA & Testing"

    if any(
        x in combined
        for x in [
            "product manager",
            "product owner",
            "ux designer",
            "ui designer",
        ]
    ):
        return "Product & UX"

    return "Software & IT"


def is_tech_job(
    title,
    industries
):

    text = (
        f"{title} "
        f"{' '.join(map(str, industries))}"
    ).lower()

    tech_terms = [
        "software",
        "developer",
        "engineer",
        "programmer",
        "data",
        "machine learning",
        "artificial intelligence",
        "devops",
        "cloud",
        "cybersecurity",
        "cyber security",
        "network",
        "systems administrator",
        "information technology",
        "ict",
        "qa",
        "quality assurance",
        "product manager",
        "ux",
        "ui",
    ]

    return any(
        term in text
        for term in tech_terms
    )


def collect(
    count=100
):

    response = requests.get(
        API_URL,
        params={
            "count": min(
                count,
                100
            )
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    jobs = data.get(
        "jobs",
        []
    )

    records = []

    for job in jobs:

        title = clean_text(
            job.get(
                "jobTitle",
                ""
            )
        )

        industries = job.get(
            "jobIndustry",
            []
        )

        if isinstance(
            industries,
            str
        ):
            industries = [industries]

        if not is_tech_job(
            title,
            industries
        ):
            continue

        description = clean_text(
            re.sub(
                r"<[^>]+>",
                " ",
                job.get(
                    "jobDescription",
                    ""
                )
            )
        )

        job_url = clean_text(
            job.get(
                "url",
                ""
            )
        )

        location = clean_text(
            job.get(
                "jobGeo",
                "Anywhere"
            )
        )

        job_type = job.get(
            "jobType",
            []
        )

        if isinstance(
            job_type,
            list
        ):
            job_type = ", ".join(
                map(
                    str,
                    job_type
                )
            )

        salary_min = job.get(
            "salaryMin"
        )

        salary_max = job.get(
            "salaryMax"
        )

        salary = ""

        if (
            salary_min is not None
            or salary_max is not None
        ):

            salary = (
                f"{salary_min or ''}"
                f" - "
                f"{salary_max or ''}"
            ).strip()

        records.append({

            "job_id": generate_job_id(
                f"jobicy_{job.get('id', '')}"
            ),

            "source": "Jobicy",

            "source_job_id": str(
                job.get("id", "")
            ),

            "job_title": title,

            "company": clean_text(
                job.get(
                    "companyName",
                    ""
                )
            ),

            "job_description": description,

            "location": location,

            "country": location,

            "work_mode": "Remote",

            "remote_eligible": 1,

            "remote_scope": location,

            "job_field": (
                ", ".join(
                    map(
                        str,
                        industries
                    )
                )
            ),

            "industry": (
                ", ".join(
                    map(
                        str,
                        industries
                    )
                )
            ),

            "employment_type": job_type,

            "experience_required": clean_text(
                job.get(
                    "jobLevel",
                    ""
                )
            ),

            "education_required": "",

            "salary": salary,

            "currency": clean_text(
                job.get(
                    "salaryCurrency",
                    ""
                )
            ),

            "date_posted": clean_text(
                job.get(
                    "pubDate",
                    ""
                )
            ),

            "application_deadline": "",

            "tech_category": classify_category(
                title,
                industries
            ),

            "vacancy_url": job_url,

            "scraped_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "_is_tech_candidate": 1,
        })

    return pd.DataFrame(
        records
    )