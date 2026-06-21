# filepath: core/tools.py
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from backend.vendor_logging import get_vendor_logger
from clients.chroma import get_vector_store

# Conditional import configuration for safe execution environments
try:
    from newspaper import Article

    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False


def call_with_budget(
    vendor_id: str, tool_fn, *args, max_calls_per_vendor: int = 5, **kwargs
) -> dict:
    """
    Enforces distinct execution quotas per vendor-tool compound identity over a
    rolling 24-hour cycle using Django's shared cache infrastructure.
    """
    v_logger = get_vendor_logger(vendor_id)
    cache_key = f"tool_budget:{vendor_id}:{tool_fn.__name__}"
    calls_executed = cache.get(cache_key, 0)

    if calls_executed >= max_calls_per_vendor:
        v_logger.warning(
            f"TOOL_BUDGET_EXCEEDED: Quota ceiling hit for {tool_fn.__name__} (vendor={vendor_id})"
        )
        return {
            "tool": tool_fn.__name__,
            "status": "skipped",
            "reason": "budget_exceeded",
            "summary": "This execution path was throttled to preserve structural API budgets.",
        }

    cache.set(cache_key, calls_executed + 1, timeout=86400)
    return tool_fn(vendor_id, *args, **kwargs)


def search_xposedornot_breach(vendor_id: str, domain: str) -> dict:
    """Queries XposedOrNot open-source API framework to detect public data leaks."""
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_xposedornot_breach target_domain={domain}")
    target_url = f"https://api.xposedornot.com/v1/breach-analytics?email=test@{domain}"

    try:
        response = requests.get(
            target_url, headers={"User-Agent": "VendorRiskEngine"}, timeout=10
        )
        if response.status_code == 404:
            return {
                "tool": "xposedornot",
                "status": "ok",
                "breaches_found": 0,
                "summary": f"No historic exposure matrices identified for domain context: {domain}",
            }

        response.raise_for_status()
        payload = response.json()
        breaches_list = payload.get("BreachesSummary", {}).get(
            " there are breaches found for this email", []
        )

        v_logger.info(
            f"TOOL_RESULT: xposedornot identified {len(breaches_list)} exposures for {domain}"
        )
        return {
            "tool": "xposedornot",
            "status": "ok",
            "breaches_found": len(breaches_list),
            "raw_data": payload,
        }
    except Exception as err:
        v_logger.error(f"TOOL_ERROR: xposedornot query collapsed: {str(err)}")
        return {"tool": "xposedornot", "status": "error", "error": str(err)}


def search_tavily(vendor_id: str, query: str, max_results: int = 5) -> dict:
    """Executes a structural, context-aware web investigation search optimized for LLM processing."""
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_tavily runtime_query='{query}'")

    api_key = getattr(settings, "TAVILY_API_KEY", None)
    if not api_key:
        v_logger.warning(
            "TOOL_SKIP: TAVILY_API_KEY configuration token missing from target settings file."
        )
        return {"tool": "tavily", "status": "skipped", "reason": "no_api_key"}

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=15,
        )
        response.raise_for_status()
        results_payload = response.json().get("results", [])
        v_logger.info(
            f"TOOL_RESULT: tavily extracted {len(results_payload)} valid citation nodes."
        )
        return {"tool": "tavily", "status": "ok", "results": results_payload}
    except Exception as err:
        v_logger.error(
            f"TOOL_ERROR: tavily agentic search context raised exception: {str(err)}"
        )
        return {"tool": "tavily", "status": "error", "error": str(err)}


def search_serpapi_news(vendor_id: str, query: str) -> dict:
    """Executes live Google News spatial analytics searches across generic news strings via SerpAPI."""
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_serpapi_news raw_query='{query}'")

    api_key = getattr(settings, "SERPAPI_API_KEY", None)
    if not api_key:
        v_logger.warning(
            "TOOL_SKIP: SERPAPI_API_KEY is currently unconfigured inside environment scopes."
        )
        return {"tool": "serpapi", "status": "skipped", "reason": "no_api_key"}

    search_params = {
        "engine": "google_news",
        "q": query,
        "gl": "us",
        "hl": "en",
        "api_key": api_key,
    }
    try:
        response = requests.get(
            "https://serpapi.com/search", params=search_params, timeout=12
        )
        response.raise_for_status()
        news_results = response.json().get("news_results", [])

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
            for story in news_results[:6]
        ]
        v_logger.info(
            f"TOOL_RESULT: serpapi returned {len(normalized_stories)} parsed news footprints."
        )
        return {"tool": "serpapi", "status": "ok", "stories": normalized_stories}
    except Exception as err:
        v_logger.error(
            f"TOOL_ERROR: serpapi service layer interaction failed: {str(err)}"
        )
        return {"tool": "serpapi", "status": "error", "error": str(err)}


def search_news_breach_signal(vendor_id: str, vendor_name: str) -> dict:
    """Targets systemic corporate vulnerability mentions or structural crises via GNews engine."""
    v_logger = get_vendor_logger(vendor_id)
    constructed_query = f'"{vendor_name}" (breach OR ransomware OR hack OR bankruptcy OR "data exposed")'
    v_logger.info(f"TOOL_CALL: search_news_breach_signal targeted_target={vendor_name}")

    api_key = getattr(settings, "GNEWS_API_KEY", None)
    if not api_key:
        v_logger.warning("TOOL_SKIP: GNEWS_API_KEY missing from context properties.")
        return {"tool": "gnews", "status": "skipped", "reason": "no_api_key"}

    try:
        response = requests.get(
            "https://gnews.io/api/v4/search",
            params={"q": constructed_query, "lang": "en", "max": 6, "apikey": api_key},
            timeout=10,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
        v_logger.info(
            f"TOOL_RESULT: gnews located {len(articles)} explicit adversarial anomalies."
        )
        return {"tool": "gnews", "status": "ok", "articles": articles}
    except Exception as err:
        v_logger.error(
            f"TOOL_ERROR: gnews target scraping protocol dropped completely: {str(err)}"
        )
        return {"tool": "gnews", "status": "error", "error": str(err)}


def search_sec_edgar(vendor_id: str, company_name: str = None, query: str = None) -> dict:
    company_name = company_name or query  # accept either argument name
    """Full-text search engine utility accessing non-authenticated public regulatory filing repositories."""
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: search_sec_edgar query_target={company_name}")
    try:
        response = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": company_name, "forms": "8-K,10-K"},
            headers={"User-Agent": "VendorRiskEngine research@yourorg.com"},
            timeout=10,
        )
        response.raise_for_status()
        filing_hits = response.json().get("hits", {}).get("hits", [])
        v_logger.info(
            f"TOOL_RESULT: sec_edgar located {len(filing_hits)} active listings."
        )
        return {"tool": "sec_edgar", "status": "ok", "filings": filing_hits[:5]}
    except Exception as err:
        v_logger.error(f"TOOL_ERROR: sec_edgar database connection drop: {str(err)}")
        return {"tool": "sec_edgar", "status": "error", "error": str(err)}


def scrape_public_url_content(vendor_id: str, target_url: str) -> dict:
    """Strips clean raw text content from external targets with automated fallback pipelines."""
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: scrape_public_url_content endpoint={target_url}")

    if HAS_NEWSPAPER:
        try:
            article = Article(target_url)
            article.download()
            article.parse()
            v_logger.info(
                f"TOOL_RESULT: Extracted {len(article.text)} raw data bytes via Newspaper4k core engine."
            )
            return {
                "tool": "web_scraper",
                "status": "ok",
                "title": article.title,
                "extracted_text": article.text[:4000],
            }
        except Exception as engine_err:
            v_logger.warning(
                f"Newspaper4k parsing execution hit error bounds. Engaging backup parser: {str(engine_err)}"
            )

    try:
        headers = {"User-Agent": "Mozilla/5.0 VendorRiskEngine/1.0"}
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for bad_tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            bad_tag.extract()

        consolidated_text = " ".join(soup.get_text().split())
        return {
            "tool": "web_scraper",
            "status": "ok",
            "title": soup.title.string
            if soup.title
            else "Manually Reconstructed DOM Content Target",
            "extracted_text": consolidated_text[:3500],
        }
    except Exception as final_err:
        v_logger.error(
            f"TOOL_ERROR: All structural web scraper fallbacks failed for node: {str(final_err)}"
        )
        return {"tool": "web_scraper", "status": "error", "error": str(final_err)}


def query_vendor_rag(vendor_id: str, question: str, n_results: int = 4) -> dict:
    """Vector data retrieval path checking existing document segment records inside local database blocks."""
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"TOOL_CALL: query_vendor_rag contextual_query='{question}'")
    try:
        vector_store_manager = get_vector_store()
        collection = vector_store_manager.get_vendor_collection(vendor_id)
        raw_results = collection.query(query_texts=[question], n_results=n_results)

        text_chunks = raw_results.get("documents", [[]])[0]
        meta_blocks = raw_results.get("metadatas", [[]])[0]

        v_logger.info(
            f"TOOL_RESULT: vendor_rag surfaced {len(text_chunks)} active contextual definitions."
        )
        return {
            "tool": "vendor_rag",
            "status": "ok",
            "chunks": [
                {"text": txt, "metadata": meta}
                for txt, meta in zip(text_chunks, meta_blocks)
            ],
        }
    except Exception as err:
        v_logger.error(f"TOOL_ERROR: internal vendor_rag pipeline failure: {str(err)}")
        return {"tool": "vendor_rag", "status": "error", "error": str(err)}


# Explicit array of tools requiring external network budgeting boundaries
BUDGETED_TOOLS = {
    "search_xposedornot_breach",
    "search_hibp_breach",
    "search_tavily",
    "search_serpapi_news",
    "search_news_breach_signal",
    "scrape_public_url_content",
    "check_company_registration",
}


def _wrap_with_budget(name, core_function):
    if name not in BUDGETED_TOOLS:
        return core_function

    def wrapped(vendor_id, *args, **kwargs):
        return call_with_budget(
            vendor_id, core_function, *args, max_calls_per_vendor=5, **kwargs
        )

    wrapped.__name__ = core_function.__name__
    return wrapped


# Construct the immutable framework map exposed to the agent loop
BASE_REGISTRY = {
    "search_xposedornot_breach": search_xposedornot_breach,
    "search_tavily": search_tavily,
    "search_serpapi_news": search_serpapi_news,
    "search_news_breach_signal": search_news_breach_signal,
    "scrape_public_url_content": scrape_public_url_content,
    "search_sec_edgar": search_sec_edgar,
    "query_vendor_rag": query_vendor_rag,
}

TOOL_REGISTRY = {
    name: _wrap_with_budget(name, fn) for name, fn in BASE_REGISTRY.items()
}
