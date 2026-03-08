"""
CAM Agent — Credit Appraisal Memorandum Generator.
Produces bank-grade CAM with full evidence citations.
"""
import json
from typing import AsyncGenerator
from core.llm_client import chat_completion, stream_completion
from models.database import SessionStore

class CAMAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return

        yield "📋 Generating Credit Appraisal Memorandum...\n"

        company = session.get("company_name", "Unknown")
        cin = session.get("cin", "N/A")
        gstin = session.get("gstin", "N/A")
        fd = session.get("financial_data", {})
        calcs = session.get("calculations", {})
        evidence = session.get("evidence", {})
        gst = session.get("gst_report", {})
        fraud = session.get("fraud_report", {})
        sim = session.get("simulation_results", {})
        osint = session.get("osint_findings", {})
        unstructured = session.get("unstructured_insights", {})
        loan = session.get("loan_amount", 0)
        purpose = session.get("loan_purpose", "Working Capital")

        cam_data = {
            "company_profile": {"name": company, "cin": cin, "gstin": gstin, "loan_amount": loan, "loan_purpose": purpose},
            "financial_summary": {k: v.get("value") for k, v in calcs.items()},
            "evidence_summary": {"green": len(evidence.get("green",[])), "yellow": len(evidence.get("yellow",[])), "red": len(evidence.get("red",[]))},
            "gst_risk": gst.get("risk_level", "N/A"),
            "fraud_score": fraud.get("fraud_probability", 0),
            "risk_score": fd.get("risk_score", 0),
        }

        prompt = f"""Generate a formal Credit Appraisal Memorandum (CAM) for Indian bank lending.

BORROWER DATA:
{json.dumps(cam_data, default=str, indent=2)}

EVIDENCE FLAGS:
GREEN: {len(evidence.get('green',[]))} verified items
YELLOW: {len(evidence.get('yellow',[]))} items needing attention
RED: {len(evidence.get('red',[]))} critical flags

The CAM MUST include these sections:
1. EXECUTIVE SUMMARY — Decision recommendation with key metrics
2. COMPANY PROFILE — CIN, GSTIN, incorporation, promoters
3. FINANCIAL ANALYSIS — 3 key ratios with [Logic: formula] citations
4. GST RECONCILIATION — GSTR-1 vs P&L, 2A vs 3B findings
5. RISK ASSESSMENT — Top 3 risks with evidence
6. FRAUD SCREENING — Fraud probability and key signals
7. SIMULATION RESULTS — Worst-case scenario impact
8. RECOMMENDATION — Decision + conditions + monitoring

Rules:
- Use Indian numbering (Lakhs/Crores)
- Every claim must cite [Source: Document, Section]
- Every formula must cite [Logic: Formula]
- Be professional and bank-grade
- Maximum 800 words"""

        yield "  Sections: Executive Summary → Company Profile → Financial Analysis..."
        yield "  → GST Reconciliation → Risk Assessment → Fraud Screening..."
        yield "  → Simulation → Recommendation\n"

        try:
            cam_text = ""
            async for chunk in stream_completion(prompt):
                cam_text += chunk
                yield chunk

            cam_report = {
                "company_profile": cam_data["company_profile"],
                "financial_analysis": cam_data["financial_summary"],
                "gst_reconciliation": gst,
                "fraud_assessment": {"probability": fraud.get("fraud_probability", 0), "signals": len(fraud.get("all_signals", []))},
                "risk_matrix": cam_data["evidence_summary"],
                "full_narrative": cam_text,
                "evidence_trail": evidence.get("green", [])[:5] + evidence.get("red", [])[:5],
            }
            self.store.set_cam_report(self.session_id, cam_report)
        except Exception as e:
            yield f"\n⚠ CAM generation error: {e}"
            cam_report = {"full_narrative": "CAM generation failed — manual review required", "company_profile": cam_data["company_profile"]}
            self.store.set_cam_report(self.session_id, cam_report)

        yield "\n\n✅ Credit Appraisal Memorandum generated."
