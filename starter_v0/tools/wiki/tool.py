from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

SUPPORTED_LANGS = ("en", "vi")
USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"
HEADERS = {"User-Agent": USER_AGENT}
SEARCH_LIMIT = 3
MAX_RETRY_WAIT_SECONDS = 5.0


class WikiNotFound(Exception):
    """No article for the title and no search hit either."""


def _get(url: str, **kwargs: Any) -> requests.Response:
    """GET with one light retry on HTTP 429 (Wikimedia rate limit), honouring Retry-After up to 5s."""
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    if response.status_code == 429:
        try:
            wait = float((getattr(response, "headers", None) or {}).get("retry-after", 2))
        except (TypeError, ValueError):
            wait = 2.0
        time.sleep(min(max(wait, 0.0), MAX_RETRY_WAIT_SECONDS))
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    return response


def _get_summary(lang: str, title: str) -> requests.Response:
    return _get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'), safe='')}")


def _search_pages(lang: str, query: str) -> list[dict[str, Any]]:
    """Full-text search; used only when the exact title returned 404."""
    response = _get(
        f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page",
        params={"q": query, "limit": SEARCH_LIMIT},
    )
    response.raise_for_status()
    return [page for page in response.json().get("pages") or [] if page.get("key")]


def wiki_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    """Return the lead summary of one Wikipedia article (REST API, no key needed).

    If the exact title does not exist (404), fall back to Wikipedia full-text search and
    summarise the best hit, marking the result as approximate (`resolved_from`, `alternatives`).
    """
    try:
        title = (title or "").strip() if isinstance(title, str) else ""
        if not title:
            raise ValueError("title must be a non-empty string")
        lang = (lang or "en").strip().lower() if isinstance(lang, str) else "en"
        if lang not in SUPPORTED_LANGS:
            lang = "en"

        resolved_from: str | None = None
        alternatives: list[str] = []
        response = _get_summary(lang, title)
        if response.status_code == 404:
            pages = _search_pages(lang, title.replace("_", " "))
            if not pages:
                raise WikiNotFound(
                    f"No Wikipedia article or search result for '{title}'. "
                    "Use lookup (web search) for this question instead."
                )
            resolved_from = title
            alternatives = [page.get("title") or page["key"] for page in pages[1:]]
            response = _get_summary(lang, pages[0]["key"])
        response.raise_for_status()

        data = response.json()
        if data.get("type") == "disambiguation":
            raise LookupError(f"'{title}' is ambiguous on Wikipedia; ask the user which one they mean")

        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") or ""
        result: dict[str, Any] = {
            "tool": "wiki_summary",
            "title": title,
            "lang": lang,
            "items": [{
                "title": data.get("title") or title,
                "url": page_url,
                "source": f"{lang}.wikipedia.org",
                "summary": (data.get("extract") or "")[:2000],
                "description": data.get("description") or "",
            }],
        }
        if resolved_from:
            result.update({
                "resolved_from": resolved_from,
                "match": "search_fallback",
                "alternatives": alternatives,
                "note": "Exact title not found; this is the closest Wikipedia article. "
                        "Say so to the user, and use lookup if it does not answer the question.",
            })
        return result
    except Exception as exc:
        return err("wiki_summary", exc)
