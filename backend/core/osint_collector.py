"""
OSINT Collector — India-specific investigative intelligence gathering.
Queries NCLT, MCA, SEBI, RBI, ED, and Income Tax domains.
"""
from core.web_search import web_search

CATEGORY_QUERIES = {
    "litigation": '"{company}" AND ("NCLT" OR "Supreme Court" OR "High Court" OR "e-Courts" OR "arbitration")',
    "regulatory": '"{company}" AND ("MCA" OR "SEBI" OR "RBI penalty" OR "ED raid" OR "Income Tax Notice")',
    "sentiment": '"{company}" AND ("Moneycontrol" OR "Economic Times" OR "Livemint" OR "fraud" OR "delay in wages")',
    "director_check": '"{company}" directors AND ("disqualified" OR "DIN deactivated" OR "defaulter")',
    "gst_fraud": '"{company}" AND ("GST fraud" OR "fake invoice" OR "circular trading" OR "ITC fraud")',
}

async def collect_osint(company_name: str) -> dict:
    findings = {"company": company_name, "categories": {}, "total_findings": 0, "risk_signals": []}
    for category, query_template in CATEGORY_QUERIES.items():
        query = query_template.replace("{company}", company_name)
        results = await web_search(query, num_results=3)
        severity = _assess_severity(category, results)
        findings["categories"][category] = {"query": query, "results": results, "severity": severity, "count": len(results)}
        findings["total_findings"] += len(results)
        if severity == "HIGH":
            findings["risk_signals"].append(f"HIGH risk signal in {category}: {results[0]['title']}" if results else f"HIGH risk in {category}")
    return findings

def _assess_severity(category: str, results: list[dict]) -> str:
    if not results:
        return "LOW"
    text = " ".join(r.get("snippet","").lower() for r in results)
    high_keywords = ["fraud","penalty","raid","default","disqualified","npa","wilful","suspended"]
    medium_keywords = ["notice","investigation","warning","audit qualification","delay"]
    if any(kw in text for kw in high_keywords):
        return "HIGH"
    if any(kw in text for kw in medium_keywords):
        return "MEDIUM"
    return "LOW"
