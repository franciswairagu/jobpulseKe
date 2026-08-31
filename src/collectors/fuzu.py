"""
Fuzu (fuzu.com) — pan-African job board.

FIX (v2): v1's `a.job-card` / `div.job-listing-item` selectors returned
0 records — guessed wrapper classes were wrong. Switched to anchor-first
extraction keyed off `/jobs/<slug>` detail-page URLs (Fuzu's URL
pattern), with the original selectors kept as a first-try fast path in
case they still work for you.
"""
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record
from utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none
from config import BROAD_TECH_SEARCH_TERMS

BASE_URL = "https://www.fuzu.com"
SEARCH_PATH = "/jobs"
TECH_QUERY_TERMS = BROAD_TECH_SEARCH_TERMS

CARD_SELECTOR_CANDIDATES = [
    "a.job-card",
    "div.job-listing-item",
    "article.job-card",
    "div[class*='JobCard']",
]
JOB_LINK_PATTERNS = [r"/jobs/[a-z0-9-]+-\d+", r"/jobs/[a-z0-9-]{10,}"]


class FuzuScraper(BaseScraper):
    source_name = "fuzu"

    def scrape(self, max_pages=15, query_terms=None, **kwargs):
        query_terms = query_terms or TECH_QUERY_TERMS
        records = []
        seen_ids = set()

        for term in query_terms:
            for page in range(1, max_pages + 1):
                params = {"q": term, "page": page}
                try:
                    resp = self.get(f"{BASE_URL}{SEARCH_PATH}", params=params)
                except Exception as e:
                    self.logger.warning(f"'{term}' page {page} failed: {e}")
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards, matched_sel = select_first_nonempty(soup, CARD_SELECTOR_CANDIDATES)

                parsed_this_page = 0
                if cards:
                    for card in cards:
                        rec = self._parse_card(card)
                        if rec and rec["source_job_id"] not in seen_ids:
                            seen_ids.add(rec["source_job_id"])
                            records.append(rec)
                            parsed_this_page += 1
                else:
                    for a, container in anchor_based_cards(soup, JOB_LINK_PATTERNS):
                        rec = self._parse_anchor(a, container)
                        if rec and rec["source_job_id"] not in seen_ids:
                            seen_ids.add(rec["source_job_id"])
                            records.append(rec)
                            parsed_this_page += 1

                if parsed_this_page == 0:
                    self.debug_dump(resp.text, tag=f"{term}_p{page}")
                    break

                self.polite_sleep()
        return records

    def _parse_card(self, card):
        href = card.get("href") if card.name == "a" else (
            card.find("a", href=True)["href"] if card.find("a", href=True) else None
        )
        if not href:
            return None
        return self._build(href, card)

    def _parse_anchor(self, a, container):
        return self._build(a.get("href"), container)

    def _build(self, href, card):
        if not href:
            return None
        vacancy_url = href if href.startswith("http") else BASE_URL + href
        source_job_id = vacancy_url.rstrip("/").split("/")[-1]

        title = card.select_one("[class*='title']")
        company = card.select_one("[class*='company']")
        location = card.select_one("[class*='location']")
        deadline = card.select_one("[class*='deadline']")

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=text_or_none(title),
            company=text_or_none(company),
            location=text_or_none(location),
            application_deadline=text_or_none(deadline),
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = FuzuScraper()
    scraper.run_and_save("output/fuzu.csv", max_pages=5)
