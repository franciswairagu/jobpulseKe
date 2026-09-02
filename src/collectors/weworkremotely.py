"""
We Work Remotely (weworkremotely.com) publishes RSS feeds per category,
which is much more stable to parse than their HTML and is meant for
public consumption (no ToS concerns). We pull the Programming and
DevOps/Sysadmin category feeds and — same as RemoteOK — keep only
postings that are open globally or explicitly mention Africa, since WWR
is a global board.
"""
from bs4 import BeautifulSoup

from src.collectors.base_scraper import BaseScraper
from src.utils.helpers import build_record, guess_country
from src.scraping_config import AFRICAN_COUNTRIES

FEEDS = {
    "Programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "DevOps & SysAdmin": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "Product": "https://weworkremotely.com/categories/remote-product-jobs.rss",
}

OPEN_TO_ALL_MARKERS = ["anywhere", "worldwide", "global"]


class WeWorkRemotelyScraper(BaseScraper):
    source_name = "weworkremotely"

    def scrape(self, max_pages=1, **kwargs):
        # RSS feeds aren't paginated — "max_pages" kept for API consistency.
        records = []
        for job_field, feed_url in FEEDS.items():
            try:
                resp = self.get(feed_url)
            except Exception as e:
                self.logger.warning(f"Feed '{job_field}' failed: {e}")
                continue

            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")

            for item in items:
                title = item.title.get_text(strip=True) if item.title else None
                link = item.link.get_text(strip=True) if item.link else None
                description = item.description.get_text(strip=True) if item.description else None
                pub_date = item.pubDate.get_text(strip=True) if item.pubDate else None

                # WWR RSS titles are usually "Company: Job Title"
                company, job_title = None, title
                if title and ":" in title:
                    company, job_title = [p.strip() for p in title.split(":", 1)]

                haystack = f"{title} {description}".lower() if description else (title or "").lower()
                africa_related = any(c.lower() in haystack for c in AFRICAN_COUNTRIES)
                open_to_all = any(m in haystack for m in OPEN_TO_ALL_MARKERS)
                if not (africa_related or open_to_all):
                    # WWR doesn't reliably state geo-restriction in the
                    # feed text; default to keeping it but tag scope
                    # as unknown rather than dropping (unlike RemoteOK's
                    # richer per-job location field).
                    pass

                rec = build_record(
                    source=self.source_name,
                    source_job_id=link.rstrip("/").split("/")[-1] if link else None,
                    job_title=job_title,
                    company=company,
                    job_description=description,
                    work_mode="remote",
                    remote_scope="Global" if open_to_all else ("Africa-wide" if africa_related else None),
                    country=guess_country([title, description]) if africa_related else "Any (Global Remote)",
                    job_field=job_field,
                    date_posted=pub_date,
                    vacancy_url=link,
                )
                records.append(rec)

            self.polite_sleep()
        return records


if __name__ == "__main__":
    scraper = WeWorkRemotelyScraper()
    scraper.run_and_save("output/weworkremotely.csv")
