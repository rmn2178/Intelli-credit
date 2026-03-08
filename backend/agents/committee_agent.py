"""
Committee Agent — Multi-Persona Credit Committee AI.
Three AI personas debate: Risk Officer, Compliance Officer, Business Officer.
Produces structured debate transcript and consensus decision.
"""
import json
from typing import AsyncGenerator
from core.llm_client import chat_completion, stream_completion
from core.regulatory_engine import RegulatoryEngine
from models.database import SessionStore

class CommitteeAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return

        yield "🏛️ Autonomous Credit Committee Convening...\n"
        yield "  👤 Risk Officer AI — analyzing financial risk\n"
        yield "  👤 Compliance Officer AI — verifying regulatory compliance\n"
        yield "  👤 Business Officer AI — assessing growth potential\n\n"

        fd = session.get("financial_data", {})
        calcs = session.get("calculations", {})
        evidence = session.get("evidence", {})
        fraud = session.get("fraud_report", {})
        gst = session.get("gst_report", {})

        context = json.dumps({
            "company": session.get("company_name", "Unknown"),
            "ratios": {k: v.get("value") for k, v in calcs.items()},
            "red_flags": len(evidence.get("red", [])),
            "yellow_flags": len(evidence.get("yellow", [])),
            "green_flags": len(evidence.get("green", [])),
            "fraud_score": fraud.get("fraud_probability", 0),
            "gst_risk": gst.get("risk_level", "N/A"),
            "risk_score": fd.get("risk_score", 0),
        }, default=str)

        debate = {"personas": [], "transcript": ""}

        # Risk Officer
        yield "━━━ RISK OFFICER AI ━━━\n"
        risk_prompt = f"""You are the Risk Officer on a bank credit committee. Analyze:
{context}
Focus on: DSCR, leverage, cash flow volatility, default probability.
Cite ratios with [Logic: formula]. State your position: APPROVE/CONDITIONAL/REJECT.
Be concise (150 words max)."""
        try:
            risk_opinion = await chat_completion(risk_prompt)
            debate["personas"].append({"role": "Risk Officer", "opinion": risk_opinion})
            yield risk_opinion + "\n\n"
        except Exception as e:
            yield f"⚠ Risk Officer error: {e}\n"
            risk_opinion = "Unable to generate — manual review required"

        # Compliance Officer
        yield "━━━ COMPLIANCE OFFICER AI ━━━\n"
        reg = RegulatoryEngine()
        compliance = reg.check_compliance(
            session.get("loan_amount", 0), calcs, fd
        )
        comp_prompt = f"""You are the Compliance Officer. Verify RBI regulatory compliance.
{context}
Compliance results: {json.dumps(compliance, default=str)[:1000]}
Check: exposure limits, DSCR minimums, NPA status, MSME mandates.
State your position: APPROVE/CONDITIONAL/REJECT. Cite regulations. 150 words max."""
        try:
            comp_opinion = await chat_completion(comp_prompt)
            debate["personas"].append({"role": "Compliance Officer", "opinion": comp_opinion})
            yield comp_opinion + "\n\n"
        except Exception as e:
            yield f"⚠ Compliance Officer error: {e}\n"
            comp_opinion = "Unable to generate"

        # Business Officer
        yield "━━━ BUSINESS OFFICER AI ━━━\n"
        biz_prompt = f"""You are the Business Officer. Assess growth potential.
{context}
Focus on: revenue growth, market position, industry outlook, repayment capacity.
Advocate for profitable lending where appropriate.
State your position: APPROVE/CONDITIONAL/REJECT. 150 words max."""
        try:
            biz_opinion = await chat_completion(biz_prompt)
            debate["personas"].append({"role": "Business Officer", "opinion": biz_opinion})
            yield biz_opinion + "\n\n"
        except Exception as e:
            yield f"⚠ Business Officer error: {e}\n"
            biz_opinion = "Unable to generate"

        # Consensus
        yield "━━━ CONSENSUS ENGINE ━━━\n"
        consensus_prompt = f"""You are the Credit Committee Chair. Based on the debate:
Risk Officer: {risk_opinion[:300]}
Compliance Officer: {comp_opinion[:300]}
Business Officer: {biz_opinion[:300]}

Issue FINAL DECISION: Approve / Conditional Approval / Reject.
Include: decision rationale, conditions (if conditional), monitoring requirements.
Format as structured output. 200 words max."""
        try:
            decision_text = await chat_completion(consensus_prompt)
            yield decision_text + "\n"

            # Determine decision
            dt = decision_text.lower()
            if "reject" in dt:
                final = "Reject"
            elif "conditional" in dt:
                final = "Conditional Approval"
            else:
                final = "Approve"

            debate["transcript"] = f"RISK: {risk_opinion}\n\nCOMPLIANCE: {comp_opinion}\n\nBUSINESS: {biz_opinion}\n\nDECISION: {decision_text}"
            debate["final_decision"] = final
            debate["decision_narrative"] = decision_text
            debate["compliance_results"] = compliance
        except Exception as e:
            yield f"⚠ Consensus error: {e}\n"
            debate["final_decision"] = "Manual Review Required"

        self.store.set_committee_debate(self.session_id, debate)
        yield f"\n✅ Committee Decision: {debate.get('final_decision', 'Pending')}"
