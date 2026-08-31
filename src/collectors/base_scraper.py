"""
BaseScraper: shared HTTP session, retry/backoff, polite delays, logging,
debug-dumping, and a to_dataframe/save_csv convenience. Every
site-specific scraper subclasses this and implements
`scrape(max_pages)` -> list[dict].
"""
import logging
import os
import random
import time

import pandas as pd
import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
)

from config import (
    DEFAULT_HEADERS, REQUEST_TIMEOUT, MIN_DELAY, MAX_DELAY, MAX_RETRIES,
    SCHEMA_COLUMNS, OUTPUT_DIR,
)

try:
    import cloudscraper  # optional; bypasses some Cloudflare/anti-bot checks
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

DEBUG_DIR = os.path.join(OUTPUT_DIR, "debug")
MAX_DEBUG_DUMPS_PER_SOURCE = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class BaseScraper:
    source_name = "base"          # override in subclass, must match SOURCE tag
    base_url = ""                  # override in subclass

    # Set to True on subclasses hitting heavy anti-bot protection
    # (Indeed, LinkedIn) to auto-use cloudscraper's session when available.
    use_cloudscraper = False

    def __init__(self, headers=None, timeout=REQUEST_TIMEOUT):
        if self.use_cloudscraper and HAS_CLOUDSCRAPER:
            self.session = cloudscraper.create_scraper()
            self.session.headers.update(headers or DEFAULT_HEADERS)
        else:
            self.session = requests.Session()
            self.session.headers.update(headers or DEFAULT_HEADERS)
        self.timeout = timeout
        self.logger = logging.getLogger(self.source_name)
        self.records = []
        self._debug_dumps_written = 0

    # ------------------------------------------------------------------
    # HTTP with retry/backoff so transient errors (429/503/timeouts)
    # don't kill an entire multi-page crawl.
    # ------------------------------------------------------------------
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1.5, min=2, max=20),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException,)
        ),
        reraise=True,
    )
    def get(self, url, params=None, **kwargs):
        self.logger.debug(f"GET {url} params={params}")
        resp = self.session.get(
            url, params=params, timeout=self.timeout, **kwargs
        )
        if resp.status_code == 429:
            self.logger.warning("429 rate-limited, backing off harder")
            time.sleep(10)
            resp.raise_for_status()
        resp.raise_for_status()
        return resp

    def polite_sleep(self):
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    def debug_dump(self, html, tag=""):
        """
        Save a snippet of raw HTML when a page returns 0 parsed cards, so
        you can inspect what the site actually sent back (redesigned
        markup? a CAPTCHA/challenge page? a soft-block?) instead of
        guessing. Capped per scraper instance to avoid flooding disk.
        """
        if self._debug_dumps_written >= MAX_DEBUG_DUMPS_PER_SOURCE:
            return
        os.makedirs(DEBUG_DIR, exist_ok=True)
        fname = f"{self.source_name}_{tag or self._debug_dumps_written}.html"
        path = os.path.join(DEBUG_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html[:20000])  # first 20k chars is plenty to diagnose
        self._debug_dumps_written += 1
        self.logger.warning(f"0 cards parsed — dumped raw HTML to {path} for inspection")

    # ------------------------------------------------------------------
    # To be implemented by every subclass
    # ------------------------------------------------------------------
    def scrape(self, max_pages=5, **kwargs):
        raise NotImplementedError("Subclasses must implement scrape()")

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def to_dataframe(self):
        df = pd.DataFrame(self.records, columns=SCHEMA_COLUMNS)
        return df

    def save_csv(self, path):
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        self.logger.info(f"Saved {len(df)} records -> {path}")
        return path

    def run_and_save(self, path, max_pages=5, **kwargs):
        self.records = self.scrape(max_pages=max_pages, **kwargs)
        return self.save_csv(path)
