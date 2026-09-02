"""
MyJobMag — Nigeria (myjobmag.com) & Kenya (myjobmag.co.ke).

FIX (v2): the first version targeted a guessed category path
(/jobs-by-field/it-telecomms) and returned 0 records — either the slug
is wrong or the theme markup changed. This version instead crawls the
site's general/recent jobs listing (naturally newest-first) across many
pages and keeps only postings that pass `is_tech_job()` keyword
filtering from utils.helpers — this is more robust because it doesn't
depend on MyJobMag's category taxonomy staying stable, only on the
listing page existing at all. Card parsing tries multiple selector
candidates, then falls back to anchor-based extraction.
"""
from bs4 import BeautifulSoup

from src.collectors.base_scraper import BaseScraper
from src.utils.helpers import build_record, is_tech_job
from src.utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none

COUNTRY_DOMAINS = {
    "Nigeria": "https://www.myjobmag.com",
    "Kenya": "https://www.myjobmag.co.ke",
}
# General/recent jobs listing (not category-specific), newest-first
LISTING_PATH = "/jobs"

CARD_SELECTOR_CANDIDATES = [
    "li.job-list-li",
    "div.job-list-item",
    "li.job-item",
    "div.job-card",
]

JOB_LINK_PATTERNS = [r"/job/[a-z0-9-]+", r"/jobs/[a-z0-9-]+-\d+"]


class MyJobMagScraper(BaseScraper):
    source_name = "myjobmag"

    def scrape(self, max_pages=15, countries=None, **kwargs):
        countries = countries or list(COUNTRY_DOMAINS.keys())
        records = []
        seen_urls = set()

        for country in countries:
            domain = COUNTRY_DOMAINS[country]
            for page in range(1, max_pages + 1):
                url = f"{domain}{LISTING_PATH}"
                params = {"page": page} if page > 1 else None
                try:
                    resp = self.get(url, params=params)
                except Exception as e:
                    self.logger.warning(f"{country} page {page} failed: {e}")
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards, matched_sel = select_first_nonempty(soup, CARD_SELECTOR_CANDIDATES)

                parsed_this_page = 0
                if cards:
                    for card in cards:
                        rec = self._parse_card(card, domain, country)
                        if rec and rec["vacancy_url"] not in seen_urls and self._is_relevant(rec):
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1
                else:
                    for a, container in anchor_based_cards(soup, JOB_LINK_PATTERNS):
                        rec = self._parse_anchor(a, container, domain, country)
                        if rec and rec["vacancy_url"] not in seen_urls and self._is_relevant(rec):
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1

                if not cards and parsed_this_page == 0:
                    self.debug_dump(resp.text, tag=f"{country}_p{page}")

                if parsed_this_page == 0 and page > 1:
                    break  # ran out of pages for this country

                self.polite_sleep()
        return records

    @staticmethod
    def _is_relevant(rec):
        return is_tech_job([rec.get("job_title"), rec.get("job_description")])

    def _parse_card(self, card, domain, country):
        link_tag = card.find("a", href=True)
        if not link_tag:
            return None
        return self._build(link_tag["href"], text_or_none(link_tag), card, domain, country)

    def _parse_anchor(self, a, container, domain, country):
        return self._build(a.get("href"), text_or_none(a), container, domain, country)

    def _build(self, href, title, card, domain, country):
        if not href or not title:
            return None
        vacancy_url = href if href.startswith("http") else domain + href
        source_job_id = vacancy_url.rstrip("/").split("/")[-1]

        company_tag = card.select_one(".job-list-comp, .company-name, [class*='company']")
        meta_tag = card.select_one(".job-list-meta, .job-meta, [class*='meta']")

        location, employment_type = None, None
        if meta_tag:
            meta_text = meta_tag.get_text(" ", strip=True)
            parts = [p.strip() for p in meta_text.split("|")]
            if parts:
                location = parts[0] or None
            if len(parts) > 1:
                employment_type = parts[1] or None

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=title,
            company=text_or_none(company_tag),
            location=location,
            country=country,
            employment_type=employment_type,
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = MyJobMagScraper()
    scraper.run_and_save("output/myjobmag.csv", max_pages=5)
