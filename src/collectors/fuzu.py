import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


BASE_URL = "https://www.fuzu.com"

START_URL = (
    f"{BASE_URL}/kenya/job/"
    f"computers-software-development"
)

REQUEST_DELAY = 1.5
MAX_PAGES = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
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


def generate_job_id(url):

    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]


def normalize_url(url):

    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    ).rstrip("/")


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


def is_job_url(url):

    url = normalize_url(url)

    parsed = urlparse(url)

    if parsed.netloc not in {
        "www.fuzu.com",
        "fuzu.com"
    }:
        return False

    path = parsed.path.rstrip("/")

    # We want individual vacancies,
    # not the category page.
    if "/job/" not in path:
        return False

    if path == (
        "/kenya/job/"
        "computers-software-development"
    ):
        return False

    if path.endswith(
        "computers-software-development"
    ):
        return False

    return True


def extract_job_links(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = set()

    # Current Fuzu job cards contain the
    # actual individual job anchor.
    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"].strip()

        url = normalize_url(
            urljoin(
                BASE_URL,
                href
            )
        )

        if is_job_url(url):

            links.add(
                url
            )

    return sorted(
        links
    )


def get_page_url(
    page_number
):

    if page_number == 1:

        return START_URL

    return (
        f"{START_URL}"
        f"?page={page_number - 1}"
    )


def extract_value_from_text(
    text,
    label
):

    match = re.search(
        rf"{re.escape(label)}"
        r"\s*(.+?)"
        r"(?=\s+(?:Location|"
        r"Contract Type|Company|"
        r"Description|Tags)\b|$)",
        text,
        flags=re.IGNORECASE
    )

    if match:

        return clean_text(
            match.group(1)
        )

    return ""


def extract_description(
    soup
):

    heading = soup.find(
        lambda tag:
        tag.name in [
            "h2",
            "h3",
            "h4"
        ]
        and "description"
        in clean_text(
            tag.get_text(
                " ",
                strip=True
            )
        ).lower()
    )

    if heading:

        parts = []

        for element in heading.find_all_next():

            if (
                element.name in {
                    "h2",
                    "h3"
                }
                and element != heading
            ):
                break

            text = clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if text:

                parts.append(
                    text
                )

            if len(
                " ".join(parts)
            ) >= 12000:

                break

        result = clean_text(
            " ".join(parts)
        )

        if result:

            return result[:12000]

    main = soup.find(
        "main"
    )

    if main:

        return clean_text(
            main.get_text(
                " ",
                strip=True
            )
        )[:12000]

    return ""


def detect_work_mode(
    location,
    description
):

    text = clean_text(
        f"{location} {description}"
    ).lower()

    if "remote" in text:

        return (
            "Remote",
            1,
            "Kenya/Global"
        )

    if "hybrid" in text:

        return (
            "Hybrid",
            1,
            "Kenya"
        )

    return (
        "On-site",
        0,
        ""
    )


def classify_category(
    title
):

    title = title.lower()

    if any(
        x in title
        for x in [
            "data analyst",
            "data scientist",
            "data engineer",
            "machine learning",
            "artificial intelligence",
            "ai "
        ]
    ):

        return "Data & AI"

    if any(
        x in title
        for x in [
            "cybersecurity",
            "cyber security",
            "security analyst",
            "security engineer"
        ]
    ):

        return "Cybersecurity"

    if any(
        x in title
        for x in [
            "network engineer",
            "network administrator",
            "network"
        ]
    ):

        return "Networking"

    if any(
        x in title
        for x in [
            "devops",
            "cloud"
        ]
    ):

        return "Cloud & DevOps"

    if any(
        x in title
        for x in [
            "qa",
            "tester",
            "quality assurance"
        ]
    ):

        return "QA & Testing"

    if any(
        x in title
        for x in [
            "product manager",
            "product owner",
            "ux",
            "ui"
        ]
    ):

        return "Product & UX"

    return "Software & IT"


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

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    description = extract_description(
        soup
    )

    location = extract_value_from_text(
        page_text,
        "Location"
    )

    company = extract_value_from_text(
        page_text,
        "Company"
    )

    contract_type = extract_value_from_text(
        page_text,
        "Contract Type"
    )

    work_mode, remote, remote_scope = (
        detect_work_mode(
            location,
            description
        )
    )

    return {
        "job_id": generate_job_id(
            url
        ),
        "source": "Fuzu",
        "source_job_id": generate_job_id(
            url
        ),
        "job_title": title,
        "company": company,
        "job_description": description,
        "location": location,
        "country": "Kenya",
        "work_mode": work_mode,
        "remote_eligible": remote,
        "remote_scope": remote_scope,
        "job_field": (
            "Information Technology, "
            "Software Development, Data"
        ),
        "industry": "",
        "employment_type": contract_type,
        "experience_required": "",
        "education_required": "",
        "salary": "",
        "currency": "",
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


def collect():

    session = create_session()

    all_urls = set()

    print()
    print(
        "FUZU — DISCOVERING TECH JOBS"
    )

    for page in range(
        1,
        MAX_PAGES + 1
    ):

        listing_url = get_page_url(
            page
        )

        print(
            f"Page {page}: "
            f"{listing_url}"
        )

        try:

            html = get_page(
                session,
                listing_url
            )

        except Exception as e:

            print(
                f"Failed: {e}"
            )

            break

        links = extract_job_links(
            html
        )

        print(
            f"  Found {len(links)}"
        )

        if not links:

            break

        before = len(
            all_urls
        )

        all_urls.update(
            links
        )

        print(
            f"  New: "
            f"{len(all_urls) - before}"
        )

    print()
    print(
        f"Fuzu total vacancy URLs: "
        f"{len(all_urls)}"
    )

    records = []

    for i, url in enumerate(
        sorted(all_urls),
        start=1
    ):

        print(
            f"Fuzu [{i}/{len(all_urls)}]"
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

            if record[
                "_is_tech_candidate"
            ]:

                records.append(
                    record
                )

        except Exception as e:

            print(
                f"Failed: {e}"
            )

    print(
        f"Fuzu records: "
        f"{len(records)}"
    )

    return pd.DataFrame(
        records
    )