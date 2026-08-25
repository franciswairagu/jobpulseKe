import os
import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


# CONFIGURATION

BASE_URL = "https://www.myjobmag.co.ke"

START_PAGES = {
    "information-technology": 1,
    "research-data-analysis": 1,
}

END_PAGE = 100
REQUEST_DELAY = 1.5
OUTPUT_DIR = "data/raw"

OUTPUT_FILE = (f"{OUTPUT_DIR}/myjobmag_historical_deep.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# TECH TITLE PATTERNS
TECH_TITLE_PATTERNS = [
    # Software
    r"\bsoftware\s+(engineer|developer|development)\b",
    r"\bapplication\s+(developer|engineer)\b",
    r"\bweb\s+(developer|engineer)\b",
    r"\bfrontend\b",
    r"\bfront[- ]end\b",
    r"\bbackend\b",
    r"\bback[- ]end\b",
    r"\bfull[- ]stack\b",
    r"\bmobile\s+(developer|engineer)\b",
    r"\bandroid\s+(developer|engineer)\b",
    r"\bios\s+(developer|engineer)\b",
    r"\bprogrammer\b",
    r"\bsoftware\s+architect\b",
    r"\bsolutions?\s+architect\b",

    # Data / AI
    r"\bdata\s+scientist\b",
    r"\bdata\s+analyst\b",
    r"\bdata\s+engineer\b",
    r"\bdata\s+science\b",
    r"\bmachine\s+learning\b",
    r"\bartificial\s+intelligence\b",
    r"\bai\s+engineer\b",
    r"\bai\s+developer\b",
    r"\banalytics\s+(engineer|analyst)\b",

    # Cybersecurity
    r"\bcyber\s*security\b",
    r"\bsecurity\s+analyst\b",
    r"\bsecurity\s+engineer\b",
    r"\binformation\s+security\b",
    r"\bsecurity\s+specialist\b",

    # Networking
    r"\bnetwork\s+engineer\b",
    r"\bnetwork\s+administrator\b",
    r"\bnetwork\s+technician\b",
    r"\bnetwork\s+specialist\b",

    # Cloud / DevOps
    r"\bdevops\b",
    r"\bcloud\s+engineer\b",
    r"\bcloud\s+architect\b",
    r"\bcloud\s+administrator\b",
    r"\bsite\s+reliability\b",
    r"\bsre\b",
    r"\binfrastructure\s+engineer\b",

    # IT
    r"\bit\s+(officer|manager|support|technician)\b",
    r"\bict\s+(officer|manager|support|technician)\b",
    r"\bsystem\s+administrator\b",
    r"\bsystems\s+administrator\b",
    r"\bit\s+support\b",
    r"\btechnical\s+support\b",
    r"\bhelp\s+desk\b",

    # QA
    r"\bqa\s+(engineer|analyst|tester)\b",
    r"\bquality\s+assurance\b",
    r"\bsoftware\s+tester\b",
    r"\btest\s+engineer\b",

    # Product / UX
    r"\bproduct\s+manager\b",
    r"\bproduct\s+owner\b",
    r"\bux\s+designer\b",
    r"\bui\s+designer\b",
]


# SESSION
def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


# TEXT
def clean_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


# URL
def normalize_url(url):
    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    ).rstrip("/")


def generate_job_id(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

# REQUEST
def get_page(session, url):
    time.sleep(REQUEST_DELAY)

    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.text

# JOB URL DETECTION
def is_job_url(url):
    url = normalize_url(url)
    parsed = urlparse(url)

    if parsed.netloc not in {
        "www.myjobmag.co.ke",
        "myjobmag.co.ke",
    }:
        return False

    parts = (parsed.path.strip("/").split("/"))

    if len(parts) != 2:
        return False

    if parts[0].lower() not in {"job", "jobs",}:
        return False

    slug = parts[1].lower()

    excluded = {
        "jobs",
        "job",
        "students",
        "internships",
        "graduate-jobs",
        "volunteer",
        "job-alerts",
    }

    return slug not in excluded


# EXTRACT LINKS
def extract_job_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if not href:
            continue

        url = normalize_url(urljoin(BASE_URL, href))

        if is_job_url(url):
            links.add(url)

    return sorted(links)


# TECH CLASSIFICATION
def is_tech_title(title):
    text = clean_text(
        title
    ).lower()

    for pattern in TECH_TITLE_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            return True

    return False


def classify_category(title):

    text = title.lower()

    if any(
        x in text
        for x in [
            "data scientist",
            "data analyst",
            "data engineer",
            "data science",
            "machine learning",
            "artificial intelligence",
            "ai engineer",
            "analytics",
        ]
    ):

        return "Data & AI"

    if any(
        x in text
        for x in [
            "cyber",
            "security analyst",
            "security engineer",
            "information security",
        ]
    ):

        return "Cybersecurity"

    if any(
        x in text
        for x in [
            "network engineer",
            "network administrator",
            "network technician",
            "network specialist",
        ]
    ):

        return "Networking"

    if any(
        x in text
        for x in [
            "devops",
            "cloud engineer",
            "cloud architect",
            "site reliability",
            "infrastructure engineer",
        ]
    ):

        return "Cloud & DevOps"

    if any(
        x in text
        for x in [
            "qa",
            "quality assurance",
            "software tester",
            "test engineer",
        ]
    ):

        return "QA & Testing"

    if any(
        x in text
        for x in [
            "product manager",
            "product owner",
            "ux designer",
            "ui designer",
        ]
    ):

        return "Product & UX"

    return "Software & IT"


# LABELED VALUES

def extract_labeled_value(
    soup,
    labels
):

    if isinstance(
        labels,
        str
    ):

        labels = [labels]

    labels_lower = [
        x.lower()
        for x in labels
    ]

    for tag in soup.find_all(
        [
            "li",
            "div",
            "p",
            "span",
            "td",
        ]
    ):

        text = clean_text(
            tag.get_text(
                " ",
                strip=True
            )
        )

        low = text.lower()

        for label in labels_lower:

            if low.startswith(
                label
            ):

                value = (
                    text[
                        len(label):
                    ]
                    .lstrip(" :-")
                    .strip()
                )

                if value:

                    return value

    return ""


# DESCRIPTION

def extract_description(
    soup
):

    headings = [
        "Job Description",
        "Description",
        "About the Job",
        "About the Role",
    ]

    for heading in headings:

        node = soup.find(
            lambda tag:
            tag.name in [
                "h2",
                "h3",
                "h4",
            ]
            and clean_text(
                tag.get_text(
                    " ",
                    strip=True
                )
            ).lower()
            == heading.lower()
        )

        if not node:
            continue

        parts = []

        for element in node.find_all_next():

            if (
                element.name in [
                    "h2",
                    "h3",
                ]
                and element != node
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
            ) >= 10000:

                break

        result = clean_text(
            " ".join(parts)
        )

        if result:

            return result[:10000]

    return ""


# PARSE JOB

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

    # Only keep actual tech vacancies

    if not is_tech_title(
        title
    ):

        return None

    # Company

    company = ""

    company_match = re.search(
        r"View Jobs at\s+(.+?)"
        r"(?=\s+(?:Posted|Deadline|"
        r"Save|Email|Contents)\b|$)",
        page_text,
        flags=re.IGNORECASE
    )

    if company_match:

        company = clean_text(
            company_match.group(1)
        )

    # Fields

    location = extract_labeled_value(
        soup,
        [
            "Location",
            "Job Location",
        ]
    )

    job_field = extract_labeled_value(
        soup,
        [
            "Job Field",
        ]
    )

    employment_type = extract_labeled_value(
        soup,
        [
            "Job Type",
            "Employment Type",
        ]
    )

    education = extract_labeled_value(
        soup,
        [
            "Qualification",
            "Qualifications",
        ]
    )

    salary = extract_labeled_value(
        soup,
        [
            "Salary",
            "Salary Range",
        ]
    )

    # Date

    date_posted = ""

    date_match = re.search(
        r"\b(\d{1,2}\s+"
        r"[A-Za-z]+\s+\d{4})\b",
        page_text
    )

    if date_match:

        date_posted = (
            date_match.group(1)
        )

    # Experience

    experience = ""

    experience_match = re.search(
        r"\b\d+\+?\s*"
        r"(?:years?|yrs?)\b",
        page_text,
        flags=re.IGNORECASE
    )

    if experience_match:

        experience = (
            experience_match.group(0)
        )

    # Description

    description = extract_description(
        soup
    )

    return {
        "job_id": generate_job_id(url),
        "source": "MyJobMag",
        "source_job_id": generate_job_id(url),
        "job_title": title,
        "company": company,
        "job_description": description,
        "location": location,
        "country": "Kenya",
        "work_mode": "",
        "remote_eligible": 0,
        "remote_scope": "",
        "job_field": job_field,
        "industry": "",
        "employment_type": employment_type,
        "experience_required": experience,
        "education_required": education,
        "salary": salary,
        "currency":
            ("KES" if "ksh" in salary.lower() else ""),
        "date_posted": date_posted,
        "application_deadline": "",
        "tech_category": classify_category(title),
        "vacancy_url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "_is_tech_candidate": 1,
    }


# HISTORICAL COLLECTION
def collect_category(session, category, start_page, end_page):
    category_url = (
        f"{BASE_URL}/jobs-by-field/"
        f"{category}"
    )

    all_urls = set()

    print()
    print("=" * 75)
    print(f"HISTORICAL CATEGORY: {category}")
    print("=" * 75)

    for page in range(start_page, end_page + 1):
        listing_url = (f"{category_url}/{page}")

        print(
            f"[PAGE {page}] "
            f"{listing_url}"
        )

        try:
            html = get_page(session, listing_url)

        except Exception as e:
            print(f"  Failed: {e}")
            continue

        links = extract_job_links(html)
        before = len(all_urls)

        all_urls.update(links)

        print(
            f"  Links: {len(links)} | "
            f"New: "
            f"{len(all_urls) - before} | "
            f"Total: {len(all_urls)}"
        )

    return all_urls


def collect():
    session = create_session()
    categories = [
        "information-technology",
        "research-data-analysis",
    ]

    all_urls = set()

    # DISCOVER HISTORICAL VACANCY URLs

    for category in categories:
        urls = collect_category(
            session=session,
            category=category,
            start_page=21,
            end_page=100
        )

        all_urls.update(urls)

    print()
    print("=" * 75)
    print(
        f"TOTAL HISTORICAL VACANCY URLS: "
        f"{len(all_urls)}"
    )
    print("=" * 75)

    # DOWNLOAD + PARSE HISTORICAL JOBS

    records = []

    urls = sorted(all_urls)

    for i, url in enumerate(urls, start=1):
        print(f"[JOB {i}/{len(urls)}]")

        try:
            html = get_page(session, url)
            record = parse_job_page(html, url)

            if record is not None:
                records.append(record)

        except Exception as e:
            print(f"  Failed: {e}")

    # CREATE DATAFRAME

    df = pd.DataFrame(record)

    print()
    print("=" * 75)
    print("HISTORICAL COLLECTION COMPLETE")
    print("=" * 75)

    print(
        f"Historical tech jobs: "
        f"{len(df)}"
    )

    # REPORT

    if not df.empty:

        print()
        print("BY CATEGORY")

        print(
            df["tech_category"]
            .value_counts()
            .to_string()
        )

        print()
        print(
            "DATE POSTED"
        )

        print(
            df["date_posted"]
            .value_counts()
            .head(20)
            .to_string()
        )

        # SAVE

        os.makedirs(
            OUTPUT_DIR, exist_ok=True
        )

        df.to_csv(
            OUTPUT_FILE, index=False
        )

        print()
        print(f"Saved to: "f"{OUTPUT_FILE}")

    else:
        print("No historical tech jobs found.")

    return df



if __name__ == "__main__":

    collect()