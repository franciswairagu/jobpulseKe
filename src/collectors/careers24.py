"""
Careers24 (careers24.com) — one of South Africa's largest job boards,
with an IT/Telecommunications category. Anchor-first parsing from the
start here since this is a new addition (no live-verified selector
history to trust yet) — more resilient than guessing a wrapper class.
"""
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record
from utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none
from config import BROAD_TECH_SEARCH_TERMS

BASE_URL = "https://www.careers24.com"
SEARCH_TERMS = BROAD_TECH_SEARCH_TERMS

CARD_SELECTOR_CANDIDATES = [
    "div.job-result",
    "article.job-listing",
    "div[class*='JobCard']",
    "li[class*='job']",
]
JOB_LINK_PATTERNS = [r"/jobs/[a-z0-9-]+-\d+", r"/job/[a-z0-9-]+"]


class Careers24Scraper(BaseScraper):
    source_name = "careers24"

    def scrape(self, max_pages=15, search_terms=None, **kwargs):
        search_terms = search_terms or SEARCH_TERMS
        records = []
        seen_urls = set()

        for term in search_terms:
            for page in range(1, max_pages + 1):
                url = f"{BASE_URL}/jobs/"
                params = {"q": term, "page": page, "sort": "date"}
                try:
                    resp = self.get(url, params=params)
                except Exception as e:
                    self.logger.warning(f"'{term}' page {page} failed: {e}")
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards, matched_sel = select_first_nonempty(soup, CARD_SELECTOR_CANDIDATES)

                parsed_this_page = 0
                if cards:
                    for card in cards:
                        rec = self._parse_card(card)
                        if rec and rec["vacancy_url"] not in seen_urls:
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1
                else:
                    for a, container in anchor_based_cards(soup, JOB_LINK_PATTERNS):
                        rec = self._parse_anchor(a, container)
                        if rec and rec["vacancy_url"] not in seen_urls:
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1

                if parsed_this_page == 0:
                    self.debug_dump(resp.text, tag=f"{term}_p{page}")
                    break

                self.polite_sleep()
        return records

    def _parse_card(self, card):
        link_tag = card.select_one("a[href*='/jobs/']") or card.find("a", href=True)
        if not link_tag or not link_tag.get("href"):
            return None
        return self._build(link_tag, card)

    def _parse_anchor(self, a, container):
        return self._build(a, container)

    def _build(self, link_tag, card):
        href = link_tag.get("href")
        if not href:
            return None
        vacancy_url = href if href.startswith("http") else BASE_URL + href
        title = text_or_none(link_tag)
        if not title or len(title) < 5:
            title_tag = card.select_one("[class*='title']")
            title = text_or_none(title_tag)
        if not title:
            return None

        company_tag = card.select_one("[class*='company']")
        location_tag = card.select_one("[class*='location']")
        salary_tag = card.select_one("[class*='salary']")
        date_tag = card.select_one("time, [class*='date']")

        return build_record(
            source=self.source_name,
            source_job_id=vacancy_url.rstrip("/").split("/")[-1],
            job_title=title,
            company=text_or_none(company_tag),
            location=text_or_none(location_tag),
            country="South Africa",
            salary=text_or_none(salary_tag),
            date_posted=(date_tag.get("datetime") if date_tag and date_tag.has_attr("datetime")
                         else text_or_none(date_tag)),
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = Careers24Scraper()
    scraper.run_and_save("output/careers24.csv", max_pages=5)
