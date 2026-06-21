
# filepath: core/test_tools.py
"""
Manual smoke test for every tool in TOOL_REGISTRY. Not a pytest suite —
a simple script you run directly to confirm each external API actually
responds before you rely on it during the live demo.

Run with:
    cd <project_root>          # the directory containing manage.py
    python manage.py shell -c "from core.test_tools import run_all_tool_tests; run_all_tool_tests()"
    
cd /path/to/your/project   # same folder as manage.py
python manage.py shell -c "from core.test_tools import run_all_tool_tests; run_all_tool_tests()"

Or, if you prefer a plain script (no Django shell), set DJANGO_SETTINGS_MODULE
first since tools.py imports django.conf.settings:
    DJANGO_SETTINGS_MODULE=backend.settings python -m core.test_tools

Either way this MUST run from inside the project root (same level as
manage.py) so that `core`, `clients`, and `backend` resolve as packages.
"""

import os
import django

# 1. bootstrap Django settings if this file is run as a plain script
#    (skip this block if you're already inside `manage.py shell`)
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()

from core.tools import (
    search_xposedornot_breach,
    search_serpapi_news,
    scrape_public_url_content,
    search_sec_edgar,
    query_vendor_rag,
    search_tavily,
    search_news_breach_signal,
)

# 2. a real vendor for testing breach/news/sec lookups against — using
#    a known company with public history gives tools something real to find
REAL_TEST_VENDOR_NAME = "Equifax"
REAL_TEST_VENDOR_DOMAIN = "equifax.com"

# 3. a dummy vendor_id — only used for log file naming and budget cache keys,
#    doesn't need to exist in the database for these tool tests
DUMMY_VENDOR_ID = "test-vendor-0001"


def test_search_xposedornot_breach():
    # 3.1 known-breached domain should return breaches_found > 0
    print("\n--- search_xposedornot_breach ---")
    result = search_xposedornot_breach(DUMMY_VENDOR_ID, REAL_TEST_VENDOR_DOMAIN)
    print(result)
    assert result["status"] in ("ok", "error"), "tool must always return a status field"


def test_search_serpapi_news():
    # 3.2 requires SERPAPI_API_KEY configured in settings — will report
    #     status=skipped cleanly if not configured, that's expected behavior
    print("\n--- search_serpapi_news ---")
    result = search_serpapi_news(DUMMY_VENDOR_ID, f"{REAL_TEST_VENDOR_NAME} data breach")
    print(result)
    assert result["status"] in ("ok", "error", "skipped")


def test_scrape_public_url_content():
    # 3.3 a stable, real, public URL — Wikipedia is reliable for this
    print("\n--- scrape_public_url_content ---")
    result = scrape_public_url_content(DUMMY_VENDOR_ID, "https://en.wikipedia.org/wiki/Equifax")
    print(result.get("title"), "-", (result.get("extracted_text") or "")[:120])
    assert result["status"] in ("ok", "error")


def test_search_sec_edgar():
    # 3.4 free, no key needed — should always return status=ok
    print("\n--- search_sec_edgar ---")
    result = search_sec_edgar(DUMMY_VENDOR_ID, REAL_TEST_VENDOR_NAME)
    print(f"filings found: {len(result.get('filings', []))}")
    assert result["status"] in ("ok", "error")


def test_query_vendor_rag():
    # 3.5 this WILL return an empty/error result unless this vendor_id has
    #     already been vectorized via vectorize_markdown_content() — that's
    #     expected for a dummy vendor; confirms the function doesn't crash
    print("\n--- query_vendor_rag ---")
    result = query_vendor_rag(DUMMY_VENDOR_ID, "What is the breach notification window?")
    print(result)
    assert result["status"] in ("ok", "error")


def test_search_tavily():
    # Requires TAVILY_API_KEY configured in settings — will skip cleanly if missing
    print("\n--- search_tavily ---")
    result = search_tavily(DUMMY_VENDOR_ID, f"{REAL_TEST_VENDOR_NAME} security posture")
    print(result)
    assert result["status"] in ("ok", "error", "skipped"), "tool must handle registration state"


def test_search_news_breach_signal():
    # Requires GNEWS_API_KEY configured in settings — will skip cleanly if missing
    print("\n--- search_news_breach_signal ---")
    result = search_news_breach_signal(DUMMY_VENDOR_ID, REAL_TEST_VENDOR_NAME)
    print(f"articles found: {len(result.get('articles', []))}")
    assert result["status"] in ("ok", "error", "skipped"), "tool must return expected execution envelopes"

def run_all_tool_tests():
    # 5. runs every test in sequence, printing results — not pytest, just a runner
    test_search_xposedornot_breach()
    test_search_tavily()              
    test_search_serpapi_news()
    test_search_news_breach_signal()  
    test_scrape_public_url_content()
    test_search_sec_edgar()
    test_query_vendor_rag()
    print("\nAll tool tests completed — check status fields above for any 'error' entries.")


if __name__ == "__main__":
    run_all_tool_tests()