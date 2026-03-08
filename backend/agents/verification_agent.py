"""
Verification & OSINT Agent — External web verification + OSINT collection.
India-targeted: NCLT, MCA, SEBI, RBI, ED, Income Tax investigations.
"""
from typing import AsyncGenerator
from core.web_search import web_search
from core.osint_collector import collect_osint
from core.llm_client import chat_completion
from models.database import SessionStore

class VerificationAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run_verification(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return
        company = session.get("company_name", "Unknown Company")
        yield f"🔎 Running external verification for {company}...\n"

        queries = [
            f'"{company}" NCLT insolvency proceedings',
            f'"{company}" MCA ROC filing compliance',
            f'"{company}" SEBI penalty enforcement',
            f'"{company}" RBI defaulter list',
            f'"{company}" fraud investigation news India',
        ]
        all_results = []
        for q in queries:
            results = await web_search(q, num_results=3)
            all_results.extend(results)
            for r in results:
                yield f"  📰 [{r.get('source','Web')}] {r.get('title','')}"

        session["verification_results"] = all_results
        yield f"\n✅ Web verification complete. {len(all_results)} results found."

    async def run_osint(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return
        company = session.get("company_name", "Unknown Company")
        yield f"🕵️ Running OSINT intelligence collection for {company}...\n"

        osint = await collect_osint(company)
        session["osint_findings"] = osint
        for cat, data in osint.get("categories", {}).items():
            sev = data.get("severity", "LOW")
            icon = "🚨" if sev == "HIGH" else ("⚠" if sev == "MEDIUM" else "✅")
            yield f"  {icon} {cat}: {sev} ({data.get('count',0)} findings)"

        if osint.get("risk_signals"):
            yield "\n⚠ Risk Signals:"
            for sig in osint["risk_signals"]:
                yield f"  🚨 {sig}"

        yield "\n📝 Generating CRM Intelligence Report..."
        try:
            prompt = f"""Generate a Corporate Risk Management (CRM) intelligence report for {company}.
OSINT Findings: {str(osint)[:2000]}
Cite every finding. Use Indian regulatory context. Be concise."""
            report = await chat_completion(prompt)
            session["crm_report"] = report
            yield f"  {report[:300]}..."
        except Exception as e:
            yield f"  ⚠ Report generation failed: {e}"

        yield f"\n✅ OSINT complete. Total findings: {osint.get('total_findings', 0)}"
