"""
Fraud Radar Agent — AI Financial Forensics System.
Detects circular GST trading, fake invoices, shell companies,
promoter fund diversion, suspicious vendor relationships.
"""
import json
from typing import AsyncGenerator
from core.knowledge_graph import FinancialKnowledgeGraph
from core.llm_client import chat_completion
from core.federated_stub import get_federated_signals
from models.database import SessionStore

class FraudRadarAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return

        yield "🛡️ AI Fraud Radar Engine Starting...\n"

        # Build knowledge graph
        yield "📊 Constructing Financial Transaction Graph..."
        kg = FinancialKnowledgeGraph()
        kg.build_from_financial_data(session)
        yield f"  Nodes: {kg.graph.number_of_nodes()} | Edges: {kg.graph.number_of_edges()}"

        # Run fraud detection
        yield "\n🔍 Running Graph Neural Network Analysis..."
        analysis = kg.run_full_analysis()

        # Report findings
        circular = analysis.get("circular_trading", [])
        shells = analysis.get("shell_companies", [])
        clusters = analysis.get("vendor_clusters", [])
        diversions = analysis.get("fund_diversions", [])

        if circular:
            yield f"\n🚨 CIRCULAR TRADING DETECTED ({len(circular)} loops):"
            for c in circular:
                yield f"  → {c['description']}"
        else:
            yield "\n✅ No circular trading loops detected"

        if shells:
            yield f"\n🚨 SHELL COMPANY PATTERNS ({len(shells)}):"
            for s in shells:
                yield f"  → {s['description']}"
        else:
            yield "\n✅ No shell company patterns detected"

        if clusters:
            yield f"\n⚠ SUSPICIOUS VENDOR CLUSTERS ({len(clusters)}):"
            for cl in clusters:
                yield f"  → {cl['description']}"
        else:
            yield "\n✅ No suspicious vendor clusters"

        if diversions:
            yield f"\n🚨 FUND DIVERSION PATTERNS ({len(diversions)}):"
            for d in diversions:
                yield f"  → {d['description']}"
        else:
            yield "\n✅ No fund diversion patterns detected"

        # Federated intelligence
        yield "\n🌐 Checking Federated Intelligence Network..."
        company = session.get("company_name", "")
        gstin = session.get("gstin", "")
        fed = get_federated_signals(company, gstin)
        yield f"  Cross-bank exposure: {fed['cross_bank_exposure']['total_facilities']} facilities"
        yield f"  SMA Status: {fed['cross_bank_exposure']['sma_status']}"
        yield f"  Sector default rate: {fed['systemic_risk']['sector_default_rate_pct']}%"

        # Compute fraud probability
        fp = analysis.get("fraud_probability", 0)
        yield f"\n🎯 Fraud Probability Score: {fp:.2f}"

        # LLM narrative
        yield "\n📝 Generating Fraud Investigation Narrative..."
        try:
            prompt = f"""Generate a forensic fraud analysis narrative.
Graph findings: {json.dumps(analysis.get('all_signals', []), default=str)[:1500]}
Federated signals: {json.dumps(fed, default=str)[:500]}
Fraud probability: {fp}
Rules: Cite document/transaction references. Use Indian financial context."""
            narrative = await chat_completion(prompt)
            analysis["narrative"] = narrative
            yield f"  {narrative[:300]}..."
        except Exception:
            pass

        analysis["federated"] = fed
        analysis["graph_summary"] = kg.get_graph_summary()
        self.store.set_fraud_report(self.session_id, analysis)

        yield f"\n✅ Fraud Radar complete. Score: {fp:.2f} | Signals: {analysis['total_signals']}"
