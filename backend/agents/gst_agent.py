"""
GST Reconciliation Agent — Dedicated GST cross-verification.
GSTR-1 vs P&L, GSTR-2A vs GSTR-3B, circular trading, accommodation entries.
"""
from typing import AsyncGenerator
from core.llm_client import chat_completion
from models.database import SessionStore

class GSTAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return
        fd = session.get("financial_data", {})

        yield "🧾 Running GST Reconciliation Analysis...\n"

        revenue = fd.get("revenue", 0)
        g1 = fd.get("gstr1_sales", 0)
        g3b = fd.get("gstr3b_sales", 0)
        itc_2a = fd.get("gstr2a_itc_available", 0)
        itc_3b = fd.get("gstr3b_tax_paid", 0)

        gst_report = {"checks": [], "risk_level": "LOW"}

        # Check 1: GSTR-1 vs P&L Revenue
        if revenue > 0 and g1 > 0:
            ratio = g1 / revenue
            if ratio > 1.15:
                gst_report["checks"].append({"check": "GSTR-1 vs P&L Revenue", "status": "RED", "ratio": round(ratio, 3), "detail": f"GSTR-1 ({g1:,.0f}) exceeds P&L revenue ({revenue:,.0f}) by {(ratio-1)*100:.1f}%. Potential circular trading / accommodation entries.", "citation": "[Source: GSTR-1, P&L Statement] [Logic: GSTR-1 Outward Supplies / P&L Revenue > 1.15]"})
                gst_report["risk_level"] = "HIGH"
                yield f"  🚨 RED: GSTR-1/P&L ratio = {ratio:.3f} — Circular trading risk"
            elif ratio > 1.05:
                gst_report["checks"].append({"check": "GSTR-1 vs P&L Revenue", "status": "YELLOW", "ratio": round(ratio, 3), "detail": f"Minor variance. Monitor closely.", "citation": "[Source: GSTR-1, P&L Statement]"})
                yield f"  ⚠ YELLOW: GSTR-1/P&L ratio = {ratio:.3f} — Mild mismatch"
            else:
                gst_report["checks"].append({"check": "GSTR-1 vs P&L Revenue", "status": "GREEN", "ratio": round(ratio, 3), "detail": "Consistent", "citation": "[Source: GSTR-1, P&L Statement]"})
                yield f"  ✅ GREEN: GSTR-1/P&L ratio = {ratio:.3f} — Consistent"

        # Check 2: GSTR-3B vs P&L
        if revenue > 0 and g3b > 0:
            ratio = g3b / revenue
            status = "GREEN" if 0.95 <= ratio <= 1.05 else ("YELLOW" if 0.85 <= ratio <= 1.15 else "RED")
            gst_report["checks"].append({"check": "GSTR-3B vs P&L Revenue", "status": status, "ratio": round(ratio, 3), "citation": "[Source: GSTR-3B, P&L Statement]"})
            icon = "✅" if status == "GREEN" else ("⚠" if status == "YELLOW" else "🚨")
            yield f"  {icon} {status}: GSTR-3B/P&L ratio = {ratio:.3f}"
            if status == "RED" and gst_report["risk_level"] != "HIGH":
                gst_report["risk_level"] = "HIGH"

        # Check 3: ITC Reconciliation (GSTR-2A vs GSTR-3B)
        if itc_2a > 0 and itc_3b > 0:
            ratio = itc_3b / itc_2a
            if ratio > 1.20:
                gst_report["checks"].append({"check": "ITC Reconciliation (2A vs 3B)", "status": "RED", "ratio": round(ratio, 3), "detail": f"ITC claimed ({itc_3b:,.0f}) exceeds auto-drafted 2A ({itc_2a:,.0f}) by {(ratio-1)*100:.1f}%. Rule 36(4) violation risk.", "citation": "[Source: GSTR-2A, GSTR-3B] [Logic: CBIC Rule 36(4)]"})
                gst_report["risk_level"] = "HIGH"
                yield f"  🚨 RED: ITC ratio = {ratio:.3f} — Rule 36(4) violation risk"
            elif ratio > 1.0:
                gst_report["checks"].append({"check": "ITC Reconciliation (2A vs 3B)", "status": "YELLOW", "ratio": round(ratio, 3)})
                yield f"  ⚠ YELLOW: ITC ratio = {ratio:.3f} — Minor excess"
            else:
                gst_report["checks"].append({"check": "ITC Reconciliation (2A vs 3B)", "status": "GREEN", "ratio": round(ratio, 3)})
                yield f"  ✅ GREEN: ITC ratio = {ratio:.3f} — Compliant"

        session["gst_report"] = gst_report
        yield f"\n✅ GST Reconciliation complete. Risk Level: {gst_report['risk_level']}"
