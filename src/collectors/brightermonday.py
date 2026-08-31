"""
BrighterMonday (brightermonday.co.ke / .co.ug) — East Africa job board.

FIX (v2): v1 returned 0 records ("no more results at page 1") — the
`div.search-result` wrapper class it relied on is either gone or the
listing page is more JS-hydrated than before. This version:
  1. Tries several candidate wrapper selectors first (cheap, fast path).
  2. Falls back to anchor-based extraction keyed off the URL pattern
     `/listings/<slug>` which BrighterMonday has used consistently for
     years even across visual redesigns — links are almost always
     present in initial server HTML even when styling is JS-driven.
  3. Auto-dumps raw HTML to output/debug/ on a genuine dead end so you
     can see immediately if the page is fully client-rendered (in which
     case the README's Selenium/Playwright note applies) vs. just a
     wrong selector.
"""
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record
from utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none

COUNTRY_DOMAINS = {
    "Kenya": "https://www.brightermonday.co.ke",
    "Uganda": "https://www.brightermonday.co.ug",
}
TECH_CATEGORY_SLUG = "jobs-in-ict-computer"

CARD_SELECTOR_CANDIDATES = [
    "div.search-result",
    "div[data-cy='listing-cards-components']",
    "article",
    "li.search-result",
]
JOB_LINK_PATTERNS = [r"/listings/[a-z0-9-]+"]


class BrighterMondayScraper(BaseScraper):
    source_name = "brightermonday"

    def scrape(self, max_pages=15, countries=None, **kwargs):
        countries = countries or list(COUNTRY_DOMAINS.keys())
        records = []
        seen_urls = set()

        for country in countries:
            domain = COUNTRY_DOMAINS[country]
            for page in range(1, max_pages + 1):
                url = f"{domain}/{TECH_CATEGORY_SLUG}?page={page}"
                try:
                    resp = self.get(url)
                except Exception as e:
                    self.logger.warning(f"{country} page {page} failed: {e}")
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards, matched_sel = select_first_nonempty(soup, CARD_SELECTOR_CANDIDATES)

                parsed_this_page = 0
                if cards:
                    for card in cards:
                        rec = self._parse_card(card, domain, country)
                        if rec and rec["vacancy_url"] not in seen_urls:
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1
                else:
                    for a, container in anchor_based_cards(soup, JOB_LINK_PATTERNS):
                        rec = self._parse_anchor(a, container, domain, country)
                        if rec and rec["vacancy_url"] not in seen_urls:
                            seen_urls.add(rec["vacancy_url"])
                            records.append(rec)
                            parsed_this_page += 1

                if parsed_this_page == 0:
                    self.debug_dump(resp.text, tag=f"{country}_p{page}")
                    self.logger.info(f"{country}: no more results at page {page}")
                    break

                self.polite_sleep()
        return records

    def _parse_card(self, card, domain, country):
        link_tag = card.select_one("a[href*='/listings/']") or card.find("a", href=True)
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

        title_tag = card.select_one("p.search-result__job-title") or card.find(["h3", "h2"])
        company_tag = card.select_one("p.search-result__job-company") or card.select_one("[class*='company']")
        location_tag = card.select_one("[class*='location']")
        salary_tag = card.select_one("[class*='salary']")
        summary_tag = card.select_one("p.search-result__job-summary") or card.select_one("p")

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=text_or_none(title_tag) or text_or_none(link_tag),
            company=text_or_none(company_tag),
            job_description=text_or_none(summary_tag),
            location=text_or_none(location_tag),
            country=country,
            job_field="ICT & Computer",
            salary=text_or_none(salary_tag),
            vacancy_url=vacancy_url,
        )

    def enrich_with_description(self, record):
        """Optional second pass: visit vacancy_url to pull the full job
        description + deadline + experience for a smaller, curated
        subset if you don't want to hit every detail page."""
        try:
            resp = self.get(record["vacancy_url"])
        except Exception as e:
            self.logger.warning(f"Detail fetch failed for {record['vacancy_url']}: {e}")
            return record

        soup = BeautifulSoup(resp.text, "lxml")
        desc = soup.select_one("div#job-description") or soup.select_one(".job-details")
        deadline = soup.find(string=lambda s: s and "deadline" in s.lower())
        exp = soup.find(string=lambda s: s and "experience" in s.lower())

        if desc:
            record["job_description"] = desc.get_text(" ", strip=True)
        if deadline:
            record["application_deadline"] = deadline.strip()
        if exp:
            record["experience_required"] = exp.strip()
        return record


if __name__ == "__main__":
    scraper = BrighterMondayScraper()
    scraper.run_and_save("output/brightermonday.csv", max_pages=5)
