"""Tool Unit Test Challenge - all stubs implemented.

Patterns come from test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
wiki_tool = TOOL_FUNCTIONS["wiki"]


def _set_rapidapi(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk-test")
    monkeypatch.setenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify_tool(question="Chọn nguồn nào?", response_type="choice", options=["web", "twitter"])

    assert result["options"] == ["web", "twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("a2") < markdown.index("## B")  # a2 grouped under A


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"t{i}", "url": f"https://x.com/{i}"} for i in range(3)]
    lines = format_tool(items=items, template="thread")["markdown"].split("\n\n")

    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        result = format_tool(items=empty, template="sections")
        assert result["item_count"] == 0
        assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "bot123:abc/sendMessage" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100999"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="x", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tk")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nbody",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post"},
    }}))

    result = fetch_tool(url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://www.example.com/post"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-test"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.example.com/post",
        "source": "example.com", "summary": "# Hello\nbody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "y" * 5000, "metadata": {}}}))

    summary = fetch_tool(url="https://example.com")["items"][0]["summary"]

    assert len(summary) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    _set_rapidapi(monkeypatch)
    raw = [{"text": "no id", "screen_name": "sama"}] + [
        {"tweet_id": str(100 + i), "text": f"tweet {i}", "screen_name": "sama"} for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": raw}))

    result = timeline_tool(screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        "https://x.com/sama/status/100", "https://x.com/sama/status/101", "https://x.com/sama/status/102",
    ]


def test_timeline_strips_at_sign_from_handle(monkeypatch, fake_http) -> None:
    """Regression: model often sends '@sama'; the API expects 'sama' (bug found + fixed)."""
    _set_rapidapi(monkeypatch)
    calls = fake_http(FakeResponse({"timeline": []}))

    result = timeline_tool(screenname=" @sama ", limit=1)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert result["screenname"] == "sama"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    _set_rapidapi(monkeypatch)
    calls = fake_http(FakeResponse({"timeline": []}))

    social_search_tool(query="OpenAI", search_type="Top")

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/search.php"
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "rk-test"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    for empty in ("", "   ", "?!"):
        assert policy_tool(query=empty)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="dữ liệu cá nhân privacy", policy_area="data_privacy", top_k=5)

    assert result["results"]
    assert {hit["policy_area"] for hit in result["results"]} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="viral tweet citation verified", policy_area="source_citation", top_k=10)

    flagged = [line for hit in result["results"] for line in hit["untrusted_text"] if line.lower().startswith("assistant:")]
    assert flagged, "instruction-like quoted line should be isolated in untrusted_text"
    for hit in result["results"]:
        assert "assistant:" not in hit["facts"].lower()


# ---------------- wiki (team tool) ----------------

def test_wiki_happy_path_builds_request_and_maps_summary(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "type": "standard",
        "title": "Retrieval-augmented generation",
        "description": "AI technique",
        "extract": "RAG is a technique...",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"}},
    }))

    result = wiki_tool(title="Retrieval-augmented generation", lang="en")

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Retrieval-augmented_generation"
    assert "User-Agent" in calls[0]["headers"]
    assert result["items"][0] == {
        "title": "Retrieval-augmented generation",
        "url": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
        "source": "en.wikipedia.org",
        "summary": "RAG is a technique...",
        "description": "AI technique",
    }


def test_wiki_empty_or_wrong_type_title_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))

    for bad in ("", "   ", None, 123):
        result = wiki_tool(title=bad)
        assert result["error"] == "ValueError"

    assert calls == []


def test_wiki_out_of_enum_lang_falls_back_to_en_and_encodes_title(fake_http) -> None:
    calls = fake_http(FakeResponse({"type": "standard", "title": "Hà Nội", "extract": "x"}))

    result = wiki_tool(title="Hà Nội", lang="klingon")

    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/H%C3%A0_N%E1%BB%99i"
    assert result["lang"] == "en"


def _fake_get_sequence(monkeypatch, responses: list[FakeResponse]) -> list[dict]:
    """Like fake_http, but returns a different response for each successive requests.get."""
    calls: list[dict] = []
    queue = list(responses)

    def _get(url: str, **kwargs):
        calls.append({"url": url, **kwargs})
        return queue.pop(0)

    monkeypatch.setattr(requests, "get", _get)
    return calls


def test_wiki_404_falls_back_to_search_and_marks_result_approximate(monkeypatch) -> None:
    calls = _fake_get_sequence(monkeypatch, [
        FakeResponse(status_code=404),
        FakeResponse({"pages": [
            {"key": "Agent_harness", "title": "Agent harness"},
            {"key": "AI_agent", "title": "AI agent"},
        ]}),
        FakeResponse({"type": "standard", "title": "Agent harness", "extract": "An agent harness ...",
                      "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Agent_harness"}}}),
    ])

    result = wiki_tool(title="Agent loop")

    assert [call["url"] for call in calls] == [
        "https://en.wikipedia.org/api/rest_v1/page/summary/Agent_loop",
        "https://en.wikipedia.org/w/rest.php/v1/search/page",
        "https://en.wikipedia.org/api/rest_v1/page/summary/Agent_harness",
    ]
    assert calls[1]["params"] == {"q": "Agent loop", "limit": 3}
    assert "error" not in result
    assert result["items"][0]["title"] == "Agent harness"
    assert result["resolved_from"] == "Agent loop"
    assert result["match"] == "search_fallback"
    assert result["alternatives"] == ["AI agent"]


def test_wiki_404_with_no_search_hit_returns_not_found_with_lookup_hint(monkeypatch) -> None:
    calls = _fake_get_sequence(monkeypatch, [FakeResponse(status_code=404), FakeResponse({"pages": []})])

    result = wiki_tool(title="qwxzv nonsense")

    assert len(calls) == 2
    assert result["error"] == "WikiNotFound"
    assert "lookup" in result["message"]


def test_wiki_exact_hit_does_not_search_or_mark_approximate(fake_http) -> None:
    calls = fake_http(FakeResponse({"type": "standard", "title": "Transformer", "extract": "x"}))

    result = wiki_tool(title="Transformer")

    assert len(calls) == 1
    assert "resolved_from" not in result


def test_wiki_rate_limited_retries_once_with_capped_wait(monkeypatch) -> None:
    import tools.wiki.tool as wiki_module

    sleeps: list[float] = []
    monkeypatch.setattr(wiki_module.time, "sleep", sleeps.append)
    limited = FakeResponse(status_code=429)
    limited.headers = {"retry-after": "60"}
    calls = _fake_get_sequence(monkeypatch, [
        limited,
        FakeResponse({"type": "standard", "title": "Transformer", "extract": "x"}),
    ])

    result = wiki_tool(title="Transformer")

    assert len(calls) == 2
    assert sleeps == [5.0]  # Retry-After 60s capped to 5s
    assert result["items"][0]["title"] == "Transformer"


def test_wiki_server_error_does_not_trigger_search(fake_http) -> None:
    calls = fake_http(FakeResponse(status_code=500))

    result = wiki_tool(title="Anything")

    assert len(calls) == 1
    assert result["error"] == "HTTPError"
    assert result["tool"] == "wiki_summary"


def test_wiki_timeout_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("read timed out"))

    assert wiki_tool(title="Anything")["error"] == "Timeout"


def test_wiki_disambiguation_page_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse({"type": "disambiguation", "title": "Mercury", "extract": "may refer to"}))

    result = wiki_tool(title="Mercury")

    assert result["error"] == "LookupError"
    assert "ambiguous" in result["message"]
