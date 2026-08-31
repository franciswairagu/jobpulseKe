"""
Talent.com — a large global job aggregator (NOT a single employer board;
it pulls postings from many underlying source feeds, including several
other sites already in this pack like JobWebKenya and Fuzu). This makes
it one of the highest-volume, most reliable sources available here.

Unlike the other HTML scrapers in this pack, this one's structure was
verified against LIVE fetched pages (via web_search + web_fetch) rather
than guessed from memory — confirmed working for Kenya, Nigeria, and
South Africa as of this writing:
  https://ke.talent.com/jobs/k-junior-software-developer-l-kenya
  https://ng.talent.com/jobs/k-software-engineer-l-nigeria
  https://za.talent.com/jobs/k-database-developer-intern-l-bedfordview

URL pattern:  https://{country_code}.talent.com/jobs/k-{query-slug}-l-{location-slug}?p={page}
Card structure (confirmed): job title in <h2>, a "Company•Location" line
right after it, a snippet paragraph, a "Last updated: X ago" line, and a
detail-page link matching `/view?id=<digits>`.

Countries beyond ke/ng/za are included optimistically (Talent.com covers
~78 countries) but not individually verified — the scraper skips any
subdomain that errors out rather than failing the whole run.
"""
import re

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.helpers import build_record
from utils.parsing import anchor_based_cards, text_or_none
from config import BROAD_TECH_SEARCH_TERMS

# country_code: display name — subdomain is {code}.talent.com
COUNTRY_CODES = {
    "ke": "Kenya",
    "ng": "Nigeria",
    "za": "South Africa",
    "gh": "Ghana",
    "ug": "Uganda",
    "eg": "Egypt",
    "tz": "Tanzania",
    "rw": "Rwanda",
    "zm": "Zambia",
    "ma": "Morocco",
}

SEARCH_TERMS = BROAD_TECH_SEARCH_TERMS

JOB_LINK_PATTERN = [r"/view\?id=\d+"]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


class TalentComScraper(BaseScraper):
    source_name = "talent_com"

    def scrape(self, max_pages=15, countries=None, search_terms=None, **kwargs):
        countries = countries or list(COUNTRY_CODES.keys())
        search_terms = search_terms or SEARCH_TERMS
        records = []
        seen_ids = set()

        for cc in countries:
            country_name = COUNTRY_CODES[cc]
            domain = f"https://{cc}.talent.com"

            for term in search_terms:
                q_slug = slugify(term)
                l_slug = slugify(country_name)

                for page in range(1, max_pages + 1):
                    url = f"{domain}/jobs/k-{q_slug}-l-{l_slug}"
                    params = {"p": page} if page > 1 else None
                    try:
                        resp = self.get(url, params=params)
                    except Exception as e:
                        self.logger.warning(
                            f"{country_name}/{term} page {page} failed "
                            f"(subdomain may not exist for this country): {e}"
                        )
                        break

                    soup = BeautifulSoup(resp.text, "lxml")
                    cards = anchor_based_cards(soup, JOB_LINK_PATTERN, min_text_len=40)

                    parsed_this_page = 0
                    for a, container in cards:
                        rec = self._parse(a, container, domain, country_name)
                        if rec and rec["source_job_id"] not in seen_ids:
                            seen_ids.add(rec["source_job_id"])
                            records.append(rec)
                            parsed_this_page += 1

                    if parsed_this_page == 0:
                        if page == 1:
                            self.debug_dump(resp.text, tag=f"{cc}_{term}_p{page}")
                        break

                    self.polite_sleep()
        return records

    def _parse(self, a, container, domain, country_name):
        href = a.get("href")
        if not href:
            return None
        vacancy_url = href if href.startswith("http") else domain + href
        match = re.search(r"id=(\d+)", href)
        source_job_id = match.group(1) if match else vacancy_url

        title_tag = container.find("h2")
        title = text_or_none(title_tag)
        if not title:
            return None

        # Company/location line typically contains a bullet separator
        company, location = None, None
        for tag in container.find_all(["p", "span", "div"]):
            t = tag.get_text(strip=True)
            if "\u2022" in t and 3 < len(t) < 120:  # '•' bullet char
                parts = t.split("\u2022")
                company = parts[0].strip() or None
                location = parts[1].strip() if len(parts) > 1 else None
                break

        # Snippet: longest paragraph that isn't the title/company line
        snippet = None
        for p in container.find_all("p"):
            t = p.get_text(" ", strip=True)
            if t and t != title and (not company or company not in t) and len(t) > 40:
                snippet = t
                break

        date_posted = None
        date_match = container.find(string=re.compile(r"Last updated", re.IGNORECASE))
        if date_match:
            date_posted = date_match.strip()

        return build_record(
            source=self.source_name,
            source_job_id=source_job_id,
            job_title=title,
            company=company,
            job_description=snippet,
            location=location,
            country=country_name,
            date_posted=date_posted,
            vacancy_url=vacancy_url,
        )


if __name__ == "__main__":
    scraper = TalentComScraper()
    scraper.run_and_save("output/talent_com.csv", max_pages=5)
