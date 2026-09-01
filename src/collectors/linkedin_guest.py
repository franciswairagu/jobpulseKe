"""
LinkedIn — IMPORTANT CAVEATS BEFORE YOU USE THIS ONE:

1. LinkedIn's Terms of Service prohibit automated scraping, and they run
   aggressive bot detection (rate limits, CAPTCHAs, IP blocks) even
   against the "guest" (logged-out) job search endpoint used below.
2. This scraper only hits the public, no-login "guest" search API
   (linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings) which returns
   partial job cards (title/company/location/link, NOT the full
   description) — LinkedIn requires a logged-in session to view full
   descriptions, and we deliberately don't attempt to authenticate here.
3. Treat this as the lowest-priority, most fragile source in the pack.
   Expect it to break or get blocked faster than the others. For a
   capstone with a hard deadline, get your other 7-8 sources solid
   first and only lean on this one if you still need volume.
4. Keep request volume low and delays generous (already configured
   more conservatively below than the other scrapers).

If this becomes unreliable, a safer alternative for LinkedIn coverage is
manually exporting a saved search's results or using LinkedIn's official
Talent/Jobs API (requires partner access) instead of scraping.
"""
import time

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record

GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

SEARCH_TERMS = ["software developer", "data analyst", "IT"]
# LinkedIn's geoId per location varies; using free-text location param
# instead of geoId keeps this simpler at the cost of some precision.
LOCATIONS = ["Kenya", "Nigeria", "South Africa", "Ghana", "Egypt", "Rwanda"]

EXTRA_DELAY = 4.0  # seconds, on top of the base class's polite_sleep


class LinkedInGuestScraper(BaseScraper):
    source_name = "linkedin"

    def scrape(self, max_pages=6, search_terms=None, locations=None, **kwargs):
        search_terms = search_terms or SEARCH_TERMS
        locations = locations or LOCATIONS
        records = []
        seen_ids = set()

        for location in locations:
            for term in search_terms:
                for page in range(max_pages):
                    start = page * 25
                    params = {
                        "keywords": term,
                        "location": location,
                        "start": start,
                        "sortBy": "DD",  # date descending = newest first
                    }
                    try:
                        resp = self.get(GUEST_API, params=params)
                    except Exception as e:
                        self.logger.warning(
                            f"{location}/{term} start={start} failed "
                            f"(likely rate-limited/blocked): {e}"
                        )
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    cards = soup.select("li")
                    if not cards:
                        break

                    for card in cards:
                        rec = self._parse_card(card, location)
                        if rec and rec["source_job_id"] not in seen_ids:
                            seen_ids.add(rec["source_job_id"])
                            records.append(rec)

                    time.sleep(EXTRA_DELAY)
                    self.polite_sleep()
        return records

    def _parse_card(self, card, location):
        link_tag = card.select_one("a.base-card__full-link") or card.find("a", href=True)
        if not link_tag or not link_tag.get("href"):
            return None
        vacancy_url = link_tag["href"].split("?")[0]
        source_job_id = vacancy_url.rstrip("/").split("-")[-1]

        title_tag = card.select_one("h3.base-search-card__title")
        company_tag = card.select_one("h4.base-search-card__subtitle")
        loc_tag = card.select_one("span.job-search-card__location")
        date_tag = card.find("time")

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=title_tag.get_text(strip=True) if title_tag else None,
            company=company_tag.get_text(strip=True) if company_tag else None,
            location=loc_tag.get_text(strip=True) if loc_tag else location,
            country=location if location != "South Africa" else "South Africa",
            date_posted=date_tag.get("datetime") if date_tag else None,
            job_description=None,  # not available without an authenticated session
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = LinkedInGuestScraper()
    scraper.run_and_save("output/linkedin.csv", max_pages=4)
