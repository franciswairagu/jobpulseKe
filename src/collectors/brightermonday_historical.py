import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://www.brightermonday.co.ke"

START_URL = (
    f"{BASE_URL}/jobs/software-data"
)

REQUEST_DELAY = 1.5

MAX_PAGES = 100

OUTPUT_FILE = (
    "data/raw/brightermonday_historical_jobs.csv"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# SESSION
# ============================================================

def create_session():

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    return session


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text)
        .replace("\xa0", " ")
    ).strip()


def normalize_url(url):

    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
        + (
            f"?{parsed.query}"
            if parsed.query
            else ""
        )
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


# ============================================================
# JOB URL DETECTION
# ============================================================

def is_job_url(url):

    url = normalize_url(url)

    parsed = urlparse(url)

    if parsed.netloc not in {
        "brightermonday.co.ke",
        "www.brightermonday.co.ke"
    }:
        return False

    path = parsed.path.lower()

    # Individual BrighterMonday vacancies
    return "/listings/" in path


# ============================================================
# EXTRACT JOB LINKS
# ============================================================

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


# ============================================================
# FIND NEXT PAGE
# ============================================================

def find_next_page(
    html,
    current_url
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidates = []

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

        aria = clean_text(
            a.get(
                "aria-label",
                ""
            )
        ).lower()

        href = a.get(
            "href",
            ""
        ).strip()

        if not href:
            continue

        full_url = normalize_url(
            urljoin(
                current_url,
                href
            )
        )

        # ----------------------------------------------------
        # Strongest signal:
        # aria-label="Go to next page"
        # ----------------------------------------------------

        if aria == "go to next page":

            candidates.append(
                full_url
            )

            continue

        # ----------------------------------------------------
        # Other possible next labels
        # ----------------------------------------------------

        if text in {
            "next",
            "next page",
            "›",
            "»",
        }:

            candidates.append(
                full_url
            )

    # Remove current page
    candidates = [
        url
        for url in candidates
        if url != normalize_url(
            current_url
        )
    ]

    if candidates:

        return candidates[0]

    return None


# ============================================================
# PARSE JOB
# ============================================================

def classify_category(title):

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
            "devops",
            "cloud",
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


def extract_description(soup):

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

    # --------------------------------------------------------
    # Company
    # --------------------------------------------------------

    company = ""

    match = re.search(
        r"Company\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Location|Work Type|"
        r"Job Function|Experience|Salary)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if match:

        company = clean_text(
            match.group(1)
        )

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    location = ""

    match = re.search(
        r"Location\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Work Type|Job Function|"
        r"Experience Level|Salary|Company)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if match:

        location = clean_text(
            match.group(1)
        )

    # --------------------------------------------------------
    # Work mode
    # --------------------------------------------------------

    combined = clean_text(
        f"{location} {description}"
    ).lower()

    if "remote" in combined:

        work_mode = "Remote"
        remote = 1
        remote_scope = "Kenya"

    elif "hybrid" in combined:

        work_mode = "Hybrid"
        remote = 1
        remote_scope = "Kenya"

    else:

        work_mode = "On-site"
        remote = 0
        remote_scope = ""

    # --------------------------------------------------------
    # Work type
    # --------------------------------------------------------

    work_type = ""

    match = re.search(
        r"Work Type\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Experience Level|"
        r"Salary|Location|Job Function)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if match:

        work_type = clean_text(
            match.group(1)
        )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    experience = ""

    match = re.search(
        r"Experience Level\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Work Type|Salary|"
        r"Location|Job Function)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if match:

        experience = clean_text(
            match.group(1)
        )

    # --------------------------------------------------------
    # Salary
    # --------------------------------------------------------

    salary = ""

    match = re.search(
        r"Salary\s*:?\s*(.{2,100}?)"
        r"(?=\s+(?:Location|Work Type|"
        r"Experience|Job Function)\b|$)",
        body_text,
        flags=re.IGNORECASE
    )

    if match:

        salary = clean_text(
            match.group(1)
        )

    return {

        "job_id":
            generate_job_id(url),

        "source":
            "BrighterMonday",

        "source_job_id":
            generate_job_id(url),

        "job_title":
            title,

        "company":
            company,

        "job_description":
            description,

        "location":
            location,

        "country":
            "Kenya",

        "work_mode":
            work_mode,

        "remote_eligible":
            remote,

        "remote_scope":
            remote_scope,

        "job_field":
            "Software & Data",

        "industry":
            "",

        "employment_type":
            work_type,

        "experience_required":
            experience,

        "education_required":
            "",

        "salary":
            salary,

        "currency":
            (
                "KES"
                if (
                    "KSh" in salary
                    or "KES" in salary
                )
                else ""
            ),

        "date_posted":
            "",

        "application_deadline":
            "",

        "tech_category":
            classify_category(title),

        "vacancy_url":
            url,

        "scraped_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

    }


# ============================================================
# HISTORICAL URL DISCOVERY
# ============================================================

def discover_historical_urls():

    session = create_session()

    all_urls = set()

    visited_pages = set()

    current_url = START_URL

    page_number = 1

    print()
    print("=" * 70)
    print(
        "BRIGHTERMONDAY HISTORICAL URL DISCOVERY"
    )
    print("=" * 70)

    while (
        current_url
        and page_number <= MAX_PAGES
    ):

        current_url = normalize_url(
            current_url
        )

        # ----------------------------------------------------
        # Prevent infinite loops
        # ----------------------------------------------------

        if current_url in visited_pages:

            print(
                "  Already visited page."
            )

            break

        visited_pages.add(
            current_url
        )

        print()
        print(
            f"[PAGE {page_number}] "
            f"{current_url}"
        )

        try:

            html = get_page(
                session,
                current_url
            )

        except Exception as e:

            print(
                f"  Failed listing page: {e}"
            )

            break

        links = extract_job_links(
            html
        )

        before = len(
            all_urls
        )

        all_urls.update(
            links
        )

        new_count = (
            len(all_urls)
            - before
        )

        print(
            f"  Links: {len(links)} "
            f"| New: {new_count} "
            f"| Total: {len(all_urls)}"
        )

        next_url = find_next_page(
            html,
            current_url
        )

        if not next_url:

            print(
                "  No next page found."
            )

            break

        if normalize_url(
            next_url
        ) == current_url:

            print(
                "  Next page is same as "
                "current page. Stopping."
            )

            break

        current_url = next_url

        page_number += 1

    print()
    print(
        f"Historical vacancy URLs: "
        f"{len(all_urls)}"
    )

    return sorted(
        all_urls
    )


# ============================================================
# DOWNLOAD HISTORICAL JOBS
# ============================================================

def collect_historical_jobs():

    session = create_session()

    urls = discover_historical_urls()

    records = []

    print()
    print("=" * 70)
    print(
        "DOWNLOADING HISTORICAL BRIGHTERMONDAY JOBS"
    )
    print("=" * 70)

    for i, url in enumerate(
        urls,
        start=1
    ):

        print(
            f"[{i}/{len(urls)}] "
            f"{url}"
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

            # Require a meaningful title
            if len(
                record["job_title"]
            ) < 3:

                continue

            records.append(
                record
            )

        except Exception as e:

            print(
                f"  Failed: {e}"
            )

    df = pd.DataFrame(
        records
    )

    print()
    print("=" * 70)
    print(
        "HISTORICAL COLLECTION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Historical jobs: {len(df)}"
    )

    if not df.empty:

        print()
        print(
            "BY CATEGORY"
        )

        print(
            df[
                "tech_category"
            ]
            .value_counts()
            .to_string()
        )

    return df


# ============================================================
# SAVE
# ============================================================

def main():

    df = collect_historical_jobs()

    if df.empty:

        print(
            "No historical records collected."
        )

        return

    import os

    os.makedirs(
        "data/raw",
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":

    main()