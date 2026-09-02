"""
Indeed — CAVEAT: strongest anti-scraping defenses in this pack
(Cloudflare-style challenges, frequent HTML changes, IP blocking).

FIX (v2) based on the last run's errors:
1. `ke.indeed.com` failed DNS resolution entirely (NameResolutionError)
   — that country subdomain may no longer exist. Now we try a small
   list of domain candidates per country (country subdomain first,
   then the global www.indeed.com with an `l=<location>` param as
   fallback) and use whichever resolves.
2. `za.indeed.com` / `ng.indeed.com` returned 403s — added
   `use_cloudscraper = True` so this scraper automatically uses the
   `cloudscraper` library's session (if installed) instead of plain
   `requests`, which handles a meaningful fraction of these challenge
   pages automatically. Falls back to plain requests if cloudscraper
   isn't installed.
3. Added `sort=date` (Indeed supports this natively) for newest-first
   ordering.

Still budget this as last-priority — even with these fixes, expect a
lower success rate than the other sources.
"""
from bs4 import BeautifulSoup

from src.collectors.base_scraper import BaseScraper
from src.utils.helpers import build_record
from src.utils.parsing import text_or_none

# (subdomain_url, needs_location_param) — tried in order per country
COUNTRY_DOMAIN_CANDIDATES = {
    "Kenya": [("https://ke.indeed.com", False), ("https://www.indeed.com", True)],
    "Nigeria": [("https://ng.indeed.com", False), ("https://www.indeed.com", True)],
    "South Africa": [("https://za.indeed.com", False), ("https://www.indeed.com", True)],
}
SEARCH_TERMS = ["software developer", "data analyst", "IT support"]


class IndeedScraper(BaseScraper):
    source_name = "indeed"
    use_cloudscraper = True  # auto-uses cloudscraper session if installed

    def scrape(self, max_pages=10, countries=None, search_terms=None, **kwargs):
        countries = countries or list(COUNTRY_DOMAIN_CANDIDATES.keys())
        search_terms = search_terms or SEARCH_TERMS
        records = []
        seen_ids = set()

        for country in countries:
            domain, needs_loc = self._resolve_working_domain(country)
            if not domain:
                self.logger.error(f"{country}: no working domain found, skipping entirely")
                continue

            for term in search_terms:
                for page in range(max_pages):
                    params = {"q": term, "start": page * 10, "sort": "date"}
                    if needs_loc:
                        params["l"] = country
                    try:
                        resp = self.get(f"{domain}/jobs", params=params)
                    except Exception as e:
                        self.logger.warning(
                            f"{country}/{term} start={page*10} failed "
                            f"(blocked/challenged/DNS): {e}"
                        )
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    cards = soup.select("div.job_seen_beacon, td.resultContent")
                    if not cards:
                        self.debug_dump(resp.text, tag=f"{country}_{term}_p{page}")
                        self.logger.info(
                            f"{country}/{term}: 0 cards — likely a CAPTCHA/"
                            f"challenge page instead of results"
                        )
                        break

                    for card in cards:
                        rec = self._parse_card(card, domain, country)
                        if rec and rec["source_job_id"] not in seen_ids:
                            seen_ids.add(rec["source_job_id"])
                            records.append(rec)

                    self.polite_sleep()
        return records

    def _resolve_working_domain(self, country):
        """Try each candidate domain with a trivial request; return the
        first that responds without a connection-level failure (a 403
        still 'counts' as working — it just means content is blocked,
        not that the domain is unreachable; we still attempt real
        requests against it since some queries succeed even when others
        get challenged)."""
        for domain, needs_loc in COUNTRY_DOMAIN_CANDIDATES.get(country, []):
            try:
                self.get(f"{domain}/jobs", params={"q": "test"})
                return domain, needs_loc
            except Exception as e:
                self.logger.warning(f"{country}: domain {domain} unreachable ({e}), trying next candidate")
                continue
        return None, False

    def _parse_card(self, card, domain, country):
        link_tag = card.select_one("h2.jobTitle a") or card.find("a", href=True)
        if not link_tag or not link_tag.get("href"):
            return None
        href = link_tag["href"]
        vacancy_url = href if href.startswith("http") else domain + href
        if "jk=" in vacancy_url:
            source_job_id = vacancy_url.split("jk=")[-1].split("&")[0]
        else:
            source_job_id = vacancy_url.rstrip("/").split("/")[-1]

        title_tag = card.select_one("h2.jobTitle span")
        company_tag = card.select_one("span.companyName")
        location_tag = card.select_one("div.companyLocation")
        salary_tag = card.select_one("div.salary-snippet-container, div.metadata.salary-snippet-container")
        summary_tag = card.select_one("div.job-snippet")

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=text_or_none(title_tag) or text_or_none(link_tag),
            company=text_or_none(company_tag),
            location=text_or_none(location_tag),
            country=country,
            salary=text_or_none(salary_tag),
            job_description=text_or_none(summary_tag),
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = IndeedScraper()
    scraper.run_and_save("output/indeed.csv", max_pages=3)
