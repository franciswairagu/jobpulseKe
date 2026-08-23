import os
import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://www.myjobmag.co.ke"

# MyJobMag uses /jobs for the first page and
# /jobs/page/2, /jobs/page/3, etc.
START_PAGE = 1
MAX_PAGES = 20

# Maximum individual vacancy URLs to collect
MAX_JOBS = 500

# Delay between requests
REQUEST_DELAY = 1.5

OUTPUT_PATH = "data/raw/myjobmag_jobs_raw.csv"

HEADERS = {
    "User-Agent": (
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
    "Connection": "keep-alive",
}


# ============================================================
# TECH CLASSIFICATION
# ============================================================
#
# IMPORTANT:
#
# We intentionally DO NOT classify based on arbitrary words
# appearing anywhere in the description.
#
# Strong signals:
#   1. Job title
#   2. MyJobMag job field
#   3. MyJobMag industry
#
# Description is only used as a secondary signal when there
# are strong technical terms.
#
# ============================================================


# ------------------------------------------------------------
# Strong title patterns
# ------------------------------------------------------------

TECH_TITLE_PATTERNS = {

    "Software Development": [
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
        r"\bpython\s+developer\b",
        r"\bjava\s+developer\b",
        r"\bphp\s+developer\b",
        r"\bjavascript\s+developer\b",
        r"\breact\s+developer\b",
        r"\bnode(?:\.js|js)?\s+developer\b",
        r"\bflutter\s+developer\b",
        r"\bprogrammer\b",
    ],

    "Data & AI": [
        r"\bdata\s+scientist\b",
        r"\bdata\s+analyst\b",
        r"\bdata\s+engineer\b",
        r"\bdata\s+science\b",
        r"\bdata\s+engineering\b",
        r"\bmachine\s+learning\b",
        r"\bartificial\s+intelligence\b",
        r"\bai\s+engineer\b",
        r"\bai\s+developer\b",
        r"\bdeep\s+learning\b",
        r"\bnatural\s+language\s+processing\b",
        r"\bcomputer\s+vision\b",
        r"\bbi\s+analyst\b",
        r"\bbusiness\s+intelligence\b",
        r"\banalytics\s+engineer\b",
    ],

    "Cybersecurity": [
        r"\bcyber\s*security\b",
        r"\bcybersecurity\b",
        r"\binformation\s+security\b",
        r"\bsecurity\s+analyst\b",
        r"\bsecurity\s+engineer\b",
        r"\bsecurity\s+specialist\b",
        r"\bpenetration\s+tester\b",
        r"\bpenetration\s+testing\b",
        r"\bethical\s+hacker\b",
        r"\bsoc\s+analyst\b",
    ],

    "Cloud & DevOps": [
        r"\bdevops\b",
        r"\bdevops\s+engineer\b",
        r"\bcloud\s+engineer\b",
        r"\bcloud\s+architect\b",
        r"\bcloud\s+computing\b",
        r"\bcloud\s+infrastructure\b",
        r"\bsite\s+reliability\s+engineer\b",
        r"\bsre\s+engineer\b",
    ],

    "Networking": [
        r"\bnetwork\s+engineer\b",
        r"\bnetwork\s+administrator\b",
        r"\bnetwork\s+technician\b",
        r"\bnetwork\s+architect\b",
        r"\bnetworking\s+engineer\b",
        r"\bnetwork\s+security\b",
        r"\btelecommunications\s+engineer\b",
    ],

    "IT & Systems": [
        r"\bit\s+officer\b",
        r"\bit\s+manager\b",
        r"\bit\s+administrator\b",
        r"\bit\s+support\b",
        r"\bit\s+technician\b",
        r"\binformation\s+technology\s+(officer|manager|specialist)\b",
        r"\btechnical\s+support\b",
        r"\bhelp\s*desk\b",
        r"\bsystems?\s+administrator\b",
        r"\bsystems?\s+engineer\b",
        r"\bsystem\s+administrator\b",
        r"\bdatabase\s+administrator\b",
        r"\bdatabase\s+engineer\b",
        r"\bict\s+(officer|manager|technician|specialist)\b",
    ],

    "QA & Testing": [
        r"\bqa\s+(engineer|analyst|tester)\b",
        r"\bquality\s+assurance\s+(engineer|analyst)\b",
        r"\bsoftware\s+tester\b",
        r"\btest\s+engineer\b",
        r"\btest\s+automation\b",
        r"\bautomation\s+tester\b",
    ],

    "Product & UX": [
        r"\bproduct\s+manager\b",
        r"\btechnical\s+product\s+manager\b",
        r"\bproduct\s+owner\b",
        r"\btechnical\s+product\b",
        r"\bux\s+designer\b",
        r"\bui\s+designer\b",
        r"\bui/ux\b",
        r"\bux/ui\b",
        r"\buser\s+experience\s+designer\b",
        r"\bsolutions?\s+architect\b",
        r"\btechnical\s+consultant\b",
        r"\btechnical\s+project\s+manager\b",
    ],
}


# ------------------------------------------------------------
# Strongly tech-related MyJobMag fields
# ------------------------------------------------------------

TECH_FIELDS = {
    "ict / computer",
    "data, business analysis and ai",
    "product management",
}


# ------------------------------------------------------------
# Strongly tech-related industries
# ------------------------------------------------------------

TECH_INDUSTRIES = {
    "ict / telecommunication",
    "internet / e-commerce",
    "blockchain",
}


# ------------------------------------------------------------
# Explicit non-tech title patterns
#
# These are deliberately conservative.
# ------------------------------------------------------------

NON_TECH_TITLE_PATTERNS = [
    r"\bdriver\b",
    r"\btruck\s+driver\b",
    r"\btractor\s+driver\b",
    r"\bteacher\b",
    r"\bteaching\b",
    r"\blecturer\b",
    r"\bnurse\b",
    r"\bdoctor\b",
    r"\baccountant\b",
    r"\baccounting\b",
    r"\bsales\s+(representative|executive|officer)\b",
    r"\bmarketing\s+(officer|executive|manager)\b",
    r"\bhr\s+(officer|manager|assistant)\b",
    r"\bhuman\s+resource\b",
    r"\bprocurement\b",
    r"\bstore\s+keeper\b",
    r"\bstorekeeper\b",
    r"\bsecurity\s+guard\b",
    r"\bwaiter\b",
    r"\bchef\b",
    r"\bcook\b",
    r"\bhousekeeper\b",
    r"\bcleaner\b",
    r"\bmechanic\b",
    r"\belectrician\b",
    r"\bplumber\b",
    r"\bwelder\b",
]


# ============================================================
# SESSION
# ============================================================

def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)

    return session


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(text):
    """
    Normalize whitespace.
    """

    if not text:
        return ""

    text = text.replace("\xa0", " ")

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def normalize_lower(text):
    return clean_text(text).lower()


# ============================================================
# JOB ID
# ============================================================

def generate_job_id(url):
    """
    Stable ID based on vacancy URL.
    """

    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# URL UTILITIES
# ============================================================

def normalize_url(url):
    """
    Remove query parameters/fragments.
    """

    parsed = urlparse(url)

    normalized = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path}"
    )

    return normalized.rstrip("/")


def is_myjobmag_job_url(url):
    """
    Determine whether URL looks like an individual
    MyJobMag vacancy.
    """

    url = normalize_url(url)

    parsed = urlparse(url)

    if parsed.netloc not in {
        "www.myjobmag.co.ke",
        "myjobmag.co.ke",
    }:
        return False

    parts = parsed.path.strip("/").split("/")

    # Current MyJobMag individual vacancy URLs are generally:
    #
    # /jobs/job-title-slug
    #
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


# ============================================================
# HTTP
# ============================================================

def get_page(session, url):
    """
    Download a page.
    """

    time.sleep(REQUEST_DELAY)

    response = session.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


# ============================================================
# LISTING PAGE URL
# ============================================================

def get_listing_url(page_number):
    """
    MyJobMag:
        page 1 -> /jobs
        page 2 -> /jobs/page/2
        page 3 -> /jobs/page/3
    """

    if page_number <= 1:
        return f"{BASE_URL}/jobs"

    return f"{BASE_URL}/jobs/page/{page_number}"


# ============================================================
# EXTRACT JOB LINKS
# ============================================================

def extract_job_links(html):
    """
    Extract individual vacancy links from a MyJobMag
    listing page.

    We look for actual /jobs/<slug> links and ignore
    navigation/category URLs.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = set()

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = anchor.get("href", "").strip()

        if not href:
            continue

        full_url = normalize_url(
            urljoin(
                BASE_URL,
                href,
            )
        )

        if is_myjobmag_job_url(
            full_url
        ):
            links.add(full_url)

    return sorted(links)


# ============================================================
# FIND LABELLED VALUE
# ============================================================

def extract_label_value(
    soup,
    labels,
):
    """
    Search page elements for labelled metadata.

    Handles examples such as:

        Job Type Full Time
        Qualification BA/BSc/HND
        Experience 2 - 3 years
        Location Nairobi
        Job Field ICT / Computer
        Salary Range KSh 50,000 - KSh 80,000/month
    """

    if isinstance(
        labels,
        str,
    ):
        labels = [labels]

    label_set = {
        normalize_lower(label)
        for label in labels
    }

    # --------------------------------------------------------
    # Look through relatively small text elements.
    # --------------------------------------------------------

    for tag in soup.find_all(
        ["div", "li", "p", "span", "td"],
    ):

        text = clean_text(
            tag.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        lower = text.lower()

        for label in label_set:

            if not lower.startswith(label):
                continue

            remainder = text[len(label):].strip()

            remainder = remainder.lstrip(
                ":-"
            ).strip()

            if remainder:
                return clean_text(
                    remainder
                )

    return ""


# ============================================================
# EXTRACT BREADCRUMB METADATA
# ============================================================

def extract_job_field_and_industry(soup):
    """
    MyJobMag job pages expose metadata such as:

        View Jobs in Consulting
        View Jobs at Company

    We also inspect visible text for "Job Field".
    """

    job_field = ""
    industry = ""

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    # --------------------------------------------------------
    # Job Field
    # --------------------------------------------------------

    field_match = re.search(
        r"Job Field\s*[:\-]?\s*"
        r"(.{2,120}?)"
        r"(?=\s+(?:Salary|Method of Application|"
        r"Job Type|Qualification|Experience|Location)"
        r"\b|$)",
        page_text,
        flags=re.IGNORECASE,
    )

    if field_match:

        job_field = clean_text(
            field_match.group(1)
        )

    # --------------------------------------------------------
    # Industry from "View Jobs in ..."
    # --------------------------------------------------------

    industry_match = re.search(
        r"View Jobs in\s+"
        r"(.{2,100}?)"
        r"\s*/\s*View Jobs at",
        page_text,
        flags=re.IGNORECASE,
    )

    if industry_match:

        industry = clean_text(
            industry_match.group(1)
        )

    return job_field, industry


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_section(
    soup,
    headings,
    max_chars=8000,
):
    """
    Extract text after a heading.

    This is deliberately limited so that navigation/footer
    content does not become the job description.
    """

    if isinstance(
        headings,
        str,
    ):
        headings = [headings]

    for heading in headings:

        target = soup.find(
            lambda tag:
            tag.name in {
                "h2",
                "h3",
                "h4",
                "strong",
            }
            and normalize_lower(
                tag.get_text(
                    " ",
                    strip=True,
                )
            ) == normalize_lower(
                heading
            )
        )

        if not target:
            continue

        collected = []

        for element in target.find_all_next():

            # Stop at another major heading
            if (
                element.name in {
                    "h2",
                    "h3",
                }
                and element != target
            ):
                break

            text = clean_text(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                collected.append(text)

            if len(
                " ".join(collected)
            ) >= max_chars:

                break

        result = clean_text(
            " ".join(collected)
        )

        if result:

            return result[:max_chars]

    return ""


# ============================================================
# DESCRIPTION EXTRACTION
# ============================================================

def extract_description(soup):
    """
    Try several known/likely MyJobMag content structures.

    Falls back to the main content area rather than the
    entire page, avoiding navigation where possible.
    """

    # First try explicit sections
    description = extract_section(
        soup,
        [
            "Job Description",
            "Description",
            "About the Role",
            "Job Summary",
        ],
        max_chars=12000,
    )

    if description:
        return description

    # --------------------------------------------------------
    # Try common content containers
    # --------------------------------------------------------

    candidates = [
        soup.find(
            id=re.compile(
                r"job.*description|description",
                re.IGNORECASE,
            )
        ),
        soup.find(
            class_=re.compile(
                r"job.*description|description",
                re.IGNORECASE,
            )
        ),
    ]

    for candidate in candidates:

        if candidate:

            text = clean_text(
                candidate.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) > 100:

                return text[:12000]

    # --------------------------------------------------------
    # Last resort: body text, but remove obvious navigation
    # --------------------------------------------------------

    body = soup.body

    if not body:
        return ""

    for unwanted in body.find_all(
        [
            "nav",
            "header",
            "footer",
            "script",
            "style",
            "form",
        ]
    ):
        unwanted.decompose()

    text = clean_text(
        body.get_text(
            " ",
            strip=True,
        )
    )

    return text[:12000]


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_posted_date(soup):
    """
    Extract MyJobMag's Posted date.
    """

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    patterns = [

        r"Posted\s*:\s*"
        r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",

        r"Posted\s+"
        r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",

        r"\b(\d{1,2}\s+"
        r"[A-Za-z]{3,9}\s+\d{4})\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            page_text,
            flags=re.IGNORECASE,
        )

        if match:

            return clean_text(
                match.group(1)
            )

    return ""


# ============================================================
# DEADLINE EXTRACTION
# ============================================================

def extract_deadline(soup):
    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    patterns = [
        r"Deadline\s*:\s*"
        r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",

        r"Deadline\s+"
        r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            page_text,
            flags=re.IGNORECASE,
        )

        if match:

            return clean_text(
                match.group(1)
            )

    return ""


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience(text):

    patterns = [

        r"\b\d+\s*-\s*\d+\s+years?\b",

        r"\b\d+\+?\s+years?\b",

        r"\b\d+\+?\s+yrs?\b",

        r"\bminimum\s+\d+\s+years?\b",
    ]

    matches = []

    for pattern in patterns:

        found = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        matches.extend(
            found
        )

    if not matches:
        return ""

    # Keep unique matches
    unique = []

    for match in matches:

        match = clean_text(
            match
        )

        if match.lower() not in {
            x.lower()
            for x in unique
        }:

            unique.append(match)

    return "; ".join(
        unique[:5]
    )


# ============================================================
# TECH CLASSIFICATION
# ============================================================

def classify_tech_job(
    title,
    job_field,
    industry,
    description,
):
    """
    Conservative tech classification.

    Priority:

        1. Explicit non-tech title
        2. Strong tech title
        3. MyJobMag job field
        4. MyJobMag industry
        5. Strong technical phrase in description

    A generic word such as "data", "system", "cloud", etc.
    appearing somewhere in a page is NOT enough.
    """

    title_clean = normalize_lower(
        title
    )

    field_clean = normalize_lower(
        job_field
    )

    industry_clean = normalize_lower(
        industry
    )

    description_clean = normalize_lower(
        description
    )

    # --------------------------------------------------------
    # 1. Explicitly non-tech title
    # --------------------------------------------------------

    for pattern in NON_TECH_TITLE_PATTERNS:

        if re.search(
            pattern,
            title_clean,
        ):

            # We allow exceptions later if the title itself
            # contains an unmistakably technical role.
            technical_override = any(
                re.search(
                    tech_pattern,
                    title_clean,
                )
                for patterns in TECH_TITLE_PATTERNS.values()
                for tech_pattern in patterns
            )

            if not technical_override:

                return (
                    False,
                    "Non-Tech",
                    0,
                )

    # --------------------------------------------------------
    # 2. Strong title match
    # --------------------------------------------------------

    title_scores = {}

    for category, patterns in TECH_TITLE_PATTERNS.items():

        score = 0

        for pattern in patterns:

            if re.search(
                pattern,
                title_clean,
            ):

                score += 10

        title_scores[category] = score

    best_title_category = max(
        title_scores,
        key=title_scores.get,
    )

    best_title_score = title_scores[
        best_title_category
    ]

    if best_title_score > 0:

        return (
            True,
            best_title_category,
            best_title_score,
        )

    # --------------------------------------------------------
    # 3. MyJobMag field
    # --------------------------------------------------------

    if field_clean in TECH_FIELDS:

        category = "IT & Systems"

        if "data" in field_clean or "ai" in field_clean:

            category = "Data & AI"

        elif "product" in field_clean:

            category = "Product & UX"

        return (
            True,
            category,
            8,
        )

    # --------------------------------------------------------
    # 4. MyJobMag industry
    # --------------------------------------------------------

    if industry_clean in TECH_INDUSTRIES:

        if (
            "blockchain"
            in industry_clean
        ):

            category = "Data & AI"

        else:

            category = "IT & Systems"

        return (
            True,
            category,
            7,
        )

    # --------------------------------------------------------
    # 5. Description secondary signal
    #
    # Only accept very strong technical combinations.
    # --------------------------------------------------------

    description_patterns = {

        "Software Development": [
            r"\bsoftware\s+development\b",
            r"\bsoftware\s+engineering\b",
            r"\bapi\s+development\b",
            r"\bapplication\s+development\b",
            r"\breact\b",
            r"\bnode\.?js\b",
            r"\bdjango\b",
            r"\blaravel\b",
            r"\bspring\s+boot\b",
        ],

        "Data & AI": [
            r"\bmachine\s+learning\b",
            r"\bartificial\s+intelligence\b",
            r"\bdata\s+science\b",
            r"\bdata\s+engineering\b",
            r"\bdeep\s+learning\b",
            r"\bnatural\s+language\s+processing\b",
        ],

        "Cybersecurity": [
            r"\bpenetration\s+testing\b",
            r"\bcyber\s*security\b",
            r"\binformation\s+security\b",
            r"\bsecurity\s+operations\s+center\b",
        ],

        "Cloud & DevOps": [
            r"\bdevops\b",
            r"\bkubernetes\b",
            r"\bcontainerization\b",
            r"\bcloud\s+infrastructure\b",
            r"\bcontinuous\s+integration\b",
            r"\bcontinuous\s+deployment\b",
        ],

        "Networking": [
            r"\bnetwork\s+infrastructure\b",
            r"\bcisco\s+network\b",
            r"\bnetwork\s+administration\b",
            r"\blocal\s+area\s+network\b",
        ],

    }

    description_scores = {}

    for category, patterns in description_patterns.items():

        score = 0

        for pattern in patterns:

            if re.search(
                pattern,
                description_clean,
            ):

                score += 2

        description_scores[category] = score

    best_description_category = max(
        description_scores,
        key=description_scores.get,
    )

    best_description_score = description_scores[
        best_description_category
    ]

    # Require at least TWO strong description signals
    if best_description_score >= 4:

        return (
            True,
            best_description_category,
            best_description_score,
        )

    # --------------------------------------------------------
    # Otherwise: non-tech
    # --------------------------------------------------------

    return (
        False,
        "Non-Tech",
        0,
    )


# ============================================================
# PARSE JOB PAGE
# ============================================================

def parse_job_page(
    html,
    url,
):
    """
    Parse one MyJobMag vacancy.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = ""

    h1 = soup.find("h1")

    if h1:

        title = clean_text(
            h1.get_text(
                " ",
                strip=True,
            )
        )

    # --------------------------------------------------------
    # COMPANY
    # --------------------------------------------------------

    company = ""

    # MyJobMag generally has:
    # "View Jobs at COMPANY"

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    company_match = re.search(
        r"View Jobs at\s+"
        r"(.+?)"
        r"(?=\s+(?:Posted|Deadline|Save|Email|Contents)\b)",
        page_text,
        flags=re.IGNORECASE,
    )

    if company_match:

        company = clean_text(
            company_match.group(1)
        )

    # Fallback
    if not company:

        company_match = re.search(
            r"\bat\s+"
            r"(.+?)"
            r"\s*(?:\||$)",
            title,
            flags=re.IGNORECASE,
        )

        if company_match:

            company = clean_text(
                company_match.group(1)
            )

    # --------------------------------------------------------
    # FIELD / INDUSTRY
    # --------------------------------------------------------

    job_field, industry = (
        extract_job_field_and_industry(
            soup
        )
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    employment_type = extract_label_value(
        soup,
        [
            "Job Type",
        ],
    )

    education = extract_label_value(
        soup,
        [
            "Qualification",
            "Qualifications",
        ],
    )

    location = extract_label_value(
        soup,
        [
            "Location",
            "Job Location",
        ],
    )

    salary = extract_label_value(
        soup,
        [
            "Salary",
            "Salary Range",
            "Remuneration",
        ],
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = extract_description(
        soup
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    date_posted = extract_posted_date(
        soup
    )

    deadline = extract_deadline(
        soup
    )

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------

    experience = extract_experience(
        page_text
    )

    # --------------------------------------------------------
    # TECH CLASSIFICATION
    # --------------------------------------------------------

    (
        is_tech,
        tech_category,
        classification_score,
    ) = classify_tech_job(
        title=title,
        job_field=job_field,
        industry=industry,
        description=description,
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "job_id": generate_job_id(
            url
        ),

        "job_title": title,

        "company": company,

        "job_description": description,

        "location": location,

        "industry": industry,

        "job_field": job_field,

        "date_posted": date_posted,

        "application_deadline": deadline,

        "employment_type": employment_type,

        "education_required": education,

        "experience_required": experience,

        "salary": salary,

        "is_tech_job": int(
            is_tech
        ),

        "tech_category": tech_category,

        "classification_score": classification_score,

        "source": "MyJobMag Kenya",

        "vacancy_url": url,

        "scraped_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# ============================================================
# DISCOVER VACANCIES
# ============================================================

def discover_job_urls(
    session,
    start_page=START_PAGE,
    max_pages=MAX_PAGES,
    max_jobs=MAX_JOBS,
):
    """
    Crawl MyJobMag's paginated job listing pages.

    Page structure:

        /jobs
        /jobs/page/2
        /jobs/page/3
        ...
    """

    all_job_urls = set()

    empty_pages = 0

    for page_number in range(
        start_page,
        start_page + max_pages,
    ):

        if len(
            all_job_urls
        ) >= max_jobs:

            break

        listing_url = get_listing_url(
            page_number
        )

        print()
        print(
            f"LISTING PAGE "
            f"{page_number}"
        )

        print(
            listing_url
        )

        try:

            html = get_page(
                session,
                listing_url,
            )

        except Exception as e:

            print(
                f"    Failed: {e}"
            )

            continue

        job_urls = extract_job_links(
            html
        )

        before = len(
            all_job_urls
        )

        all_job_urls.update(
            job_urls
        )

        new_jobs = (
            len(all_job_urls)
            - before
        )

        print(
            f"    Found: "
            f"{len(job_urls)} links"
        )

        print(
            f"    New: "
            f"{new_jobs}"
        )

        # ----------------------------------------------------
        # Stop if pages stop producing jobs
        # ----------------------------------------------------

        if new_jobs == 0:

            empty_pages += 1

        else:

            empty_pages = 0

        if empty_pages >= 2:

            print(
                "    Two consecutive pages "
                "without new jobs. Stopping."
            )

            break

    return sorted(
        all_job_urls
    )[:max_jobs]


# ============================================================
# SCRAPE ALL JOBS
# ============================================================

def scrape_jobs():

    session = create_session()

    print("=" * 75)
    print("MYJOBMAG KENYA — TECH JOB MARKET COLLECTOR")
    print("=" * 75)

    # --------------------------------------------------------
    # DISCOVER
    # --------------------------------------------------------

    print()
    print(
        "STEP 1 — DISCOVERING VACANCIES"
    )

    job_urls = discover_job_urls(
        session=session,
        start_page=START_PAGE,
        max_pages=MAX_PAGES,
        max_jobs=MAX_JOBS,
    )

    print()
    print(
        f"Total vacancy URLs discovered: "
        f"{len(job_urls)}"
    )

    # --------------------------------------------------------
    # SCRAPE
    # --------------------------------------------------------

    print()
    print(
        "STEP 2 — SCRAPING VACANCIES"
    )

    records = []

    for index, url in enumerate(
        job_urls,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(job_urls)}]"
        )

        print(
            url
        )

        try:

            html = get_page(
                session,
                url,
            )

            record = parse_job_page(
                html,
                url,
            )

            records.append(
                record
            )

            if record[
                "is_tech_job"
            ]:

                print(
                    "    ✓ TECH"
                )

                print(
                    f"    Title: "
                    f"{record['job_title']}"
                )

                print(
                    f"    Category: "
                    f"{record['tech_category']}"
                )

            else:

                print(
                    "    - NON-TECH"
                )

                print(
                    f"    Title: "
                    f"{record['job_title']}"
                )

        except Exception as e:

            print(
                f"    ✗ FAILED: {e}"
            )

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    df = pd.DataFrame(
        records
    )

    if df.empty:

        return df

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "job_id"
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    if "date_posted" in df.columns:

        df = df.sort_values(
            by=[
                "date_posted",
                "job_title",
            ],
            ascending=[
                False,
                True,
            ],
            na_position="last",
        ).reset_index(
            drop=True
        )

    return df


# ============================================================
# SAVE
# ============================================================

def save_dataset(df):

    os.makedirs(
        os.path.dirname(
            OUTPUT_PATH
        ),
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print(
        f"Saved dataset to:"
    )

    print(
        OUTPUT_PATH
    )


# ============================================================
# REPORT
# ============================================================

def print_report(df):

    print()
    print("=" * 75)
    print("COLLECTION REPORT")
    print("=" * 75)

    if df.empty:

        print(
            "No records collected."
        )

        return

    total = len(df)

    tech = int(
        df["is_tech_job"].sum()
    )

    nontech = (
        total - tech
    )

    print(
        f"Total vacancies scraped : {total}"
    )

    print(
        f"Tech vacancies          : {tech}"
    )

    print(
        f"Non-tech vacancies      : {nontech}"
    )

    print()

    # --------------------------------------------------------
    # TECH CATEGORY
    # --------------------------------------------------------

    if tech > 0:

        print(
            "TECH CATEGORIES"
        )

        print(
            df[
                df["is_tech_job"] == 1
            ]["tech_category"]
            .value_counts()
            .to_string()
        )

    # --------------------------------------------------------
    # FIELDS
    # --------------------------------------------------------

    print()
    print(
        "JOB FIELDS"
    )

    print(
        df[
            "job_field"
        ]
        .replace(
            "",
            "Unknown"
        )
        .value_counts()
        .head(15)
        .to_string()
    )

    # --------------------------------------------------------
    # LOCATIONS
    # --------------------------------------------------------

    print()
    print(
        "LOCATIONS"
    )

    print(
        df[
            "location"
        ]
        .replace(
            "",
            "Unknown"
        )
        .value_counts()
        .head(15)
        .to_string()
    )

    # --------------------------------------------------------
    # SAMPLE TECH JOBS
    # --------------------------------------------------------

    print()
    print(
        "SAMPLE TECH JOBS"
    )

    tech_df = df[
        df["is_tech_job"] == 1
    ]

    if tech_df.empty:

        print(
            "No tech jobs detected."
        )

    else:

        columns = [
            "job_title",
            "company",
            "location",
            "job_field",
            "tech_category",
            "date_posted",
        ]

        print(
            tech_df[
                columns
            ]
            .head(15)
            .to_string(
                index=False
            )
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    df = scrape_jobs()

    save_dataset(
        df
    )

    print_report(
        df
    )