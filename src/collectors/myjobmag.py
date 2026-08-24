import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


BASE_URL = "https://www.myjobmag.co.ke"

REQUEST_DELAY = 1.5
MAX_PAGES_PER_CATEGORY = 20

START_URLS = [
    f"{BASE_URL}/jobs-by-field/information-technology",
    f"{BASE_URL}/jobs-by-field/research-data-analysis",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


TECH_TITLE_PATTERNS = [
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
    r"\bdata\s+scientist\b",
    r"\bdata\s+analyst\b",
    r"\bdata\s+engineer\b",
    r"\bdata\s+science\b",
    r"\bmachine\s+learning\b",
    r"\bartificial\s+intelligence\b",
    r"\bai\s+engineer\b",
    r"\bcyber\s*security\b",
    r"\bsecurity\s+analyst\b",
    r"\bsecurity\s+engineer\b",
    r"\bnetwork\s+engineer\b",
    r"\bnetwork\s+administrator\b",
    r"\bnetwork\s+technician\b",
    r"\bdevops\b",
    r"\bcloud\s+engineer\b",
    r"\bcloud\s+architect\b",
    r"\bit\s+(officer|manager|support|technician)\b",
    r"\bict\s+(officer|manager|support|technician)\b",
    r"\bsystem\s+administrator\b",
    r"\bsystems\s+administrator\b",
    r"\bqa\s+(engineer|analyst|tester)\b",
    r"\bsoftware\s+tester\b",
    r"\bsolutions?\s+architect\b",
    r"\bproduct\s+manager\b",
    r"\bproduct\s+owner\b",
    r"\bux\s+designer\b",
    r"\bui\s+designer\b",
]


def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
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
    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    ).rstrip("/")


def generate_job_id(url):
    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]


def get_page(session, url):
    time.sleep(REQUEST_DELAY)

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def is_job_url(url):
    """
    MyJobMag category pages link to individual vacancies
    using /job/<slug>, while some older pages may use
    /jobs/<slug>.
    """

    url = normalize_url(url)

    parsed = urlparse(url)

    if parsed.netloc not in {
        "www.myjobmag.co.ke",
        "myjobmag.co.ke"
    }:
        return False

    parts = parsed.path.strip("/").split("/")

    if len(parts) != 2:
        return False

    if parts[0].lower() not in {
        "job",
        "jobs"
    }:
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

def extract_job_links(html):
    """
    Extract individual MyJobMag vacancy links.

    Current MyJobMag category pages use /job/<slug>.
    Some older/general pages use /jobs/<slug>.
    """

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

        if not href:
            continue

        url = normalize_url(
            urljoin(
                BASE_URL,
                href
            )
        )

        if is_job_url(url):
            links.add(url)

    return sorted(links)

def classify_title(title):

    text = clean_text(
        title
    ).lower()

    return any(
        re.search(
            pattern,
            text
        )
        for pattern in TECH_TITLE_PATTERNS
    )


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
        ]
    ):
        return "Networking"

    if any(
        x in text
        for x in [
            "devops",
            "cloud engineer",
            "cloud architect",
        ]
    ):
        return "Cloud & DevOps"

    if any(
        x in text
        for x in [
            "qa engineer",
            "qa analyst",
            "qa tester",
            "software tester",
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


def extract_labeled_value(
    soup,
    labels
):

    if isinstance(labels, str):
        labels = [labels]

    labels_lower = [
        x.lower()
        for x in labels
    ]

    for tag in soup.find_all(
        ["li", "div", "p", "span", "td"]
    ):

        text = clean_text(
            tag.get_text(
                " ",
                strip=True
            )
        )

        low = text.lower()

        for label in labels_lower:

            if low.startswith(label):

                value = text[
                    len(label):
                ].lstrip(
                    " :-"
                ).strip()

                if value:
                    return value

    return ""


def extract_description(soup):

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
                "h4"
            ]
            and clean_text(
                tag.get_text(
                    " ",
                    strip=True
                )
            ).lower() == heading.lower()
        )

        if not node:
            continue

        parts = []

        for element in node.find_all_next():

            if (
                element.name in [
                    "h2",
                    "h3"
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
                parts.append(text)

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


def parse_job_page(
    html,
    url
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    h1 = soup.find("h1")

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

    location = extract_labeled_value(
        soup,
        [
            "Location",
            "Job Location"
        ]
    )

    job_field = extract_labeled_value(
        soup,
        [
            "Job Field"
        ]
    )

    employment_type = extract_labeled_value(
        soup,
        [
            "Job Type",
            "Employment Type"
        ]
    )

    education = extract_labeled_value(
        soup,
        [
            "Qualification",
            "Qualifications"
        ]
    )

    salary = extract_labeled_value(
        soup,
        [
            "Salary",
            "Salary Range"
        ]
    )

    date_posted = ""

    date_match = re.search(
        r"\b(\d{1,2}\s+"
        r"[A-Za-z]+\s+\d{4})\b",
        page_text
    )

    if date_match:
        date_posted = date_match.group(1)

    description = extract_description(
        soup
    )

    experience = ""

    experience_match = re.search(
        r"\b\d+\+?\s*"
        r"(?:years?|yrs?)\b",
        page_text,
        flags=re.IGNORECASE
    )

    if experience_match:
        experience = experience_match.group(0)

    is_tech = classify_title(
        title
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
        "currency": (
            "KES"
            if "ksh" in salary.lower()
            else ""
        ),
        "date_posted": date_posted,
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
        "_is_tech_candidate": int(is_tech),
    }


def collect():

    session = create_session()

    all_urls = set()

    for start_url in START_URLS:

        print()
        print(
            f"MyJobMag category:"
        )
        print(
            start_url
        )

        for page_number in range(
            1,
            MAX_PAGES_PER_CATEGORY + 1
        ):

            if page_number == 1:

                listing_url = start_url

            else:

                listing_url = (
                    f"{start_url}/"
                    f"{page_number}"
                )

            print(
                f"  Page {page_number}: "
                f"{listing_url}"
            )

            try:

                html = get_page(
                    session,
                    listing_url
                )

            except Exception as e:

                print(
                    f"  Failed: {e}"
                )

                break

            links = extract_job_links(
                html
            )

            print(
                f"  Jobs found: {len(links)}"
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
                f"  New jobs: "
                f"{len(all_urls) - before}"
            )

    print()
    print(
        f"MyJobMag total vacancy URLs: "
        f"{len(all_urls)}"
    )

    records = []

    for i, url in enumerate(
        sorted(all_urls),
        start=1
    ):

        print(
            f"MyJobMag [{i}/{len(all_urls)}]"
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

            if record["_is_tech_candidate"]:

                records.append(
                    record
                )

        except Exception as e:

            print(
                f"Failed: {e}"
            )

    print(
        f"MyJobMag tech records: "
        f"{len(records)}"
    )

    return pd.DataFrame(
        records
    )