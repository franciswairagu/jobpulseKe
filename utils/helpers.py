"""
Shared helpers: building a schema-conformant record, cleaning text,
guessing work_mode/country/tech_category/salary+currency from free text.
These are intentionally rule-based (regex/keyword) rather than ML so they
run instantly with zero dependencies beyond stdlib + re.
"""
import hashlib
import re
from datetime import datetime, timezone

from config import (
    SCHEMA_COLUMNS, AFRICAN_COUNTRIES, TECH_KEYWORDS, TECH_CATEGORY_MAP,
)

CURRENCY_PATTERNS = {
    "KES": [r"KES", r"Ksh", r"Kshs"],
    "NGN": [r"NGN", r"₦", r"Naira"],
    "GHS": [r"GHS", r"GHC", r"Cedis"],
    "ZAR": [r"ZAR", r"R\s?\d", r"Rand"],
    "UGX": [r"UGX", r"Ush"],
    "TZS": [r"TZS", r"Tsh"],
    "EGP": [r"EGP", r"E£"],
    "USD": [r"USD", r"US\$", r"\$"],
    "EUR": [r"EUR", r"€"],
    "GBP": [r"GBP", r"£"],
}

SALARY_RANGE_RE = re.compile(
    r"([\d,]{3,})\s*(?:-|to|–)\s*([\d,]{3,})", re.IGNORECASE
)
SALARY_SINGLE_RE = re.compile(r"([\d,]{3,})")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(text):
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def make_job_id(source, source_job_id, vacancy_url=None):
    """Stable hash so re-scraping the same posting doesn't create duplicates."""
    basis = f"{source}|{source_job_id or vacancy_url or ''}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def guess_country(text_blobs):
    """text_blobs: list of strings (location, description, title) to search."""
    haystack = " ".join([t for t in text_blobs if t]).lower()
    for country in AFRICAN_COUNTRIES:
        if country.lower() in haystack:
            return country
    return None


def guess_work_mode(text_blobs):
    haystack = " ".join([t for t in text_blobs if t]).lower()
    if "hybrid" in haystack:
        return "hybrid"
    if "remote" in haystack or "work from home" in haystack or "wfh" in haystack:
        return "remote"
    if "on-site" in haystack or "onsite" in haystack or "on site" in haystack:
        return "onsite"
    return "unknown"


def guess_remote_scope(text_blobs):
    """Only meaningful when work_mode == remote. e.g. 'Africa-only', 'Global', 'Country-only'."""
    haystack = " ".join([t for t in text_blobs if t]).lower()
    if "remote" not in haystack:
        return None
    if any(k in haystack for k in ["worldwide", "global", "anywhere"]):
        return "Global"
    if "africa" in haystack:
        return "Africa-wide"
    return "Country-only"


def is_tech_job(text_blobs):
    haystack = " ".join([t for t in text_blobs if t]).lower()
    return any(kw in haystack for kw in TECH_KEYWORDS)


def classify_tech_category(text_blobs):
    haystack = " ".join([t for t in text_blobs if t]).lower()
    for category, keywords in TECH_CATEGORY_MAP.items():
        if any(kw in haystack for kw in keywords):
            return category
    return "Other Tech" if is_tech_job(text_blobs) else None


def guess_currency(text):
    if not text:
        return None
    for currency, patterns in CURRENCY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return currency
    return None


def clean_salary(text):
    """Return the raw salary string cleaned up (keep as string; modeling
    stage can parse ranges/numerics later — free-text money formats vary
    too much across sources to safely coerce to a single number here)."""
    if not text:
        return None
    text = clean_text(text)
    # drop obvious placeholder junk
    if text and text.lower() in {"n/a", "not specified", "-", "negotiable"}:
        return text
    return text


def build_record(
    source,
    source_job_id=None,
    job_title=None,
    company=None,
    job_description=None,
    location=None,
    country=None,
    work_mode=None,
    remote_scope=None,
    job_field=None,
    industry=None,
    employment_type=None,
    experience_required=None,
    education_required=None,
    salary=None,
    currency=None,
    date_posted=None,
    application_deadline=None,
    tech_category=None,
    vacancy_url=None,
):
    """Assemble a dict with EXACTLY the SCHEMA_COLUMNS keys, filling
    inferred fields (country/work_mode/tech_category/currency) when the
    caller didn't already resolve them."""
    text_blobs = [job_title, job_description, location]

    if country is None:
        country = guess_country(text_blobs)
    if work_mode is None:
        work_mode = guess_work_mode(text_blobs)
    if remote_scope is None:
        remote_scope = guess_remote_scope(text_blobs)
    if tech_category is None:
        tech_category = classify_tech_category(text_blobs)
    if currency is None and salary:
        currency = guess_currency(salary)

    record = {
        "job_id": make_job_id(source, source_job_id, vacancy_url),
        "source": source,
        "source_job_id": source_job_id,
        "job_title": clean_text(job_title),
        "company": clean_text(company),
        "job_description": clean_text(job_description),
        "location": clean_text(location),
        "country": country,
        "work_mode": work_mode,
        "remote_scope": remote_scope,
        "job_field": clean_text(job_field),
        "industry": clean_text(industry),
        "employment_type": clean_text(employment_type),
        "experience_required": clean_text(experience_required),
        "education_required": clean_text(education_required),
        "salary": clean_salary(salary),
        "currency": currency,
        "date_posted": clean_text(date_posted),
        "application_deadline": clean_text(application_deadline),
        "tech_category": tech_category,
        "vacancy_url": vacancy_url,
        "scraped_at": now_iso(),
    }
    # Safety net: guarantee column order/completeness even if a key was missed
    return {col: record.get(col) for col in SCHEMA_COLUMNS}
