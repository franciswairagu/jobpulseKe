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

BASE_URL = "https://www.fuzu.com"

START_URLS = [
    (
        f"{BASE_URL}/kenya/job/"
        f"computers-software-development"
    ),

    # Fuzu also exposes the same category through Nairobi
    # pagination, which can expose additional/older listings.
    (
        f"{BASE_URL}/kenya/job/"
        f"computers-software-development/nairobi"
    ),
]

MAX_PAGES = 100

REQUEST_DELAY = 1.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
}


# ============================================================
# TECH KEYWORDS
# ============================================================

TECH_PATTERNS = [

    # Software
    r"\bsoftware\s+(engineer|developer|development)\b",
    r"\bsoftware\s+developer\b",
    r"\bsoftware\s+engineer\b",
    r"\bapplication\s+(developer|engineer)\b",
    r"\bweb\s+(developer|engineer)\b",
    r"\bfrontend\b",
    r"\bfront[- ]end\b",
    r"\bbackend\b",
    r"\bback[- ]end\b",
    r"\bfull[- ]stack\b",
    r"\bfullstack\b",
    r"\bmobile\s+(developer|engineer)\b",
    r"\bandroid\s+(developer|engineer)\b",
    r"\bios\s+(developer|engineer)\b",
    r"\bprogrammer\b",

    # Data / AI
    r"\bdata\s+scientist\b",
    r"\bdata\s+analyst\b",
    r"\bdata\s+engineer\b",
    r"\bdata\s+scientist\b",
    r"\bdata\s+science\b",
    r"\bdata\s+analytics\b",
    r"\bdata\s+analyst\b",
    r"\bmachine\s+learning\b",
    r"\bmachine\s+learning\s+engineer\b",
    r"\bartificial\s+intelligence\b",
    r"\bai\s+engineer\b",
    r"\bai\s+developer\b",
    r"\bml\s+engineer\b",
    r"\bllm\b",
    r"\bnlp\b",

    # Cybersecurity
    r"\bcyber\s*security\b",
    r"\bsecurity\s+analyst\b",
    r"\bsecurity\s+engineer\b",
    r"\binformation\s+security\b",
    r"\bcybersecurity\b",
    r"\bpenetration\s+tester\b",
    r"\bsoc\s+analyst\b",

    # Networking
    r"\bnetwork\s+engineer\b",
    r"\bnetwork\s+administrator\b",
    r"\bnetwork\s+technician\b",
    r"\bnetwork\s+architect\b",
    r"\bnoc\s+engineer\b",
    r"\bnoc\s+technician\b",

    # Cloud / DevOps
    r"\bdevops\b",
    r"\bcloud\s+engineer\b",
    r"\bcloud\s+architect\b",
    r"\bcloud\s+administrator\b",
    r"\bsite\s+reliability\b",
    r"\bsre\b",
    r"\binfrastructure\s+engineer\b",
    r"\bplatform\s+engineer\b",

    # IT
    r"\bit\s+(officer|manager|support|technician)\b",
    r"\bict\s+(officer|manager|support|technician)\b",
    r"\binformation\s+technology\b",
    r"\bsystems?\s+administrator\b",
    r"\bsystem\s+administrator\b",
    r"\bit\s+support\b",
    r"\btechnical\s+support\b",
    r"\bapplication\s+support\b",
    r"\bservice\s+desk\b",

    # QA
    r"\bqa\s+(engineer|analyst|tester)\b",
    r"\bquality\s+assurance\b",
    r"\bsoftware\s+tester\b",
    r"\btest\s+engineer\b",
    r"\bautomation\s+tester\b",

    # Architecture
    r"\bsolutions?\s+architect\b",
    r"\bsoftware\s+architect\b",
    r"\btechnical\s+architect\b",

    # Product / UX
    r"\bproduct\s+manager\b",
    r"\bproduct\s+owner\b",
    r"\btechnical\s+product\b",
    r"\bux\s+designer\b",
    r"\bui\s+designer\b",
    r"\buser\s+experience\b",
    r"\buser\s+interface\b",

    # Databases / ERP
    r"\bdatabase\s+administrator\b",
    r"\bdatabase\s+engineer\b",
    r"\bsql\s+developer\b",
    r"\berp\s+engineer\b",
    r"\berp\s+consultant\b",
    r"\bsap\s+developer\b",

    # Automation
    r"\bautomation\s+engineer\b",
    r"\brpa\s+developer\b",
    r"\brpa\s+engineer\b",
]


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
        str(text).replace(
            "\xa0",
            " "
        )
    ).strip()


def normalize_url(url):

    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    ).rstrip("/")


def generate_job_id(value):

    return hashlib.sha256(
        value.encode("utf-8")
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
        "www.fuzu.com",
        "fuzu.com",
    }:
        return False

    path = parsed.path.rstrip("/")

    if "/job/" not in path:
        return False

    # Exclude category pages
    if path.endswith(
        "computers-software-development"
    ):
        return False

    if path.endswith(
        "computers-software-development/nairobi"
    ):
        return False

    # Individual Fuzu jobs normally have
    # a deeper path after /job/
    parts = path.strip("/").split("/")

    if len(parts) < 4:
        return False

    return True


# ============================================================
# LINK EXTRACTION
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

        href = a[
            "href"
        ].strip()

        if not href:
            continue

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
# PAGINATION
# ============================================================

def build_page_url(
    base_url,
    page
):

    if page == 1:

        return base_url

    separator = (
        "&"
        if "?" in base_url
        else "?"
    )

    return (
        f"{base_url}"
        f"{separator}"
        f"page={page}"
    )


# ============================================================
# DESCRIPTION
# ============================================================

def extract_description(
    soup
):

    headings = soup.find_all(
        ["h2", "h3", "h4"]
    )

    for heading in headings:

        heading_text = clean_text(
            heading.get_text(
                " ",
                strip=True
            )
        ).lower()

        if heading_text not in {
            "description",
            "about the job",
            "about the role",
        }:

            continue

        parts = []

        for element in heading.find_all_next():

            if (
                element.name
                in {"h2", "h3", "h4"}
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


# ============================================================
# LABELED VALUES
# ============================================================

def extract_value(
    soup,
    labels
):

    if isinstance(
        labels,
        str
    ):
        labels = [labels]

    labels = [
        x.lower()
        for x in labels
    ]

    for tag in soup.find_all(
        [
            "li",
            "div",
            "p",
            "span",
            "td"
        ]
    ):

        text = clean_text(
            tag.get_text(
                " ",
                strip=True
            )
        )

        low = text.lower()

        for label in labels:

            if low.startswith(
                label
            ):

                value = text[
                    len(label):
                ].lstrip(
                    " :-"
                ).strip()

                if value:

                    return value

    return ""


# ============================================================
# TECH CLASSIFICATION
# ============================================================

def is_tech_job(
    title,
    description="",
    job_field=""
):

    text = clean_text(
        f"{title} "
        f"{description} "
        f"{job_field}"
    ).lower()

    return any(
        re.search(
            pattern,
            text
        )
        for pattern in TECH_PATTERNS
    )


def classify_category(
    title
):

    text = title.lower()

    if any(
        x in text
        for x in [
            "data",
            "machine learning",
            "artificial intelligence",
            "ai ",
            "llm",
            "nlp",
        ]
    ):

        return "Data & AI"

    if any(
        x in text
        for x in [
            "cyber",
            "security",
            "soc analyst",
            "penetration",
        ]
    ):

        return "Cybersecurity"

    if any(
        x in text
        for x in [
            "network",
            "noc",
        ]
    ):

        return "Networking"

    if any(
        x in text
        for x in [
            "devops",
            "cloud",
            "sre",
            "infrastructure",
            "platform engineer",
        ]
    ):

        return "Cloud & DevOps"

    if any(
        x in text
        for x in [
            "qa",
            "quality assurance",
            "tester",
            "testing",
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


# ============================================================
# WORK MODE
# ============================================================

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


# ============================================================
# PARSE JOB
# ============================================================

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

    location = extract_value(
        soup,
        [
            "Location"
        ]
    )

    company = extract_value(
        soup,
        [
            "Company"
        ]
    )

    contract_type = extract_value(
        soup,
        [
            "Contract Type"
        ]
    )

    job_field = (
        "Information technology, "
        "software development, data"
    )

    work_mode, remote, remote_scope = (
        detect_work_mode(
            location,
            description
        )
    )

    is_tech = is_tech_job(
        title,
        description,
        job_field
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

        "job_field": job_field,

        "industry": "",

        "employment_type": contract_type,

        "experience_required": "",

        "education_required": "",

        "salary": "",

        "currency": "",

        "date_posted": "",

        "application_deadline": "",

        "tech_category": (
            classify_category(title)
            if is_tech
            else ""
        ),

        "vacancy_url": url,

        "scraped_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "_is_tech_candidate": int(
            is_tech
        ),

    }


# ============================================================
# COLLECT
# ============================================================

def collect():

    session = create_session()

    all_urls = set()

    # Prevent endlessly scraping the same
    # HTML response under different page URLs.
    seen_page_signatures = set()

    print()
    print("=" * 70)
    print("FUZU HISTORICAL TECH COLLECTION")
    print("=" * 70)

    # --------------------------------------------------------
    # DISCOVER URLS
    # --------------------------------------------------------

    for base_url in START_URLS:

        print()
        print(
            f"BASE: {base_url}"
        )

        for page in range(
            1,
            MAX_PAGES + 1
        ):

            page_url = build_page_url(
                base_url,
                page
            )

            print(
                f"[PAGE {page}] "
                f"{page_url}"
            )

            try:

                html = get_page(
                    session,
                    page_url
                )

            except Exception as e:

                print(
                    f"  Failed: {e}"
                )

                break

            # ------------------------------------------------
            # Detect duplicate page content
            # ------------------------------------------------

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            visible_text = clean_text(
                soup.get_text(
                    " ",
                    strip=True
                )
            )

            signature = hashlib.sha256(
                visible_text.encode(
                    "utf-8"
                )
            ).hexdigest()

            if signature in seen_page_signatures:

                print(
                    "  Duplicate page content."
                )

                print(
                    "  Stopping this pagination branch."
                )

                break

            seen_page_signatures.add(
                signature
            )

            # ------------------------------------------------
            # Extract jobs
            # ------------------------------------------------

            links = extract_job_links(
                html
            )

            before = len(
                all_urls
            )

            all_urls.update(
                links
            )

            print(
                f"  Links: {len(links)}"
            )

            print(
                f"  New: "
                f"{len(all_urls) - before}"
            )

            print(
                f"  Total: "
                f"{len(all_urls)}"
            )

            # Don't stop merely because a page
            # contains zero new URLs. Some Fuzu
            # pages can contain a mixture of
            # current and closed listings.
            if page > 1 and not links:

                print(
                    "  No job links."
                )

                break

    # --------------------------------------------------------
    # DOWNLOAD JOB PAGES
    # --------------------------------------------------------

    print()
    print(
        f"Historical Fuzu vacancy URLs: "
        f"{len(all_urls)}"
    )

    records = []

    urls = sorted(
        all_urls
    )

    for i, url in enumerate(
        urls,
        start=1
    ):

        print(
            f"Fuzu historical "
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

            if record[
                "_is_tech_candidate"
            ]:

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
    print("FUZU HISTORICAL COLLECTION COMPLETE")
    print("=" * 70)

    print(
        f"Historical tech jobs: "
        f"{len(df)}"
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


if __name__ == "__main__":

    df = collect()

    output = (
        "data/raw/"
        "fuzu_historical_jobs.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    print()
    print(
        f"Saved to: {output}"
    )