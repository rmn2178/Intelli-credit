"""
Financial Analysis Agent — Computes ratios, runs simulations, generates narrative.
"""
import json
from typing import AsyncGenerator
from core.llm_client import chat_completion, stream_completion
from core.calculations import run_intermediate_calculations, compute_risk_score
from core.causal_engine import CausalEngine
from core.smt_validator import validate_financial_consistency
from models.database import SessionStore

class FinancialAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return
        fin_data = session.get("financial_data", {})
        if not fin_data:
            yield "⚠ No financial data available"; return

        yield "📊 Computing financial ratios...\n"
        calcs = run_intermediate_calculations(fin_data)
        self.store.set_calculations(self.session_id, calcs)
        for name, info in calcs.items():
            val = info.get("value", "N/A")
            status = info.get("status", "")
            unit = info.get("unit", "")
            formula = info.get("formula", "")
            icon = "✅" if status == "GREEN" else ("⚠" if status == "YELLOW" else "🚨")
            yield f"  {icon} {name}: {val}{unit} {formula}"

        yield "\n🔬 Running SMT Symbolic Validation (Double-Lock)..."
        smt = validate_financial_consistency(fin_data)
        session["smt_validation"] = smt
        for check in smt.get("checks", []):
            icon = "✅" if check["status"] == "PASS" else "❌"
            yield f"  {icon} {check['rule']}: {check['status']}"
        yield f"  Overall: {smt.get('overall', 'N/A')} (Solver: {smt.get('solver', 'N/A')})"

        yield "\n🎯 Running Digital Twin Simulation..."
        engine = CausalEngine(fin_data)
        sim = engine.run_comprehensive_simulation()
        self.store.set_simulation_results(self.session_id, sim)
        for scenario in sim.get("scenarios", [])[:5]:
            name = scenario["scenario_name"]
            pd_before = scenario["default_probability_before"] * 100
            pd_after = scenario["default_probability_after"] * 100
            yield f"  📉 {name}: PD {pd_before:.1f}% → {pd_after:.1f}%"

        yield "\n📝 Generating financial narrative..."
        evidence = session.get("evidence", {})
        risk_score = compute_risk_score(calcs, evidence, sim.get("base_risk_score", 0))
        fin_data["risk_score"] = risk_score
        self.store.set_financial_data(self.session_id, fin_data)

        prompt = f"""Generate a professional financial analysis narrative for an Indian bank credit appraisal.

Financial Ratios: {json.dumps(calcs, default=str)}
Risk Score: {risk_score}
Simulation Results: {json.dumps(sim.get('counterfactual_insights', []), default=str)}

Rules:
- Use Indian numbering (Lakhs/Crores)
- Cite every ratio with [Logic: formula]
- Reference RBI benchmarks
- Be concise and professional
- Highlight key risks and strengths"""
        try:
            narrative = await chat_completion(prompt)
            session["financial_narrative"] = narrative
            yield f"\n{narrative[:500]}..."
        except Exception as e:
            yield f"  ⚠ Narrative generation failed: {e}"

        yield f"\n✅ Financial analysis complete. Risk Score: {risk_score:.2f}"
