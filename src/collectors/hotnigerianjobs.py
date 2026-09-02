"""
Hot Nigerian Jobs (hotnigerianjobs.com) — large, long-running
Nigeria-specific job board. As of writing, its "Computer / AI /
Technology / IT Services" industry page alone lists 832 active
postings (https://www.hotnigerianjobs.com/industry/119/), which is
genuinely large single-board volume for this project.

VERIFIED LIVE (unlike several earlier guesses in this pack): I fetched
this page directly and confirmed the real structure, rather than
inferring it from a description. Every posting follows a consistent
text pattern that makes this unusually easy to parse reliably:

    # [Job Title](https://www.hotnigerianjobs.com/hotjobs/<id>/<slug>.html)
    Posted on <date> - hotnigerianjobs.com --- (0 comments)
    <Company> is recruiting to fill the position of: <Title>. The
    position is located in <Location>. Salary: <amount>. <requirements...>
    [Apply Now]

Some postings cover multiple roles at once ("Company Job Recruitment
(N Positions)") — those are kept as a single record with the heading
as job_title and the combined description, rather than exploded into
per-role rows, to keep the scraper simple and reliable.

CAVEAT: pagination beyond page 1 was NOT independently verified (the
fetched page didn't surface a page-2 URL in the extracted content). The
attempted pattern below (/industry/119/{page}/) is inferred from this
site's other URL conventions (e.g. location pages use a trailing
numeric page segment) but isn't confirmed. If pages beyond 1 return
0 records, check output/debug/hotnigerianjobs_*.html — it'll likely
show either a 404 or a repeat of page 1, either of which tells you
immediately how to fix the pattern.
"""
import re

from bs4 import BeautifulSoup

from src.collectors.base_scraper import BaseScraper
from src.utils.helpers import build_record
from src.utils.parsing import anchor_based_cards, text_or_none

BASE_URL = "https://www.hotnigerianjobs.com"
# "Computer / AI / Technology / IT Services" industry page
INDUSTRY_PATH = "/industry/119/"

JOB_LINK_PATTERN = [r"/hotjobs/\d+/[a-z0-9-]+\.html"]

POSTED_RE = re.compile(r"Posted on\s+([^-]+?)\s*-\s*hotnigerianjobs\.com", re.IGNORECASE)
COMMENTS_SUFFIX_RE = re.compile(r"^-{1,4}\s*\(\d+\s*comments?\)\s*", re.IGNORECASE)
COMPANY_RE = re.compile(r"^(.*?)\s+is recruiting", re.IGNORECASE)
LOCATION_RE = re.compile(r"located in\s+([^.]+)\.", re.IGNORECASE)
LOCATION_MULTI_RE = re.compile(r"positions?\s+in\s+([^:]+):", re.IGNORECASE)
SALARY_RE = re.compile(r"Salary:\s*([^.]+)\.", re.IGNORECASE)


class HotNigerianJobsScraper(BaseScraper):
    source_name = "hotnigerianjobs"

    def scrape(self, max_pages=15, **kwargs):
        records = []
        seen_urls = set()

        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"{BASE_URL}{INDUSTRY_PATH}"
            else:
                # Best-guess pagination pattern — see module docstring caveat.
                url = f"{BASE_URL}{INDUSTRY_PATH}{page - 1}/"

            try:
                resp = self.get(url)
            except Exception as e:
                self.logger.warning(f"page {page} failed: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = anchor_based_cards(soup, JOB_LINK_PATTERN, min_text_len=60)

            parsed_this_page = 0
            for a, container in cards:
                rec = self._parse(a, container)
                if rec and rec["vacancy_url"] not in seen_urls:
                    seen_urls.add(rec["vacancy_url"])
                    records.append(rec)
                    parsed_this_page += 1

            if parsed_this_page == 0:
                self.debug_dump(resp.text, tag=f"p{page}")
                break

            self.polite_sleep()
        return records

    def _parse(self, a, container):
        href = a.get("href")
        title = text_or_none(a)
        if not href or not title or len(title) < 5:
            return None
        vacancy_url = href if href.startswith("http") else BASE_URL + href
        source_job_id = href.rstrip("/").split("/")[-2] if "/hotjobs/" in href else None

        full_text = container.get_text(" ", strip=True)

        posted_match = POSTED_RE.search(full_text)
        date_posted = posted_match.group(1).strip() if posted_match else None

        # Strip the title + "Posted on..." prefix to isolate the body text
        # the company/location/salary regexes run against.
        body_text = full_text
        if posted_match:
            body_text = full_text[posted_match.end():].strip()
            body_text = COMMENTS_SUFFIX_RE.sub("", body_text).strip()

        company_match = COMPANY_RE.search(body_text)
        company = company_match.group(1).strip() if company_match else None

        location_match = LOCATION_RE.search(body_text) or LOCATION_MULTI_RE.search(body_text)
        location = location_match.group(1).strip() if location_match else None

        salary_match = SALARY_RE.search(body_text)
        salary = salary_match.group(1).strip() if salary_match else None

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=title,
            company=company,
            job_description=body_text if body_text else None,
            location=location,
            country="Nigeria",
            industry="Computer / AI / Technology / IT Services",
            salary=salary,
            date_posted=date_posted,
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = HotNigerianJobsScraper()
    scraper.run_and_save("output/hotnigerianjobs.csv", max_pages=5)
