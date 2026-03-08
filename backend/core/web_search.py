"""
Web Search module — external intelligence from Indian regulatory domains.
"""
import os
import httpx

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")

async def web_search(query: str, num_results: int = 5) -> list[dict]:
    if SEARCH_API_KEY and SEARCH_ENGINE_ID:
        return await _live_search(query, num_results)
    return _demo_results(query)

async def _live_search(query: str, num_results: int) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": SEARCH_API_KEY, "cx": SEARCH_ENGINE_ID, "q": query, "num": min(num_results, 10)},
            )
            resp.raise_for_status()
            data = resp.json()
            return [{"title": i.get("title",""), "snippet": i.get("snippet",""), "link": i.get("link",""), "source": "Google Search"} for i in data.get("items",[])]
    except Exception:
        return _demo_results(query)

def _demo_results(query: str) -> list[dict]:
    q = query.lower()
    results = []
    if any(w in q for w in ["nclt","litigation","court"]):
        results.append({"title":"NCLT — No pending cases","snippet":"No active NCLT proceedings found. No insolvency applications under IBC 2016.","link":"https://nclt.gov.in","source":"NCLT (Demo)"})
    if any(w in q for w in ["mca","roc","director","din"]):
        results.append({"title":"MCA-21 — Company Active","snippet":"All annual returns filed on time. No director disqualifications.","link":"https://mca.gov.in","source":"MCA-21 (Demo)"})
    if any(w in q for w in ["sebi","insider","penalty"]):
        results.append({"title":"SEBI — No penalties","snippet":"No enforcement actions found.","link":"https://sebi.gov.in","source":"SEBI (Demo)"})
    if any(w in q for w in ["rbi","default"]):
        results.append({"title":"RBI — Not in defaulter list","snippet":"Not in RBI wilful defaulter list or CRILC database.","link":"https://rbi.org.in","source":"RBI (Demo)"})
    if any(w in q for w in ["news","sentiment","layoff"]):
        results.append({"title":"Moneycontrol — Sector Positive","snippet":"Indian SaaS sector showing strong growth. No negative news.","link":"https://moneycontrol.com","source":"Moneycontrol (Demo)"})
    if not results:
        results.append({"title":f"Search: {query}","snippet":"No adverse findings in Indian regulatory databases.","link":"#","source":"Demo"})
    return results[:5]
