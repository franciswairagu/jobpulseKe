"""
RemoteOK (remoteok.com) exposes a public, unauthenticated JSON feed at
/api which is far more reliable than scraping their HTML. It's a global
remote-jobs board, not Africa-specific, so we keep only postings whose
description/location explicitly welcomes African applicants or is fully
open ("Anywhere" / "Worldwide" / names an African country) — everything
else is dropped so it doesn't pollute an "Africa tech market" dataset.
"""
from src.utils.helpers import build_record, guess_country
from src.collectors.base_scraper import BaseScraper
from src.scraping_config import AFRICAN_COUNTRIES

API_URL = "https://remoteok.com/api"

OPEN_TO_ALL_MARKERS = ["anywhere", "worldwide", "global", "remote - global"]


class RemoteOKScraper(BaseScraper):
    source_name = "remoteok"

    def scrape(self, max_pages=1, **kwargs):
        # RemoteOK's /api returns the full current listing in one shot —
        # "max_pages" is accepted for interface consistency but unused.
        try:
            resp = self.get(API_URL)
        except Exception as e:
            self.logger.error(f"RemoteOK API fetch failed: {e}")
            return []

        try:
            data = resp.json()
        except ValueError:
            self.logger.error("RemoteOK API did not return JSON (likely blocked/rate-limited)")
            return []

        # First element of RemoteOK's response is metadata, not a job
        jobs = [d for d in data if isinstance(d, dict) and d.get("id")]

        records = []
        for job in jobs:
            location = job.get("location", "") or ""
            description = job.get("description", "") or ""
            haystack = f"{location} {description}".lower()

            africa_related = any(c.lower() in haystack for c in AFRICAN_COUNTRIES)
            open_to_all = any(m in haystack for m in OPEN_TO_ALL_MARKERS) or location.strip() == ""

            if not (africa_related or open_to_all):
                continue

            country = guess_country([location, description]) or (
                "Any (Global Remote)" if open_to_all else None
            )

            rec = build_record(
                source=self.source_name,
                source_job_id=str(job.get("id")),
                job_title=job.get("position"),
                company=job.get("company"),
                job_description=description,
                location=location or "Remote",
                country=country,
                work_mode="remote",
                remote_scope="Global" if open_to_all else "Africa-wide",
                employment_type="Full Time" if not job.get("contract") else "Contract",
                salary=self._format_salary(job),
                date_posted=job.get("date"),
                tech_category=None,  # let build_record's keyword classifier decide
                vacancy_url=job.get("url") or f"https://remoteok.com/remote-jobs/{job.get('id')}",
            )
            records.append(rec)

        self.logger.info(f"Kept {len(records)} Africa-relevant jobs out of {len(jobs)} total")
        return records

    @staticmethod
    def _format_salary(job):
        lo, hi = job.get("salary_min"), job.get("salary_max")
        if lo and hi:
            return f"{lo}-{hi}"
        return None


if __name__ == "__main__":
    scraper = RemoteOKScraper()
    scraper.run_and_save("output/remoteok.csv")
