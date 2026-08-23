import re
import os
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

# Configuration 
BASE_URL = "https://www.myjobmag.co.ke"

# start with the main jobs page 
START_URL = f"{BASE_URL}/jobs"
MAX_PAGES = 20
MAX_JOBS = 500
REQUEST_DELAY = 1.5
OUTPUT_PATH = "data/raw/myjobmag_jobs_raw.csv"

HEADERS = {
    "User-Agent":(
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),

    "Accept-Language": "en-US,en;q=0.9",
}

# TECH KEYWORDS 
TECH_KEYWORDS = {

    # Software Development

    "software development": [
        "software developer",
        "software engineer",
        "software development",
        "application developer",
        "application development",
        "web developer",
        "web development",
        "frontend developer",
        "front-end developer",
        "backend developer",
        "back-end developer",
        "full stack developer",
        "full-stack developer",
        "mobile developer",
        "android developer",
        "ios developer",
        "programmer",
        "software programmer",
        "php developer",
        "java developer",
        "python developer",
        "javascript developer",
        "react developer",
        "node.js developer",
        "nodejs developer",
        "flutter developer",
        "wordpress developer",
    ],

    # Data / AI / Machine Learning

    "data & ai": [
        "data scientist",
        "data science",
        "data analyst",
        "data analysis",
        "data engineer",
        "data engineering",
        "machine learning",
        "machine learning engineer",
        "artificial intelligence",
        "ai engineer",
        "ai developer",
        "deep learning",
        "nlp",
        "natural language processing",
        "computer vision",
        "business intelligence",
        "business intelligence analyst",
        "bi analyst",
        "data warehouse",
        "data mining",
        "analytics engineer",
    ],

    # Cybersecurity

    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
        "information security analyst",
        "security analyst",
        "security engineer",
        "security specialist",
        "security administrator",
        "penetration tester",
        "penetration testing",
        "ethical hacker",
        "soc analyst",
        "security operations",
        "siem",
    ],

    # Cloud / DevOps

    "cloud & devops": [
        "devops",
        "devops engineer",
        "cloud engineer",
        "cloud architect",
        "cloud computing",
        "aws",
        "amazon web services",
        "microsoft azure",
        "azure",
        "google cloud",
        "gcp",
        "kubernetes",
        "docker",
        "site reliability engineer",
        "sre",
        "cloud infrastructure",
        "infrastructure engineer",
    ],

    # Networking

    "networking": [
        "network engineer",
        "network administrator",
        "network technician",
        "networking",
        "network infrastructure",
        "cisco",
        "ccna",
        "ccnp",
        "lan administrator",
        "wan administrator",
        "telecommunications engineer",
    ],

    # IT Support / Systems

    "it & systems": [
        "it officer",
        "it support",
        "it technician",
        "it administrator",
        "it manager",
        "information technology",
        "technical support",
        "help desk",
        "helpdesk",
        "systems administrator",
        "system administrator",
        "systems engineer",
        "system engineer",
        "database administrator",
        "database engineer",
        "it infrastructure",
        "ict officer",
        "ict technician",
        "ict manager",
    ],

    # QA / Testing

    "qa & testing": [
        "qa engineer",
        "qa analyst",
        "quality assurance engineer",
        "quality assurance analyst",
        "software tester",
        "software testing",
        "test engineer",
        "automation tester",
        "test automation",
        "quality assurance",
    ],

    # Product / UX / Technical Management

    "product & design": [
        "product manager",
        "technical product manager",
        "product owner",
        "product designer",
        "ux designer",
        "ui designer",
        "ui/ux",
        "ux/ui",
        "user experience",
        "user interface",
        "technical consultant",
        "solutions architect",
        "solution architect",
        "technical project manager",
    ],
}

# SESSION 
def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)

    return session

# TEXT CLEANING 
def clean_text(text):
    """Normalize whitespace and remove unnecessary spacing"""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# JOB ID 
def generate_job_id(url):
    """Create a stable ID from the vacancy URL"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

# DOWNLOAD PAGE 
def get_page(session, url, delay=REQUEST_DELAY):
    """
    Download a page while keeping requests deliberately slow
    """
    time.sleep(delay)

    response = session.get(
        url, timeout=30
    )
    response.raise_for_status()

    return response.text

# URL NORMALIZATION 
def normalize_url(url):
    """Normalize a URL by removing fragments and query strings"""
    parsed = urlparse(url)

    clean = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    )

    return clean.rstrip("/")

# JOB URL DETECTION 
def is_probable_job_url(url):
    """
    Determine whether a URL looks like an individual
    myjobmag vacancy
    """
    url = normalize_url(url)

    parsed = urlparse(url)

    if parsed.netloc not in(
        "www.myjobmag.co.ke",
        "myjobmag.co.ke"
    ):
        return False

    path = parsed.path.strip("/")
    parts = path.split("/")
    # Expected structure 
    # /jobs/some-job-title 

    if len(parts) != 2:
        return False

    if parts[0].lower() != "jobs":
        return False

    slug = parts[1].lower()
    excluded = {
        "jobs",
        "students",
        "internships",
        "graduate-jobs",
        "volunteer",
        "job-alerts",
        "career-advice",
        "companies",
    }

    if slug in excluded:
        return False

    return True

# EXTRACT JOB LINKS 
def extract_job_links(html):
    """Extract probable individual vacancy URLs from a listing page"""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        full_url = urljoin(
            BASE_URL, href
        )
        full_url = normalize_url(full_url)

        if is_probable_job_url(full_url):
            links.add(full_url)
    return sorted(links)

# EXTRACT PAGINATION LINKS
def extract_pagination_links(html, current_url):
    """Find pagination URLs from a job listing page"""

    soup = BeautifulSoup(html, "html.parser")
    pagination_links = set()
    for anchor in soup.find_all("a", href=True):
        text = clean_text(anchor.get_text(
            " ", strip=True
        )).lower()

        href = anchor["href"].strip()

        full_url = normalize_url(
            urljoin(current_url, href)
        )

        if (
            text in {
                "next",
                "next page",
                "older",
                "›",
                "»"
            }
            or re.search(
                r"[?&](page|p)=\d+",
                href,
                flags=re.IGNORECASE
            )
            or re.search(
                r"/page/\d+",
                href,
                flags=re.IGNORECASE
            )):
            pagination_links.add(full_url)

        return sorted(pagination_links)

# SECTION EXTRACTION 
def extract_text_section(soup, headings):
    """Extract text following a section heading
    headings can be either a string or a list of strings
    """
    if isinstance(headings, str):
        headings = [headings]

    for heading in headings:
        heading_node = soup.find(
            lambda tag:
            tag.name in ["h2", "h3", "h4", "strong"]
            and heading.lower()
            in tag.get_text(" ", strip=True).lower()
        )
        if not heading_node:
            continue
        collected = []

        for sibling in heading_node.find_all_next():
            if sibling == heading_node:
                continue
            text = sibling.get_text(" ", strip=True)

            if text:
                collected.append(text)

            if len(" ".join(collected)) > 5000:
                break

        result = clean_text(" ".join(collected))

        if result:
            return result

    return ""

# FIELD EXTRACTION 
def extract_labeled_value(text, labels):
    """Extract a value following labels such as Location:, Job Type:, Salary:"""
    if isinstance(labels, str):
        labels = [labels]

    for label in labels:
        pattern = (
            rf"{re.escape(label)}"
            rf"\s*[:\-]\s*"
            rf"(.{{2,150}}?)"
            rf"(?=\s+(?:"
            rf"Location|Job Type|Industry|"
            rf"Deadline|Qualifications|"
            rf"Requirements|Salary|"
            rf"Experience|Education"
            rf")\s*[:\-]|\s*$)"
        )

        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group(1))

    return ""

# JOB PAGE PARSER 
def parse_job_page(html, url):
    """Parse an individual MyJobMag vacancy"""
    soup = BeautifulSoup(html, "html.parser")

    # Title 
    title = ""
    h1 = soup.find("h1")

    if h1:
        title = clean_text(h1.get_text(" ", strip=True))

    # Full page text 
    page_text = clean_text(
        soup.get_text(" ", strip=True)
    )

    # Company 
    company = ""
    company_patterns = [
        r"\bat\s+(.+?)(?:\s+\||\s+is hiring|\s+is looking|$)",
        r"bcomapny\s*[:\-]\s*(.+?)(?:\s+\||$)",
    ]

    for pattern in company_patterns:
        match = re.search(
            pattern, page_text, flags=re.IGNORECASE
        )

        if match:
            company = clean_text(match.group(1))
            break

    # DATE POSTED

    date_posted = ""

    date_patterns = [
        r"\b(\d{1,2}\s+\w+\s+\d{4})\b",
        r"\b(\w+\s+\d{1,2},\s+\d{4})\b",
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            page_text,
            flags=re.IGNORECASE
        )

        if match:

            date_posted = match.group(1)

            break

    # LOCATION

    location = extract_labeled_value(
        page_text,
        [
            "Location",
            "Job Location"
        ]
    )

    # Fallback
    if not location:

        location_match = re.search(
            r"(?:Location|Job Location)"
            r"\s*[:\-]?\s*"
            r"([A-Za-z ,/&\-\(\)]+)",
            page_text,
            flags=re.IGNORECASE
        )

        if location_match:

            location = clean_text(
                location_match.group(1)
            )

    # JOB TYPE

    employment_type = extract_labeled_value(
        page_text,
        [
            "Job Type",
            "Employment Type"
        ]
    )

    # INDUSTRY

    industry = extract_labeled_value(
        page_text,
        "Industry"
    )

    # EXPERIENCE

    experience = ""

    experience_patterns = [

        r"\b(\d+\+?\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+of)?"
        r"(?:\s+relevant)?"
        r"\s+experience)\b",

        r"\b(\d+\+?\s*"
        r"(?:years?|yrs?))\b",
    ]

    for pattern in experience_patterns:

        match = re.search(
            pattern,
            page_text,
            flags=re.IGNORECASE
        )

        if match:

            experience = clean_text(
                match.group(1)
            )

            break

    # EDUCATION / QUALIFICATIONS

    education = extract_text_section(
        soup,
        [
            "Qualifications",
            "Requirements",
            "Education"
        ]
    )

    # DESCRIPTION

    description = extract_text_section(
        soup,
        [
            "Job Description",
            "Description"
        ]
    )

    if not description:

        description = page_text

    # SALARY

    salary = ""

    salary_patterns = [
        r"(?:salary|pay|remuneration)"
        r"\s*[:\-]?\s*"
        r"(.{2,100})"
    ]

    for pattern in salary_patterns:

        match = re.search(
            pattern,
            page_text,
            flags=re.IGNORECASE
        )

        if match:

            salary = clean_text(
                match.group(1)
            )

            break

    # TECH CLASSIFICATION

    combined_text = clean_text(
        " ".join([
            title,
            description,
            industry,
            employment_type
        ])
    ).lower()

    tech_category = classify_tech_job(
        combined_text
    )

    is_tech_job = (
        tech_category != "Non-Tech"
    )

    # RETURN

    return {

        "job_id": generate_job_id(url),
        "job_title": title,
        "company": company,
        "job_description": description,
        "location": location,
        "industry": industry,
        "job_field": "",
        "date_posted": date_posted,
        "employment_type": employment_type,
        "education_required": education,
        "experience_required": experience,
        "salary": salary,
        "is_tech_job": int(
            is_tech_job
        ),
        "tech_category": tech_category,
        "source": "MyJobMag Kenya",
        "vacancy_url": url,
        "scraped_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# TECH CLASSIFIER

def classify_tech_job(text):
    """
    Assign a technology category based on keyword matches.
    """

    scores = {}

    for category, keywords in TECH_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:

                # Job title/role keywords should have more weight.
                score += 1

        scores[category] = score

    best_category = max(
        scores,
        key=scores.get
    )

    best_score = scores[
        best_category
    ]

    if best_score == 0:
        return "Non-Tech"

    return best_category


# DISCOVER JOBS

def discover_jobs(
    session,
    start_url,
    max_pages=MAX_PAGES,
    max_jobs=MAX_JOBS
):
    """
    Crawl listing pages and collect individual job URLs.
    """

    visited_pages = set()

    discovered_jobs = set()

    pages_to_visit = [
        start_url
    ]

    page_number = 0

    while (
        pages_to_visit
        and page_number < max_pages
        and len(discovered_jobs) < max_jobs
    ):

        current_url = pages_to_visit.pop(0)

        current_url = normalize_url(
            current_url
        )

        if current_url in visited_pages:
            continue

        visited_pages.add(
            current_url
        )

        page_number += 1

        print()
        print(
            f"Listing page "
            f"{page_number}/{max_pages}"
        )

        print(
            current_url
        )

        try:

            html = get_page(
                session,
                current_url
            )

        except Exception as e:

            print(
                f"Failed listing page: {e}"
            )

            continue

        # JOB LINKS

        job_links = extract_job_links(
            html
        )

        before = len(
            discovered_jobs
        )

        for job_url in job_links:

            if len(
                discovered_jobs
            ) >= max_jobs:
                break

            discovered_jobs.add(
                job_url
            )

        added = (
            len(discovered_jobs)
            - before
        )

        print(
            f"Found {len(job_links)} "
            f"job links "
            f"(+{added} new)"
        )

        # PAGINATION

        pagination = extract_pagination_links(
            html,
            current_url
        )

        for next_url in pagination:

            if next_url not in visited_pages:
                pages_to_visit.append(
                    next_url
                )

        print(
            f"Pagination links found: "
            f"{len(pagination)}"
        )

    return sorted(
        discovered_jobs
    )[:max_jobs]


# SCRAPE JOBS

def scrape_jobs(
    max_pages=MAX_PAGES,
    max_jobs=MAX_JOBS
):

    session = create_session()

    print("=" * 70)
    print("MYJOBMAG KENYA TECH JOB COLLECTOR")
    print("=" * 70)

    # DISCOVER

    print()
    print("STEP 1: Discovering job vacancies...")

    job_links = discover_jobs(
        session,
        START_URL,
        max_pages=max_pages,
        max_jobs=max_jobs
    )

    print()
    print(
        f"Total unique vacancies discovered: "
        f"{len(job_links)}"
    )

    # SCRAPE

    print()
    print("STEP 2: Scraping individual vacancies...")

    records = []

    for i, url in enumerate(
        job_links,
        start=1
    ):

        print()
        print(
            f"[{i}/{len(job_links)}]"
        )

        print(url)

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

            status = (
                "TECH"
                if record["is_tech_job"] == 1
                else "NON-TECH"
            )

            print(
                f"    [{status}] "
                f"{record['job_title']}"
            )

            if record["tech_category"] != "Non-Tech":

                print(
                    f"    Category: "
                    f"{record['tech_category']}"
                )

        except Exception as e:

            print(
                f"    FAILED: {e}"
            )

    # DATAFRAME

    df = pd.DataFrame(
        records
    )

    # REMOVE DUPLICATES

    if not df.empty:

        df = df.drop_duplicates(
            subset=["job_id"]
        )

        df = df.reset_index(
            drop=True
        )

    return df


# SAVE DATA

def save_dataset(df):

    os.makedirs(
        os.path.dirname(
            OUTPUT_PATH
        ),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print(
        f"Dataset saved to: "
        f"{OUTPUT_PATH}"
    )


# MAIN

if __name__ == "__main__":

    df = scrape_jobs(
        max_pages=MAX_PAGES,
        max_jobs=MAX_JOBS
    )

    save_dataset(
        df
    )

    print()
    print("=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)

    print(
        f"Total records: {len(df)}"
    )

    if not df.empty:
        tech_count = int(
            df["is_tech_job"].sum()
        )

        nontech_count = (
            len(df)
            - tech_count
        )

        print(f"Tech jobs: {tech_count}")

        print(f"Non-tech jobs: {nontech_count}")
        print()
        print("TECH JOB CATEGORIES")
        print(
            df[
                df["is_tech_job"] == 1
            ]["tech_category"]
            .value_counts()
            .to_string()
        )

        print()
        print("SAMPLE RECORDS")
        print(
            df[[
                    "job_title",
                    "company",
                    "location",
                    "tech_category",
                    "date_posted"
                ]
            ].head(10).to_string(
                index=False
            )
        )

    else:
        print("No records were collected.")