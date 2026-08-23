import re
import time
import hashlib
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.myjobmag.co.ke"
START_URL = f"{BASE_URL}/"

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
    session.headers.update(HEADERS)
    return session

def clean_text(text):
    """Normalize whitespace"""
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()

def generate_job_id(url):
    """Create a stable ID from the vacancy URL"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

def get_page(session, url, delay=1.5):
    """
    Download a page while keeping requests deliberately slow
    """
    time.sleep(delay)

    response = session.get(
        url, timeout=30
    )
    response.raise_for_status()

    return response.text

def extract_job_links(html):
    """Extract job-detail links from MyJobMag jobs page"""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if "/jobs/" not in href:
            continue

        full_url = urljoin(BASE_URL, href)

        # Remove URL fragments 
        full_url = full_url.split("#")[0]
        links.add(full_url)

    return sorted(links)

def extract_text_section(soup, heading):
    """Try to extract text following a section heading"""
    heading_node = soup.find(
        lambda tag:
        tag.name in ["h2", "h3", "h4", "strong"]
        and heading.lower() in tag.get_text(" ", strip=True).lower()
    )

    if not heading_node:
        return ""

    collected = []

    for sibling in heading_node.find_all_next():
        if sibling == heading_node:
            continue
        text = sibling.get_text(" ", strip=True)

        if text:
            collected.append(text)

        # Avoid collecting the entire page 
        if len(" ".join(collected)) > 5000:
            break

    return clean_text(" ".join(collected))

def parse_job_page(html, url):
    """Extract fields from an individaul MyJobMag job page"""
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

    # first attempt: title/page structure 
    company_match = re.search(
        r"\bat\s+(.+?)(?:\s+\||$)",
        page_text,
        flags=re.IGNORECASE
    )

    if company_match:
        company = clean_text(company_match.group(1))

    # Date 
    date_posted = ""

    date_patterns = [
        r"(\d{1,2}\s+\w+\s+2026)",
        r"(\d{1,2}\s+\w+\s+\d{4})"
    ]

    for pattern in date_patterns:
        match = re.search(
            pattern, page_text
        )

        if match:
            date_posted = match.group(1)
            break

    # Location 
    location = ""
    location_match = re.search(
        r"(?.Location|Job Location)\s*[:\-]?\s"
        r"(.{2, 100}?)(?:\s+(?:Job Type|Industry|Deadline|"
        r"Qualifications|Requirements)\b|$",
        page_text,
        flags=re.IGNORECASE
    )

    if location_match:
        location = clean_text(
            location_match.group(1)
        )

    # Education 
    education = extract_text_section(
        soup, "Qualifications"
    )

    # Experience 
    experience = ""
    experience_match = re.search(
        r"(\d+\+?\s*(?:years?|yrs?"
        r"(?:\s+of)?\s+(?:relevant\s+)?experience",
        page_text,
        flags=re.IGNORECASE
    )

    if experience_match:
        experience = experience_match.group(1)

    # Description 
    description = extract_text_section(
        soup, "Job Description"
    )

    if not description:
        description = page_text

    # Return Record 
    return {
        "job_id": generate_job_id(url),
        "job_title": title,
        "company": company,
        "job_description": description,
        "location": location,
        "industry": "",
        "job_field": "",
        "date_posted": date_posted,
        "employment_type": "",
        "education_required": education,
        "experience_required": experience,
        "salary": "",
        "source": "MyJobMag Kenya",
        "vacancy_url": url,
        "scraped_at": datetime.utcnow().isoformat()
    }

def scrape_jobs(max_jobs=50):
    """Main scraper"""
    session = create_session()
    print("Downloading MyJobMag jobs page...")

    html = get_page(
        session, START_URL
    )

    job_links = extract_job_links(html)

    print(f"Found {len(job_links)} job links.")
    job_links = job_links[:max_jobs]

    records = []

    for i, url in enumerate(job_links, start=1):
        print(f"[{i}/{len(job_links)}] {url}")
        try:
            html = get_page(
                session, url
            )

            record = parse_job_page(
                html, url
            )
            records.append(record)

        except Exception as e:
            print(f"Failed: {url}")
            print(f"Reason: {e}")

    df = pd.DataFrame(records)

    return df

if __name__ == "__main__":
    df = scrape_jobs(max_jobs=50)

    output_path = (
        "data/raw/"
        "myjobmag_jobs_raw.csv"
    )

    df.to_csv(
        output_path, index=False
    )

    print()
    print("=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Records collected: {len(df)}")
    print(f"Saved to: {output_path}")
    print()
    print(df.head())