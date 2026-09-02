"""
Robust, redesign-resistant HTML parsing helpers.

The problem with hand-guessed CSS selectors (e.g. `div.search-result`)
is that they silently return 0 results the moment a site's frontend
changes a class name — which is exactly what happened on the first
run of this suite against several sites. Two strategies here reduce
that fragility:

1. `select_first_nonempty` — try a *list* of candidate selectors in
   priority order and use the first one that actually matches
   anything, instead of betting everything on one guess.

2. `anchor_based_cards` — skip guessing the *card wrapper* entirely.
   Job boards almost always link each posting via an <a href> whose
   URL contains a stable pattern (/job/, /jobs/, /listings/,
   /vacancy/, etc.) even when they restyle everything else. We find
   those anchors directly, then walk up the DOM a few levels to find
   a reasonably-sized container to pull title/company/location text
   from. This keeps working even when wrapper div/class names change.
"""
import re


def select_first_nonempty(soup, selectors):
    """Try each CSS selector in order; return the first non-empty result set."""
    for sel in selectors:
        found = soup.select(sel)
        if found:
            return found, sel
    return [], None


def anchor_based_cards(soup, href_patterns, min_text_len=25, max_climb=4):
    """
    Find <a> tags whose href matches any of href_patterns (list of regex
    strings), dedup by href, and for each return (anchor, container) where
    container is the smallest ancestor with at least min_text_len chars
    of text (climbing up to max_climb parent levels looking for one).
    """
    compiled = [re.compile(p, re.IGNORECASE) for p in href_patterns]
    seen_hrefs = set()
    results = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href in seen_hrefs:
            continue
        if not any(p.search(href) for p in compiled):
            continue
        seen_hrefs.add(href)

        container = a
        for _ in range(max_climb):
            text_len = len(container.get_text(strip=True))
            if text_len >= min_text_len:
                break
            if container.parent is None:
                break
            container = container.parent

        results.append((a, container))

    return results


def text_or_none(tag):
    if tag is None:
        return None
    t = tag.get_text(" ", strip=True)
    return t or None


def guess_field_near(container, keywords, tag_names=("span", "div", "p", "li")):
    """
    Loose fallback: search a container's descendant tags for the first
    one whose own (non-nested) text matches a 'looks like this field'
    heuristic supplied via a keyword-matching function. Used when there's
    no reliable class name to hook a specific field (e.g. 'location') to.
    `keywords` is a callable(text) -> bool.
    """
    for tag in container.find_all(tag_names):
        text = tag.get_text(strip=True)
        if text and keywords(text):
            return text
    return None
