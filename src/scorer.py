def score_source(url: str) -> dict:
    return {
        "score": float,
        "explanation": str
    }

"""
Project 1 - Credibility Scoring (Deliverable 1)

This module defines a single public function: score_source(url: str) -> dict
It returns a JSON-like dict:
    {"score": float, "explanation": str}

Scoring here is intentionally heuristic (draft/prototype).
It uses simple, explainable signals:
- Domain type (gov/edu vs unknown)
- HTTPS
- Page title and basic content availability
- Presence of author/date hints
- Presence of references/citations hints
- Accessibility / error handling
"""

import re
from dataclasses import dataclass
from typing import Dict, Tuple

import requests
import tldextract
from bs4 import BeautifulSoup


# -----------------------------
# Helpers: URL normalization
# -----------------------------
def _normalize_url(raw: str) -> str:
    """
    Normalize common URL inputs:
    - allow users to pass 'example.com' without scheme
    - strip spaces
    - basic validation (must contain a dot in the host)
    """
    if raw is None:
        raise ValueError("URL is None")

    url = raw.strip()
    if not url:
        raise ValueError("Empty URL")

    # If user didn't include scheme, assume https
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = "https://" + url

    # Very light validation: should contain at least one dot in hostname part
    # (this avoids 'https://hello' nonsense)
    host = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0]
    if "." not in host:
        raise ValueError(f"Invalid URL host: {host}")

    return url


def _domain_info(url: str) -> Tuple[str, str]:
    """
    Extract domain + suffix using tldextract.
    Returns: (registered_domain, suffix)
    Example: https://www.nih.gov/... -> ('nih', 'gov')
    """
    ext = tldextract.extract(url)
    registered = ext.domain  # 'nih'
    suffix = ext.suffix      # 'gov'
    return registered, suffix


# -----------------------------
# Helpers: content checks
# -----------------------------
@dataclass
class FetchResult:
    ok: bool
    status_code: int
    final_url: str
    title: str
    text_len: int
    has_author_hint: bool
    has_date_hint: bool
    has_reference_hint: bool
    used_https: bool
    error: str


def _fetch_and_analyze(url: str, timeout_s: int = 8) -> FetchResult:
    """
    Fetch the page and extract a few lightweight signals.
    Must be robust: handle timeouts, connection errors, non-HTML content, etc.
    """
    used_https = url.lower().startswith("https://")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CS676-CredibilityBot/1.0)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s, allow_redirects=True)
    except requests.RequestException as e:
        return FetchResult(
            ok=False,
            status_code=0,
            final_url=url,
            title="",
            text_len=0,
            has_author_hint=False,
            has_date_hint=False,
            has_reference_hint=False,
            used_https=used_https,
            error=str(e),
        )

    status = resp.status_code
    final_url = resp.url

    # If not OK status, still return cleanly
    if status < 200 or status >= 300:
        return FetchResult(
            ok=False,
            status_code=status,
            final_url=final_url,
            title="",
            text_len=0,
            has_author_hint=False,
            has_date_hint=False,
            has_reference_hint=False,
            used_https=final_url.lower().startswith("https://"),
            error=f"HTTP {status}",
        )

    # Basic content-type check
    ctype = resp.headers.get("Content-Type", "")
    if "text/html" not in ctype.lower():
        # Non-HTML (pdf/image/etc) -> still plausible credible, but limited analysis
        return FetchResult(
            ok=True,
            status_code=status,
            final_url=final_url,
            title="(non-html content)",
            text_len=len(resp.content or b""),
            has_author_hint=False,
            has_date_hint=False,
            has_reference_hint=False,
            used_https=final_url.lower().startswith("https://"),
            error="",
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract title (if any)
    title = soup.title.get_text(strip=True) if soup.title else ""

    # Get visible text length (rough)
    text = soup.get_text(separator=" ", strip=True)
    text_len = len(text)

    # Author hints
    author_patterns = [
        r"\bby\s+[A-Z][a-z]+\s+[A-Z][a-z]+",     # "By John Smith"
        r"author",                               # meta tags / visible labels
        r"written by",
    ]
    has_author_hint = any(re.search(p, text, flags=re.IGNORECASE) for p in author_patterns)

    # Date hints (simple)
    date_patterns = [
        r"\b(19|20)\d{2}\b",                     # year
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+(19|20)\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/(19|20)\d{2}\b",
        r"\bupdated\b|\bpublished\b|\blast reviewed\b",
    ]
    has_date_hint = any(re.search(p, text, flags=re.IGNORECASE) for p in date_patterns)

    # Reference / citation hints
    ref_patterns = [
        r"\breferences\b",
        r"\bcitations?\b",
        r"\bbibliography\b",
        r"\bdoi:\b",
        r"\bPMID\b",
        r"\bjournal\b",
    ]
    has_reference_hint = any(re.search(p, text, flags=re.IGNORECASE) for p in ref_patterns)

    return FetchResult(
        ok=True,
        status_code=status,
        final_url=final_url,
        title=title,
        text_len=text_len,
        has_author_hint=has_author_hint,
        has_date_hint=has_date_hint,
        has_reference_hint=has_reference_hint,
        used_https=final_url.lower().startswith("https://"),
        error="",
    )


# -----------------------------
# Public API: score_source
# -----------------------------
def score_source(url: str) -> Dict[str, object]:
    """
    Score a source URL for credibility.

    Returns a JSON-like dict:
      {
        "score": float,        # 0.0 to 1.0
        "explanation": str
      }

    This is a draft heuristic score:
    - domain suffix trust
    - accessibility + HTTPS
    - minimal content quality signals (title, length, author/date/ref hints)

    The explanation is intentionally human-readable and states which signals were used.
    """
    try:
        normalized = _normalize_url(url)
    except ValueError as e:
        return {
            "score": 0.0,
            "explanation": f"Invalid input URL: {e}"
        }

    # Domain-based prior
    _, suffix = _domain_info(normalized)
    suffix = suffix.lower()

    base = 0.35
    reasons = []

    # Domain suffix adjustment
    if suffix.endswith("gov"):
        base += 0.25
        reasons.append("Government domain (.gov) tends to be reliable.")
    elif suffix.endswith("edu"):
        base += 0.20
        reasons.append("Educational domain (.edu) tends to be reliable.")
    elif suffix.endswith("org"):
        base += 0.08
        reasons.append("Organization domain (.org) can be credible depending on the org.")
    elif suffix.endswith("com"):
        base += 0.02
        reasons.append("Commercial domain (.com) varies widely in credibility.")
    else:
        base += 0.00
        reasons.append("Unknown/other domain suffix; credibility varies.")

    # Fetch + analyze
    fr = _fetch_and_analyze(normalized)

    if not fr.ok:
        # Penalize heavily if can't be accessed / bad status
        score = max(0.05, base - 0.25)
        return {
            "score": float(round(min(score, 1.0), 3)),
            "explanation": f"Could not reliably access the source ({fr.error}). {', '.join(reasons)}"
        }

    # HTTPS bonus
    if fr.used_https:
        base += 0.05
        reasons.append("Uses HTTPS (encrypted connection).")
    else:
        base -= 0.05
        reasons.append("Not using HTTPS; harder to trust transport security.")

    # Title bonus
    if fr.title and fr.title != "(non-html content)":
        base += 0.03
        reasons.append("Page has a title, suggesting a structured page.")
    elif fr.title == "(non-html content)":
        reasons.append("Non-HTML content (limited text analysis).")

    # Content length bonus (very rough)
    if fr.text_len >= 2000:
        base += 0.06
        reasons.append("Has substantial content length.")
    elif fr.text_len >= 600:
        base += 0.03
        reasons.append("Has moderate content length.")
    else:
        base -= 0.03
        reasons.append("Very little readable text; harder to assess credibility.")

    # Author/date/reference signals
    if fr.has_author_hint:
        base += 0.05
        reasons.append("Author information detected.")
    if fr.has_date_hint:
        base += 0.04
        reasons.append("Publication/update date hints detected.")
    if fr.has_reference_hint:
        base += 0.06
        reasons.append("Reference/citation hints detected.")

    # Clamp score
    score = max(0.0, min(base, 1.0))

    # Short explanation
    explanation = " ".join(reasons)

    return {
        "score": float(round(score, 3)),
        "explanation": explanation
    }
