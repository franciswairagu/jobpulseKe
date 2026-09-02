"""
CareerJet — meta-search job aggregator, country editions.

FIX (v2): v1's `article.job` / `div.job` selectors matched 0 cards.
Switched to anchor-first extraction and added `sort=date` (CareerJet
supports this natively for newest-first ordering).
"""
from bs4 import BeautifulSoup

from src.collectors.base_scraper import BaseScraper
from src.utils.helpers import build_record
from src.utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none
from src.scraping_config import BROAD_TECH_SEARCH_TERMS

COUNTRY_DOMAINS = {
    "Kenya": "https://www.careerjet.co.ke",
    "South Africa": "https://www.careerjet.co.za",
    "Nigeria": "https://www.careerjet.com.ng",
    "Ghana": "https://www.careerjet.com.gh",
}
SEARCH_TERMS = BROAD_TECH_SEARCH_TERMS

CARD_SELECTOR_CANDIDATES = [
    "article.job",
    "div.job",
    "article[class*='job']",
]
JOB_LINK_PATTERNS = [r"/jobad/[a-z0-9]+", r"/job/[a-z0-9-]+"]


class CareerJetScraper(BaseScraper):
    source_name = "careerjet"

    def scrape(self, max_pages=10, countries=None, search_terms=None, **kwargs):
        countries = countries or list(COUNTRY_DOMAINS.keys())
        search_terms = search_terms or SEARCH_TERMS
        records = []
        seen_ids = set()

        for country in countries:
            domain = COUNTRY_DOMAINS[country]
            for term in search_terms:
                for page in range(1, max_pages + 1):
                    url = f"{domain}/jobs"
                    params = {"s": term, "p": page, "sort": "date"}
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
        link_tag = card.select_one("h2 a, a.job-title") or card.find("a", href=True)
        if not link_tag or not link_tag.get("href"):
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

        company_tag = card.select_one(".company, [class*='company']")
        location_tag = card.select_one(".location, [class*='location']")
        desc_tag = card.select_one("p")
        date_tag = card.select_one(".badge, .job-date, [class*='date']")

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=text_or_none(link_tag),
            company=text_or_none(company_tag),
            location=text_or_none(location_tag),
            country=country,
            job_description=text_or_none(desc_tag),
            date_posted=text_or_none(date_tag),
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = CareerJetScraper()
    scraper.run_and_save("output/careerjet.csv", max_pages=5)
