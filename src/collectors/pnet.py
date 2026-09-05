"""
PNet (pnet.co.za) — long-running South African job board with an IT
category. Anchor-first parsing (same rationale as Careers24 — new
addition, no verified selector history to lean on).
"""
from bs4 import BeautifulSoup

from src.collectors.base_scraper import BaseScraper
from src.utils.helpers import build_record
from src.utils.parsing import select_first_nonempty, anchor_based_cards, text_or_none
BASE_URL = "https://www.pnet.co.za"
# PNet's IT & Telecommunications facet. Using this avoids the slow keyword
# endpoint that timed out once per search term during the last refresh.
IT_CATEGORY_PARAMS = {"action": "facet_selected;categories;1000000", "fu": "1000000"}

CARD_SELECTOR_CANDIDATES = [
    "article[data-at='job-item']",
    "div.job-item",
    "li[class*='job']",
]
JOB_LINK_PATTERNS = [r"/jobs--.+--\d+-inline\.html", r"/job-\d+"]


class PNetScraper(BaseScraper):
    source_name = "pnet"

    def __init__(self, **kwargs):
        super().__init__(timeout=45, **kwargs)

    def scrape(self, max_pages=15, **kwargs):
        records = []
        seen_urls = set()

        for page in range(1, max_pages + 1):
            try:
                resp = self.get(f"{BASE_URL}/jobs", params={**IT_CATEGORY_PARAMS, "page": page})
            except Exception as e:
                self.logger.warning(f"IT category page {page} failed: {e}")
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
                self.debug_dump(resp.text, tag=f"it_category_p{page}")
                break

            self.polite_sleep()
        return records

    def _parse_card(self, card):
        link_tag = card.find("a", href=True)
        if not link_tag:
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

        company_tag = card.select_one("[class*='company'], [data-at='job-item-company-name']")
        location_tag = card.select_one("[class*='location'], [data-at='job-item-location']")
        salary_tag = card.select_one("[class*='salary']")
        date_tag = card.select_one("time, [class*='date'], [data-at='job-item-date']")

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
    scraper = PNetScraper()
    scraper.run_and_save("output/pnet.csv", max_pages=5)
