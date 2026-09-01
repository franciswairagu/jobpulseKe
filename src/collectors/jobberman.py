"""
Jobberman (jobberman.com / jobberman.com.gh) — Nigeria & Ghana.

FIX (v2): v1's generic `div[class*='job-card']` selector matched 0
cards (too generic to match anything, or the actual markup uses
different attribute naming entirely). Switched to anchor-first
extraction off `/listings/<slug>` style URLs, with a `sort=date` query
param added so results come back newest-first per Jobberman's own
sort options (falls back gracefully to default order if the site
ignores/changes that param).
"""
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record
from utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none
from config import BROAD_TECH_SEARCH_TERMS

COUNTRY_DOMAINS = {
    "Nigeria": "https://www.jobberman.com",
    "Ghana": "https://www.jobberman.com.gh",
}
SEARCH_TERMS = BROAD_TECH_SEARCH_TERMS

CARD_SELECTOR_CANDIDATES = [
    "div[class*='job-card']",
    "li[class*='job']",
    "div[data-cy='listing-cards-components']",
]
JOB_LINK_PATTERNS = [r"/listings/[a-z0-9-]+"]


class JobbermanScraper(BaseScraper):
    source_name = "jobberman"

    def scrape(self, max_pages=15, countries=None, search_terms=None, **kwargs):
        countries = countries or list(COUNTRY_DOMAINS.keys())
        search_terms = search_terms or SEARCH_TERMS
        records = []
        seen_ids = set()

        for country in countries:
            domain = COUNTRY_DOMAINS[country]
            for term in search_terms:
                for page in range(1, max_pages + 1):
                    url = f"{domain}/jobs"
                    params = {"q": term, "page": page, "sort": "date"}
                    try:
                        resp = self.get(url, params=params)
                    except Exception as e:
                        self.logger.warning(f"{country}/{term} page {page} failed: {e}")
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    cards, matched_sel = select_first_nonempty(soup, CARD_SELECTOR_CANDIDATES)

                    parsed_this_page = 0
                    if cards:
                        for card in cards:
                            rec = self._parse_card(card, domain, country)
                            if rec and rec["source_job_id"] not in seen_ids:
                                seen_ids.add(rec["source_job_id"])
                                records.append(rec)
                                parsed_this_page += 1
                    else:
                        for a, container in anchor_based_cards(soup, JOB_LINK_PATTERNS):
                            rec = self._parse_anchor(a, container, domain, country)
                            if rec and rec["source_job_id"] not in seen_ids:
                                seen_ids.add(rec["source_job_id"])
                                records.append(rec)
                                parsed_this_page += 1

                    if parsed_this_page == 0:
                        self.debug_dump(resp.text, tag=f"{country}_{term}_p{page}")
                        break

                    self.polite_sleep()
        return records

    def _parse_card(self, card, domain, country):
        link_tag = card.find("a", href=True)
        if not link_tag:
            return None
        return self._build(link_tag, card, domain, country)

    def _parse_anchor(self, a, container, domain, country):
        return self._build(a, container, domain, country)

    def _build(self, link_tag, card, domain, country):
        href = link_tag.get("href")
        if not href:
            return None
        vacancy_url = href if href.startswith("http") else domain + href
        source_job_id = vacancy_url.rstrip("/").split("/")[-1]

        title_tag = card.select_one("[class*='title']")
        company_tag = card.select_one("[class*='company']")
        location_tag = card.select_one("[class*='location']")
        salary_tag = card.select_one("[class*='salary']")

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=text_or_none(title_tag) or text_or_none(link_tag),
            company=text_or_none(company_tag),
            location=text_or_none(location_tag),
            country=country,
            salary=text_or_none(salary_tag),
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = JobbermanScraper()
    scraper.run_and_save("output/jobberman.csv", max_pages=5)
