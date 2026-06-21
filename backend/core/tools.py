# core/tools.py
import os
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from backend.logging import get_vendor_logger
from backend.clients.chroma import get_vector_store
from django.core.cache import cache

try:
    from newspaper import Article

    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False


# BUDGET WRAPPER
def call_with_budget(
    vendor_id: str, tool_fn, *args, max_calls_per_vendor: int = 5, **kwargs
) -> dict:
    """Enforces operational API call budget limits per vendor tracking frame via Redis cache."""

    v_logger = get_vendor_logger(vendor_id)
    key = f"tool_budget:{vendor_id}:{tool_fn.__name__}"
    used = cache.get(key, 0)

    if used >= max_calls_per_vendor:
        v_logger.warning(
            f"TOOL_BUDGET_EXCEEDED: {tool_fn.__name__} for vendor={vendor_id}"
        )
        return {
            "tool": tool_fn.__name__,
            "status": "skipped",
            "reason": "budget_exceeded",
        }

    cache.set(key, used + 1, timeout=86400)
    return tool_fn(vendor_id, *args, **kwargs)


# GROUP B — BREACH & THREAT INTELLIGENCE (Fortified)
def search_xposedornot_breach(vendor_id: str, domain: str) -> dict:
    """
    Queries XposedOrNot open-source API framework to detect public credential analytics
    and infrastructure domain exposure leaks without commercial gating.
    """
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_xposedornot_breach domain={domain}")
    url = f"https://api.xposedornot.com/v1/breach-analytics?email=test@{domain}"

    try:
        resp = requests.get(url, headers={"User-Agent": "VendorRiskEngine"}, timeout=10)
        if resp.status_code == 404:
            return {
                "tool": "xposedornot",
                "status": "ok",
                "breaches_found": 0,
                "summary": "No domain metrics identified.",
            }

        resp.raise_for_status()
        data = resp.json()
        breach_summary = data.get("BreachesSummary", {})
        exposed_breaches = breach_summary.get(
            " there are breaches found for this email", []
        )

        v_logger.info(
            f"TOOL_RESULT: xposedornot found={len(exposed_breaches)} records for domain={domain}"
        )
        return {
            "tool": "xposedornot",
            "status": "ok",
            "breaches_found": len(exposed_breaches),
            "raw_data": data,
        }
    except Exception as e:
        v_logger.error(f"TOOL_ERROR: xposedornot fallback caught: {str(e)}")
        return {"tool": "xposedornot", "status": "error", "error": str(e)}


def search_serpapi_news(vendor_id: str, query: str) -> dict:
    """
    Executes a generic Google News engine search using SerpAPI with an LLM-generated query string.
    Returns clean, structured news metadata snippets without vendor-specific hardcoding.
    """
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_serpapi_news query='{query}'")
    api_key = getattr(settings, "SERPAPI_API_KEY", None)
    if not api_key:
        v_logger.warning(
            "TOOL_SKIP: SERPAPI_API_KEY unconfigured. Aborting call execution."
        )
        return {"tool": "serpapi", "status": "skipped", "reason": "no_api_key"}
    params = {
        "engine": "google_news",
        "q": query,
        "gl": "us",
        "hl": "en",
        "api_key": api_key,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=12)
        resp.raise_for_status()
        news_results = resp.json().get("news_results", [])

        normalized_stories = [
            {
                "title": story.get("title"),
                "source": story.get("source", {}).get("name")
                if isinstance(story.get("source"), dict)
                else story.get("source"),
                "link": story.get("link"),
                "snippet": story.get("snippet"),
                "published_date": story.get("date"),
            }
            for story in news_results[:6]  # Cap results
        ]

        v_logger.info(
            f"TOOL_RESULT: serpapi loaded={len(normalized_stories)} articles for query."
        )
        return {"tool": "serpapi", "status": "ok", "stories": normalized_stories}

    except Exception as e:
        v_logger.error(f"TOOL_ERROR: serpapi endpoint dropped connection: {str(e)}")
        return {"tool": "serpapi", "status": "error", "error": str(e)}


# GROUP C — PUBLIC KNOWLEDGE & SCRAPING ENGINE (Newspaper4k)
def scrape_public_url_content(vendor_id: str, target_url: str) -> dict:
    """
    Parses clean body copy from an external public text target (Wikipedia node, corporate notice, press release)
    using Newspaper4k or an automated BeautifulSoup parser fallback.
    """
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: scrape_public_url_content url={target_url}")

    if HAS_NEWSPAPER:
        try:
            article = Article(target_url)
            article.download()
            article.parse()
            v_logger.info(
                f"TOOL_RESULT: Scraped text length={len(article.text)} via Newspaper4k engine."
            )
            return {
                "tool": "web_scraper",
                "status": "ok",
                "title": article.title,
                "extracted_text": article.text[
                    :4000
                ],  # Cap text chunk inside parameter limits
            }
        except Exception as e:
            v_logger.warning(
                f"Newspaper4k engine failed processing URL, launching soup fallback. Info: {e}"
            )

    # Manual BeautifulSoup structural fallback pipeline
    try:
        headers = {"User-Agent": "Mozilla/5.0 VendorRiskEngine/1.0"}
        resp = requests.get(target_url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Kill unnecessary code components
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.extract()

        clean_text = " ".join(soup.get_text().split())
        return {
            "tool": "web_scraper",
            "status": "ok",
            "title": soup.title.string if soup.title else "Parsed Target Document",
            "extracted_text": clean_text[:3500],
        }
    except Exception as fail_err:
        v_logger.error(
            f"TOOL_ERROR: Web scraper failed parsing completely: {str(fail_err)}"
        )
        return {"tool": "web_scraper", "status": "error", "error": str(fail_err)}


# GROUP D — EXISTING STABLE TOOL INHERITANCE
def search_sec_edgar(vendor_id: str, company_name: str) -> dict:
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_sec_edgar company={company_name}")
    try:
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": company_name, "forms": "8-K,10-K"},
            headers={"User-Agent": "VendorRiskEngine research@yourorg.com"},
            timeout=10,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", {}).get("hits", [])
        v_logger.info(f"TOOL_RESULT: sec_edgar found={len(hits)} filings")
        return {"tool": "sec_edgar", "status": "ok", "filings": hits[:5]}
    except Exception as e:
        v_logger.error(f"TOOL_ERROR: sec_edgar: {str(e)}")
        return {"tool": "sec_edgar", "status": "error", "error": str(e)}


def query_vendor_rag(vendor_id: str, question: str, n_results: int = 4) -> dict:
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: query_vendor_rag question='{question}'")
    try:
        store = get_vector_store()
        collection = store.get_vendor_collection(vendor_id)
        results = collection.query(query_texts=[question], n_results=n_results)
        chunks = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        v_logger.info(f"TOOL_RESULT: rag retrieved={len(chunks)} chunks")
        return {
            "tool": "vendor_rag",
            "status": "ok",
            "chunks": [{"text": c, "metadata": m} for c, m in zip(chunks, metadatas)],
        }
    except Exception as e:
        v_logger.error(f"TOOL_ERROR: vendor_rag {str(e)}")
        return {"tool": "vendor_rag", "status": "error", "error": str(e)}


BUDGETED_TOOLS = {
    "search_serpapi_news",
    "search_xposedornot_breach",
    "scrape_public_url_content",
}


def _wrap_with_budget(name, fn):
    if name not in BUDGETED_TOOLS:
        return fn

    def wrapped(vendor_id, *args, **kwargs):
        return call_with_budget(vendor_id, fn, *args, max_calls_per_vendor=5, **kwargs)

    wrapped.__name__ = fn.__name__
    return wrapped


TOOL_REGISTRY = {
    "search_xposedornot_breach": search_xposedornot_breach,
    "search_serpapi_news": search_serpapi_news,
    "scrape_public_url_content": scrape_public_url_content,
    "search_sec_edgar": search_sec_edgar,
    "query_vendor_rag": query_vendor_rag,
}
TOOL_REGISTRY = {
    name: _wrap_with_budget(name, fn) for name, fn in TOOL_REGISTRY.items()
}
