import re
import hashlib
import requests
import pandas as pd

from datetime import datetime, timezone


API_URL = (
    "https://remotive.com/api/remote-jobs"
)


TECH_CATEGORIES = {
    "software development",
    "devops / sysadmin",
    "data",
    "data science",
    "artificial intelligence",
    "information technology",
    "quality assurance",
}


def clean_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        re.sub(
            r"<[^>]+>",
            " ",
            str(text)
        )
    ).strip()


def generate_job_id(value):

    return hashlib.sha256(
        value.encode(
            "utf-8"
        )
    ).hexdigest()[:16]


def classify_category(
    title,
    category
):

    text = (
        f"{title} {category}"
    ).lower()

    if any(
        x in text
        for x in [
            "data",
            "machine learning",
            "artificial intelligence",
            "ai",
        ]
    ):
        return "Data & AI"

    if any(
        x in text
        for x in [
            "devops",
            "sysadmin",
            "cloud",
            "infrastructure",
        ]
    ):
        return "Cloud & DevOps"

    if any(
        x in text
        for x in [
            "security",
            "cybersecurity",
        ]
    ):
        return "Cybersecurity"

    if any(
        x in text
        for x in [
            "qa",
            "quality assurance",
            "tester",
        ]
    ):
        return "QA & Testing"

    if any(
        x in text
        for x in [
            "product manager",
            "product owner",
            "ux",
            "ui",
        ]
    ):
        return "Product & UX"

    return "Software & IT"


def collect(
    limit=100
):

    response = requests.get(
        API_URL,
        params={
            "limit": limit
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
                "title",
                ""
            )
        )

        category = clean_text(
            job.get(
                "category",
                ""
            )
        )

        category_lower = category.lower()

        if category_lower not in TECH_CATEGORIES:

            # Secondary title check
            combined = (
                f"{title} {category}"
            ).lower()

            technical_terms = [
                "software",
                "developer",
                "engineer",
                "data",
                "machine learning",
                "ai ",
                "devops",
                "cloud",
                "security",
                "qa",
                "sysadmin",
                "information technology",
            ]

            if not any(
                term in combined
                for term in technical_terms
            ):
                continue

        job_url = clean_text(
            job.get(
                "url",
                ""
            )
        )

        records.append({

            "job_id": generate_job_id(
                f"remotive_{job.get('id', '')}"
            ),

            "source": "Remotive",

            "source_job_id": str(
                job.get(
                    "id",
                    ""
                )
            ),

            "job_title": title,

            "company": clean_text(
                job.get(
                    "company_name",
                    ""
                )
            ),

            "job_description": clean_text(
                job.get(
                    "description",
                    ""
                )
            ),

            "location": clean_text(
                job.get(
                    "candidate_required_location",
                    ""
                )
            ),

            "country": clean_text(
                job.get(
                    "candidate_required_location",
                    ""
                )
            ),

            "work_mode": "Remote",

            "remote_eligible": 1,

            "remote_scope": clean_text(
                job.get(
                    "candidate_required_location",
                    ""
                )
            ),

            "job_field": category,

            "industry": "",

            "employment_type": clean_text(
                job.get(
                    "job_type",
                    ""
                )
            ),

            "experience_required": "",

            "education_required": "",

            "salary": clean_text(
                job.get(
                    "salary",
                    ""
                )
            ),

            "currency": "",

            "date_posted": clean_text(
                job.get(
                    "publication_date",
                    ""
                )
            ),

            "application_deadline": "",

            "tech_category": classify_category(
                title,
                category
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