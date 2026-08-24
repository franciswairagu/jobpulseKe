import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


BASE_URL = "https://www.brightermonday.co.ke"

START_URLS = [
    f"{BASE_URL}/jobs/software-data",
]

REQUEST_DELAY = 1.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


def create_session():

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    return session


def clean_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text.replace("\xa0", " ")
    ).strip()


def normalize_url(url):

    parsed = urlparse(
        url
    )

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    ).rstrip("/")


def generate_job_id(url):

    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]


def get_page(
    session,
    url
):

    time.sleep(
        REQUEST_DELAY
    )

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def extract_job_links(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = set()

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        # BrighterMonday vacancy pages
        # conventionally sit under /listings/
        if "/listings/" not in href:
            continue

        full_url = normalize_url(
            urljoin(
                BASE_URL,
                href
            )
        )

        links.add(
            full_url
        )

    return sorted(
        links
    )


def find_next_page(
    html,
    current_url
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for a in soup.find_all(
        "a",
        href=True
    ):

        text = clean_text(
            a.get_text(
                " ",
                strip=True
            )
        ).lower()

        if text in {
            "next",
            "next page",
            "›",
            "»"
        }:

            return normalize_url(
                urljoin(
                    current_url,
                    a["href"]
                )
            )

    return None


def extract_description(
    soup
):

    # Try article/main first
    candidates = [
        soup.find("main"),
        soup.find("article"),
    ]

    for candidate in candidates:

        if not candidate:
            continue

        text = clean_text(
            candidate.get_text(
                " ",
                strip=True
            )
        )

        if len(text) > 200:

            return text[:12000]

    return ""


def classify_category(
    title
):

    text = title.lower()

    if any(
        x in text
        for x in [
            "data scientist",
            "data analyst",
            "data engineer",
            "machine learning",
            "artificial intelligence",
            "ai ",
        ]
    ):
        return "Data & AI"

    if any(
        x in text
        for x in [
            "cybersecurity",
            "cyber security",
            "security analyst",
            "security engineer",
        ]
    ):
        return "Cybersecurity"

    if any(
        x in text
        for x in [
            "network engineer",
            "network administrator",
            "network technician",
        ]
    ):
        return "Networking"

    if any(
        x in text
        for x in [
            "cloud",
            "devops",
        ]
    ):
        return "Cloud & DevOps"

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


def detect_work_mode(
    location,
    text
):

    combined = clean_text(
        f"{location} {text}"
    ).lower()

    if "remote" in combined:
        return "Remote", 1, "Kenya"

    if "hybrid" in combined:
        return "Hybrid", 1, "Kenya"

    return "On-site", 0, ""


def parse_job_page(
    html,
    url
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    h1 = soup.find(
        "h1"
    )

    title = (
        clean_text(
            h1.get_text(
                " ",
                strip=True
            )
        )
        if h1
        else ""
    )

    description = extract_description(
        soup
    )

    body_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    company = ""

    # Common company markers
    company_match = re.search(
        r"Company\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Location|Work Type|"
        r"Job Function|Experience|Salary)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if company_match:

        company = clean_text(
            company_match.group(1)
        )

    location = ""

    location_match = re.search(
        r"Location\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Work Type|Job Function|"
        r"Experience Level|Salary|Company)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if location_match:

        location = clean_text(
            location_match.group(1)
        )

    work_mode, remote, remote_scope = (
        detect_work_mode(
            location,
            description
        )
    )

    work_type = ""

    work_match = re.search(
        r"Work Type\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Experience Level|"
        r"Salary|Location|Job Function)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if work_match:
        work_type = clean_text(
            work_match.group(1)
        )

    experience = ""

    experience_match = re.search(
        r"Experience Level\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Work Type|Salary|"
        r"Location|Job Function)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if experience_match:
        experience = clean_text(
            experience_match.group(1)
        )

    salary = ""

    salary_match = re.search(
        r"Salary\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Location|Work Type|"
        r"Experience|Job Function)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if salary_match:
        salary = clean_text(
            salary_match.group(1)
        )

    return {
        "job_id": generate_job_id(
            url
        ),
        "source": "BrighterMonday",
        "source_job_id": generate_job_id(url),
        "job_title": title,
        "company": company,
        "job_description": description,
        "location": location,
        "country": "Kenya",
        "work_mode": work_mode,
        "remote_eligible": remote,
        "remote_scope": remote_scope,
        "job_field": "Software & Data",
        "industry": "",
        "employment_type": work_type,
        "experience_required": experience,
        "education_required": "",
        "salary": salary,
        "currency": "KES" if "KSh" in salary or "KES" in salary else "",
        "date_posted": "",
        "application_deadline": "",
        "tech_category": classify_category(
            title
        ),
        "vacancy_url": url,
        "scraped_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "_is_tech_candidate": 1,
    }


def collect(
    max_pages=10
):

    session = create_session()

    urls = set()

    for start_url in START_URLS:

        current_url = start_url

        for page_no in range(
            1,
            max_pages + 1
        ):

            print(
                f"BrighterMonday listing "
                f"page {page_no}"
            )

            try:

                html = get_page(
                    session,
                    current_url
                )

            except Exception as e:

                print(
                    f"Failed listing: {e}"
                )

                break

            links = extract_job_links(
                html
            )

            print(
                f"  Found {len(links)} links"
            )

            urls.update(
                links
            )

            next_url = find_next_page(
                html,
                current_url
            )

            if not next_url:
                break

            current_url = next_url

    print(
        f"BrighterMonday vacancy URLs: "
        f"{len(urls)}"
    )

    records = []

    for i, url in enumerate(
        sorted(urls),
        start=1
    ):

        print(
            f"BrighterMonday "
            f"[{i}/{len(urls)}]"
        )

        try:

            html = get_page(
                session,
                url
            )

            record = parse_job_page(
                html,
                url
            )

            records.append(
                record
            )

        except Exception as e:

            print(
                f"Failed: {e}"
            )

    return pd.DataFrame(
        records
    )