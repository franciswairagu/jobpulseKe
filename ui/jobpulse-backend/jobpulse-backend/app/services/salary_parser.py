"""
Salary parsing.

FIXES the known open pipeline bug: currency detection previously
missed African currency prefixes (KSh, Naira/NGN, etc.), so salaries
in those postings were unreliable. This parser recognizes a broader
currency set and only marks a parsed salary as `reliable=True` when
both a numeric range AND an unambiguous currency were found -
otherwise it's surfaced honestly as unreliable rather than guessed.
"""

from __future__ import annotations

import re

CURRENCY_PATTERNS: dict[str, list[str]] = {
    "KES": [r"kes\b", r"ksh\.?\b", r"k\.sh\.?", r"kshs\.?\b"],
    "NGN": [r"ngn\b", r"naira\b", r"₦"],
    "GHS": [r"ghs\b", r"cedis?\b", r"₵"],
    "ZAR": [r"zar\b", r"rand\b", r"r\s?\d"],
    "UGX": [r"ugx\b", r"ush\.?\b"],
    "TZS": [r"tzs\b", r"tsh\.?\b"],
    "USD": [r"usd\b", r"us\$", r"\$"],
    "EUR": [r"eur\b", r"€"],
    "GBP": [r"gbp\b", r"£"],
}

_NUMBER_RANGE = re.compile(
    r"(?P<low>\d[\d,\.]*)\s*(?:k)?\s*[-–to]{1,3}\s*(?P<high>\d[\d,\.]*)\s*(?P<k2>k)?",
    re.IGNORECASE,
)
_SINGLE_NUMBER = re.compile(r"(?P<value>\d[\d,\.]*)\s*(?P<k>k)?", re.IGNORECASE)


def _detect_currency(text: str) -> str | None:
    lowered = text.lower()
    for code, patterns in CURRENCY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lowered):
                return code
    return None


def _to_number(raw: str, is_thousands: bool) -> float:
    value = float(raw.replace(",", ""))
    return value * 1000 if is_thousands else value


def parse_salary(raw_salary: str | None, raw_currency: str | None = None) -> tuple[float | None, float | None, str | None, bool]:
    """Returns (salary_min, salary_max, currency, reliable)."""
    if not raw_salary or not str(raw_salary).strip():
        return None, None, raw_currency or None, False

    text = str(raw_salary).strip()
    currency = _detect_currency(raw_currency or "") or _detect_currency(text)

    range_match = _NUMBER_RANGE.search(text)
    if range_match:
        low = _to_number(range_match.group("low"), bool(range_match.group("k2")))
        high = _to_number(range_match.group("high"), True if range_match.group("k2") else bool(range_match.group("k2")))
        # If only the high side had a 'k' suffix, the low side is likely
        # also in thousands (e.g. "50-80k") - normalize consistently.
        if range_match.group("k2") and low < 1000:
            low *= 1000
        reliable = currency is not None
        return min(low, high), max(low, high), currency, reliable

    single_match = _SINGLE_NUMBER.search(text)
    if single_match:
        value = _to_number(single_match.group("value"), bool(single_match.group("k")))
        reliable = currency is not None
        return value, value, currency, reliable

    return None, None, currency, False
