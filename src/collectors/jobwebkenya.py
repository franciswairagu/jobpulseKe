"""
JobWebKenya (jobwebkenya.com) — WordPress-based Kenyan job board.

FIX (v2): the first version hit /category/it-telecoms which now 404s —
the category taxonomy/slug has evidently changed since. Rather than
guess another slug that can just as easily rot again, this version uses
WordPress's built-in search endpoint (`/?s=<query>`), which is a stable
WP core feature almost never renamed by a site redesign, and paginates
via `/page/N/?s=<query>` (also WP core behaviour). We run several tech
search terms and de-dupe by URL. Card selectors also now try multiple
candidates and fall back to anchor-based extraction if the theme's
markup has changed too.
"""
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record
from utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none
from config import BROAD_TECH_SEARCH_TERMS

BASE_URL = "https://jobwebkenya.com"
SEARCH_TERMS = BROAD_TECH_SEARCH_TERMS

CARD_SELECTOR_CANDIDATES = [
    "article",
    "div.post",
    "div.td_module_16",
    "div.item-details",
]

JOB_LINK_PATTERNS = [r"jobwebkenya\.com/[a-z0-9-]+/?$"]


class JobWebKenyaScraper(BaseScraper):
    source_name = "jobwebkenya"

    def scrape(self, max_pages=15, search_terms=None, **kwargs):
        search_terms = search_terms or SEARCH_TERMS
        records = []
        seen_urls = set()

        for term in search_terms:
            for page in range(1, max_pages + 1):
                url = f"{BASE_URL}/page/{page}/" if page > 1 else f"{BASE_URL}/"
                params = {"s": term}
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
                    # Fallback: anchor-based extraction directly off the page
                    for a, container in anchor_based_cards(soup, JOB_LINK_PATTERNS):
                        rec = self._parse_anchor(a, container)
                        if rec and rec["vacancy_url"] not in seen_urls:
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1

                if parsed_this_page == 0:
                    self.debug_dump(resp.text, tag=f"{term}_p{page}")
                    break  # no more results for this term

                self.polite_sleep()
        return records

    def _parse_card(self, card):
        link_tag = card.select_one("h2 a, h3 a") or card.find("a", href=True)
        if not link_tag or not link_tag.get("href"):
            return None
        vacancy_url = link_tag["href"]
        title = text_or_none(link_tag)
        return self._build(vacancy_url, title, card)

    def _parse_anchor(self, a, container):
        vacancy_url = a.get("href")
        title = text_or_none(a)
        return self._build(vacancy_url, title, container)

    def _build(self, vacancy_url, title, container):
        if not vacancy_url or not title or len(title) < 5:
            return None
        source_job_id = vacancy_url.rstrip("/").split("/")[-1]
        excerpt_tag = container.select_one(".entry-summary, .excerpt, p")
        date_tag = container.select_one("time")

        company = None
        if title and " at " in title:
            company = title.split(" at ")[-1].strip()

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=title,
            company=company,
            job_description=text_or_none(excerpt_tag),
            country="Kenya",
            job_field="IT & Telecoms",
            date_posted=(date_tag.get("datetime") if date_tag and date_tag.has_attr("datetime")
                         else text_or_none(date_tag)),
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = JobWebKenyaScraper()
    scraper.run_and_save("output/jobwebkenya.csv", max_pages=5)
