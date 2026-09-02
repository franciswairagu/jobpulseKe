"""
Jobicy (jobicy.com) — remote-jobs board with a public, unauthenticated
JSON API at /api/v2/remote-jobs, similar in spirit to RemoteOK. Global
board, so (like RemoteOK/WWR) we filter to postings that are open
globally or explicitly Africa-relevant rather than keeping everything.

API docs (public): supports `count` and `tag`/`industry`/`geo` query
params, but exact accepted `geo` values aren't guaranteed stable, so we
fetch broadly and filter client-side against location/description text
— safer than trusting an undocumented filter value.
"""
from src.utils.helpers import build_record, guess_country, is_tech_job
from src.collectors.base_scraper import BaseScraper
from src.scraping_config import AFRICAN_COUNTRIES

API_URL = "https://jobicy.com/api/v2/remote-jobs"
OPEN_TO_ALL_MARKERS = ["anywhere", "worldwide", "global", "any location"]


class JobicyScraper(BaseScraper):
    source_name = "jobicy"

    def scrape(self, max_pages=1, count=100, **kwargs):
        # Jobicy's API returns a batch per call (no true pagination);
        # "max_pages" kept for interface consistency but unused. Bump
        # `count` instead for more results per call (API max varies).
        try:
            resp = self.get(API_URL, params={"count": count})
        except Exception as e:
            self.logger.error(f"Jobicy API fetch failed: {e}")
            return []

        try:
            data = resp.json()
        except ValueError:
            self.logger.error("Jobicy API did not return JSON (likely blocked/rate-limited)")
            return []

        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        records = []

        for job in jobs:
            location = job.get("jobGeo", "") or ""
            title = job.get("jobTitle", "") or ""
            description = job.get("jobExcerpt", "") or job.get("jobDescription", "") or ""
            haystack = f"{location} {title} {description}".lower()

            if not is_tech_job([title, description]):
                continue

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
                job_title=title,
                company=job.get("companyName"),
                job_description=description,
                location=location or "Remote",
                country=country,
                work_mode="remote",
                remote_scope="Global" if open_to_all else "Africa-wide",
                employment_type=job.get("jobType", [None])[0] if isinstance(job.get("jobType"), list) else job.get("jobType"),
                industry=job.get("jobIndustry", [None])[0] if isinstance(job.get("jobIndustry"), list) else job.get("jobIndustry"),
                salary=job.get("annualSalaryMin") and f"{job.get('annualSalaryMin')}-{job.get('annualSalaryMax')}",
                currency=job.get("salaryCurrency"),
                date_posted=job.get("pubDate"),
                vacancy_url=job.get("url"),
            )
            records.append(rec)

        self.logger.info(f"Kept {len(records)} Africa-relevant tech jobs out of {len(jobs)} total")
        return records


if __name__ == "__main__":
    scraper = JobicyScraper()
    scraper.run_and_save("output/jobicy.csv", count=200)
