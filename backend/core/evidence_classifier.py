"""
Evidence Classification Engine — GREEN / YELLOW / RED
Cross-verifies extracted financial data across document types.
Includes GST circular trading detection, ITC discrepancy detection,
CIN/GSTIN validation, and Indian regulatory compliance checks.
"""

from typing import Any
import re


def classify_evidence(
    financial_data: dict,
    document_types: list[str],
) -> dict[str, list[dict]]:
    """
    Compare extracted data across document types and classify each finding.
    Returns {"green": [...], "yellow": [...], "red": [...]}
    """
    green, yellow, red = [], [], []

    # ─── 1. Revenue Cross-Check: P&L vs GST ──────────────────────────────
    revenue = financial_data.get("revenue")
    gstr1_sales = financial_data.get("gstr1_sales")
    gstr3b_sales = financial_data.get("gstr3b_sales")

    if revenue and gstr3b_sales:
        ratio = gstr3b_sales / revenue if revenue > 0 else 0
        if 0.95 <= ratio <= 1.05:
            green.append({
                "variable": "revenue_vs_gst",
                "summary": f"✓ P&L Revenue ({_fmt(revenue)}) matches GSTR-3B sales ({_fmt(gstr3b_sales)}) within 5%.",
                "formula": "[Logic: GSTR-3B taxable value / P&L Revenue]",
                "value": round(ratio, 3),
                "sources": ["Profit & Loss", "GSTR-3B"],
            })
        elif 0.85 <= ratio < 0.95 or 1.05 < ratio <= 1.15:
            yellow.append({
                "variable": "revenue_vs_gst",
                "summary": f"⚠ Moderate mismatch: P&L Revenue ({_fmt(revenue)}) vs GSTR-3B ({_fmt(gstr3b_sales)}). Ratio: {ratio:.2f}",
                "formula": "[Logic: GSTR-3B taxable value / P&L Revenue]",
                "value": round(ratio, 3),
                "sources": ["Profit & Loss", "GSTR-3B"],
            })
        else:
            red.append({
                "variable": "revenue_vs_gst",
                "summary": f"🚨 Significant mismatch: P&L Revenue ({_fmt(revenue)}) vs GSTR-3B ({_fmt(gstr3b_sales)}). Ratio: {ratio:.2f}",
                "formula": "[Logic: GSTR-3B taxable value / P&L Revenue]",
                "value": round(ratio, 3),
                "sources": ["Profit & Loss", "GSTR-3B"],
            })

    # ─── 2. Circular Trading Detection: GSTR-1 vs P&L ────────────────────
    if revenue and gstr1_sales:
        ratio = gstr1_sales / revenue if revenue > 0 else 0
        if ratio <= 1.05:
            green.append({
                "variable": "circular_trading_check",
                "summary": f"✓ GSTR-1 sales ({_fmt(gstr1_sales)}) consistent with P&L revenue ({_fmt(revenue)}). No circular trading indicators.",
                "formula": "[Logic: GSTR-1 outward supplies / P&L Revenue ≤ 1.05]",
                "value": round(ratio, 3),
                "sources": ["GSTR-1", "Profit & Loss"],
            })
        elif ratio <= 1.15:
            yellow.append({
                "variable": "circular_trading_check",
                "summary": f"⚠ GSTR-1 sales ({_fmt(gstr1_sales)}) exceed P&L revenue ({_fmt(revenue)}) by {(ratio-1)*100:.1f}%. Mild circular trading risk.",
                "formula": "[Logic: GSTR-1 / P&L Revenue between 1.05–1.15 = YELLOW]",
                "value": round(ratio, 3),
                "sources": ["GSTR-1", "Profit & Loss"],
            })
        else:
            red.append({
                "variable": "circular_trading_check",
                "summary": f"🚨 Potential Circular Trading / Accommodation Entries: GSTR-1 ({_fmt(gstr1_sales)}) exceeds P&L revenue ({_fmt(revenue)}) by {(ratio-1)*100:.1f}%.",
                "formula": "[Logic: GSTR-1 / P&L Revenue > 1.15 = RED — industry threshold per CBIC]",
                "value": round(ratio, 3),
                "sources": ["GSTR-1", "Profit & Loss"],
            })

    # ─── 3. ITC Discrepancy: GSTR-2A vs GSTR-3B ──────────────────────────
    itc_available = financial_data.get("gstr2a_itc_available")
    itc_claimed = financial_data.get("gstr3b_tax_paid")

    if itc_available and itc_claimed:
        ratio = itc_claimed / itc_available if itc_available > 0 else 0
        if ratio <= 1.0:
            green.append({
                "variable": "itc_reconciliation",
                "summary": f"✓ ITC claimed in GSTR-3B ({_fmt(itc_claimed)}) is within GSTR-2A auto-drafted ({_fmt(itc_available)}). Compliant with Rule 36(4).",
                "formula": "[Logic: GSTR-3B ITC claimed / GSTR-2A ITC available ≤ 1.0]",
                "value": round(ratio, 3),
                "sources": ["GSTR-2A", "GSTR-3B"],
            })
        elif ratio <= 1.20:
            yellow.append({
                "variable": "itc_reconciliation",
                "summary": f"⚠ ITC claimed ({_fmt(itc_claimed)}) exceeds GSTR-2A ({_fmt(itc_available)}) by {(ratio-1)*100:.1f}%. Within tolerance but needs monitoring.",
                "formula": "[Logic: GSTR-3B ITC / GSTR-2A ITC between 1.0–1.2 = YELLOW]",
                "value": round(ratio, 3),
                "sources": ["GSTR-2A", "GSTR-3B"],
            })
        else:
            red.append({
                "variable": "itc_reconciliation",
                "summary": f"🚨 ITC Claim Discrepancy — Excess Over Auto-Drafted 2A: Claimed ({_fmt(itc_claimed)}) vs Available ({_fmt(itc_available)}). Ratio: {ratio:.2f}. Potential Rule 36(4) violation.",
                "formula": "[Logic: GSTR-3B ITC / GSTR-2A ITC > 1.2 = RED — violates CBIC Rule 36(4)]",
                "value": round(ratio, 3),
                "sources": ["GSTR-2A", "GSTR-3B"],
            })

    # ─── 4. ITR vs P&L Profit Match ───────────────────────────────────────
    net_profit = financial_data.get("net_profit")
    itr_profit = financial_data.get("itr_profit")

    if net_profit and itr_profit:
        diff_pct = abs(net_profit - itr_profit) / max(abs(net_profit), 1) * 100
        if diff_pct <= 5:
            green.append({
                "variable": "itr_pl_profit_match",
                "summary": f"✓ P&L Net Profit ({_fmt(net_profit)}) matches ITR declared profit ({_fmt(itr_profit)}). Variance: {diff_pct:.1f}%.",
                "formula": "[Logic: |P&L PAT - ITR Profit| / P&L PAT × 100]",
                "value": round(diff_pct, 2),
                "sources": ["Profit & Loss", "Income Tax Return"],
            })
        elif diff_pct <= 15:
            yellow.append({
                "variable": "itr_pl_profit_match",
                "summary": f"⚠ P&L Profit ({_fmt(net_profit)}) vs ITR ({_fmt(itr_profit)}) variance: {diff_pct:.1f}%. Investigate timing differences.",
                "formula": "[Logic: |P&L PAT - ITR Profit| / P&L PAT × 100]",
                "value": round(diff_pct, 2),
                "sources": ["Profit & Loss", "Income Tax Return"],
            })
        else:
            red.append({
                "variable": "itr_pl_profit_match",
                "summary": f"🚨 Significant profit mismatch: P&L ({_fmt(net_profit)}) vs ITR ({_fmt(itr_profit)}). Variance: {diff_pct:.1f}%. Potential tax evasion indicator.",
                "formula": "[Logic: |P&L PAT - ITR Profit| / P&L PAT × 100 > 15%]",
                "value": round(diff_pct, 2),
                "sources": ["Profit & Loss", "Income Tax Return"],
            })

    # ─── 5. Cash Flow vs Bank Transactions ────────────────────────────────
    ocf = financial_data.get("operating_cash_flow")
    bank_credits = financial_data.get("monthly_credits")

    if ocf and bank_credits:
        # bank_credits is monthly, annualize
        annual_credits = bank_credits * 12 if bank_credits < ocf else bank_credits
        ratio = ocf / annual_credits if annual_credits > 0 else 0
        if 0.7 <= ratio <= 1.3:
            green.append({
                "variable": "cashflow_vs_bank",
                "summary": f"✓ Operating Cash Flow ({_fmt(ocf)}) aligns with bank credit flows. Ratio: {ratio:.2f}.",
                "formula": "[Logic: Operating CF / Annualized Bank Credits]",
                "value": round(ratio, 3),
                "sources": ["Cash Flow Statement", "Bank Statement"],
            })
        else:
            yellow.append({
                "variable": "cashflow_vs_bank",
                "summary": f"⚠ Operating Cash Flow ({_fmt(ocf)}) vs bank credits divergence. Ratio: {ratio:.2f}. Investigate off-book transactions.",
                "formula": "[Logic: Operating CF / Annualized Bank Credits outside 0.7-1.3]",
                "value": round(ratio, 3),
                "sources": ["Cash Flow Statement", "Bank Statement"],
            })

    # ─── 6. Debt-Equity Ratio Check (RBI Norms) ──────────────────────────
    equity = financial_data.get("equity")
    debt = financial_data.get("debt")

    if equity and debt and equity > 0:
        de_ratio = debt / equity
        if de_ratio <= 2.0:
            green.append({
                "variable": "debt_equity_ratio",
                "summary": f"✓ Debt-to-Equity: {de_ratio:.2f}. Within RBI comfort zone (≤ 2.0).",
                "formula": "[Logic: Total Debt / Shareholders' Equity]",
                "value": round(de_ratio, 3),
                "sources": ["Balance Sheet"],
            })
        elif de_ratio <= 4.0:
            yellow.append({
                "variable": "debt_equity_ratio",
                "summary": f"⚠ Debt-to-Equity: {de_ratio:.2f}. Elevated but within sectoral tolerance.",
                "formula": "[Logic: Total Debt / Shareholders' Equity]",
                "value": round(de_ratio, 3),
                "sources": ["Balance Sheet"],
            })
        else:
            red.append({
                "variable": "debt_equity_ratio",
                "summary": f"🚨 Debt-to-Equity: {de_ratio:.2f}. Exceeds prudential norms. High leverage risk.",
                "formula": "[Logic: Total Debt / Shareholders' Equity > 4.0 = RED]",
                "value": round(de_ratio, 3),
                "sources": ["Balance Sheet"],
            })

    # ─── 7. DSCR Check ───────────────────────────────────────────────────
    dscr = financial_data.get("dscr")
    if dscr is not None:
        if dscr >= 1.5:
            green.append({
                "variable": "dscr",
                "summary": f"✓ DSCR: {dscr:.2f}. Strong debt servicing capacity.",
                "formula": "[Logic: (Net Profit + Depreciation + Interest) / (Principal + Interest)]",
                "value": round(dscr, 3),
                "sources": ["Calculations"],
            })
        elif dscr >= 1.0:
            yellow.append({
                "variable": "dscr",
                "summary": f"⚠ DSCR: {dscr:.2f}. Marginal debt servicing capacity.",
                "formula": "[Logic: DSCR between 1.0-1.5 = YELLOW]",
                "value": round(dscr, 3),
                "sources": ["Calculations"],
            })
        else:
            red.append({
                "variable": "dscr",
                "summary": f"🚨 DSCR: {dscr:.2f}. Unable to service debt from cash flows. Default risk elevated.",
                "formula": "[Logic: DSCR < 1.0 = RED]",
                "value": round(dscr, 3),
                "sources": ["Calculations"],
            })

    # ─── 8. CIN Validation ────────────────────────────────────────────────
    cin = financial_data.get("cin", "")
    if cin:
        cin_pattern = r"^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$"
        if re.match(cin_pattern, cin):
            green.append({
                "variable": "cin_validation",
                "summary": f"✓ CIN format valid: {cin}",
                "formula": "[Logic: CIN = U/L + 5-digit NIC + 2-letter state + year + PTC + 6-digit serial]",
                "value": cin,
                "sources": ["Certificate of Incorporation"],
            })
        else:
            red.append({
                "variable": "cin_validation",
                "summary": f"🚨 CIN format invalid: {cin}. Expected: U/L + 5-digits + 2-letters + 4-digits + 3-letters + 6-digits.",
                "formula": "[Logic: CIN regex validation]",
                "value": cin,
                "sources": ["Certificate of Incorporation"],
            })

    # ─── 9. GSTIN Validation ──────────────────────────────────────────────
    gstin = financial_data.get("gstin", "")
    if gstin:
        gstin_pattern = r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9][A-Z0-9]$"
        if re.match(gstin_pattern, gstin):
            green.append({
                "variable": "gstin_validation",
                "summary": f"✓ GSTIN format valid: {gstin}",
                "formula": "[Logic: GSTIN = 2-digit state + PAN (10 chars) + entity + check digit]",
                "value": gstin,
                "sources": ["GST Registration"],
            })
        else:
            red.append({
                "variable": "gstin_validation",
                "summary": f"🚨 GSTIN format invalid: {gstin}.",
                "formula": "[Logic: GSTIN regex validation]",
                "value": gstin,
                "sources": ["GST Registration"],
            })

    # ─── 10. Current Ratio ────────────────────────────────────────────────
    ca = financial_data.get("current_assets")
    cl = financial_data.get("current_liabilities")
    if ca and cl and cl > 0:
        cr = ca / cl
        if cr >= 1.5:
            green.append({
                "variable": "current_ratio",
                "summary": f"✓ Current Ratio: {cr:.2f}. Adequate short-term liquidity.",
                "formula": "[Logic: Current Assets / Current Liabilities]",
                "value": round(cr, 3),
                "sources": ["Balance Sheet"],
            })
        elif cr >= 1.0:
            yellow.append({
                "variable": "current_ratio",
                "summary": f"⚠ Current Ratio: {cr:.2f}. Tight liquidity position.",
                "formula": "[Logic: Current Assets / Current Liabilities]",
                "value": round(cr, 3),
                "sources": ["Balance Sheet"],
            })
        else:
            red.append({
                "variable": "current_ratio",
                "summary": f"🚨 Current Ratio: {cr:.2f}. Below 1.0 — negative working capital. Liquidity crisis risk.",
                "formula": "[Logic: Current Assets / Current Liabilities < 1.0 = RED]",
                "value": round(cr, 3),
                "sources": ["Balance Sheet"],
            })

    return {"green": green, "yellow": yellow, "red": red}


def _fmt(value: float) -> str:
    """Format number as Indian currency string (₹ Lakhs/Crores)."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:
        return f"₹{value / 1_00_000:.2f} L"
    else:
        return f"₹{value:,.0f}"
