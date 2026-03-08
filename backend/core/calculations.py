"""
Financial Calculations Engine — Indian Credit Ratios with RBI Norms.
Every formula includes [Logic: ...] citation for explainability.
"""

from typing import Any


def run_intermediate_calculations(financial_data: dict) -> dict:
    """
    Compute credit-relevant financial ratios from extracted data.
    All results include formula citations.
    """
    results = {}

    revenue = financial_data.get("revenue", 0)
    net_profit = financial_data.get("net_profit", 0)
    ebitda = financial_data.get("ebitda", 0)
    interest = financial_data.get("interest_expense", 0)
    depreciation = financial_data.get("depreciation", 0)
    debt = financial_data.get("debt", 0)
    equity = financial_data.get("equity", 0)
    total_assets = financial_data.get("total_assets", 0)
    current_assets = financial_data.get("current_assets", 0)
    current_liabilities = financial_data.get("current_liabilities", 0)
    operating_cf = financial_data.get("operating_cash_flow", 0)
    loan_amount = financial_data.get("loan_amount", 0)

    # ─── DSCR ─────────────────────────────────────────────────────────────
    numerator = net_profit + depreciation + interest
    # Assume annual debt service = interest + principal repayment
    annual_principal = debt * 0.1 if debt else loan_amount * 0.1 if loan_amount else 0
    denominator = interest + annual_principal
    if denominator > 0:
        dscr = numerator / denominator
        results["dscr"] = {
            "value": round(dscr, 2),
            "formula": "[Logic: DSCR = (Net Profit + Depreciation + Interest) / (Interest + Annual Principal Repayment)]",
            "status": "GREEN" if dscr >= 1.5 else ("YELLOW" if dscr >= 1.0 else "RED"),
            "benchmark": "RBI: DSCR ≥ 1.25 (minimum), ≥ 1.5 (comfortable)",
        }

    # ─── Interest Coverage Ratio ──────────────────────────────────────────
    if interest > 0:
        icr = ebitda / interest if ebitda else (net_profit + interest + depreciation) / interest
        results["interest_coverage_ratio"] = {
            "value": round(icr, 2),
            "formula": "[Logic: ICR = EBITDA / Interest Expense]",
            "status": "GREEN" if icr >= 3.0 else ("YELLOW" if icr >= 1.5 else "RED"),
            "benchmark": "RBI: ICR ≥ 2.0 (minimum)",
        }

    # ─── Current Ratio ────────────────────────────────────────────────────
    if current_liabilities > 0:
        cr = current_assets / current_liabilities
        results["current_ratio"] = {
            "value": round(cr, 2),
            "formula": "[Logic: Current Ratio = Current Assets / Current Liabilities]",
            "status": "GREEN" if cr >= 1.5 else ("YELLOW" if cr >= 1.0 else "RED"),
            "benchmark": "RBI: CR ≥ 1.33 (for working capital facilities)",
        }

    # ─── Debt-to-Equity Ratio ────────────────────────────────────────────
    if equity > 0:
        de = debt / equity
        results["debt_equity_ratio"] = {
            "value": round(de, 2),
            "formula": "[Logic: D/E = Total Debt / Shareholders' Equity]",
            "status": "GREEN" if de <= 2.0 else ("YELLOW" if de <= 4.0 else "RED"),
            "benchmark": "RBI: D/E ≤ 2.0 (comfortable), sectoral variations apply",
        }

    # ─── Net Profit Margin ───────────────────────────────────────────────
    if revenue > 0:
        npm = (net_profit / revenue) * 100
        results["net_profit_margin"] = {
            "value": round(npm, 2),
            "formula": "[Logic: NPM = (Net Profit / Revenue) × 100]",
            "status": "GREEN" if npm >= 10 else ("YELLOW" if npm >= 5 else "RED"),
            "unit": "%",
        }

    # ─── Return on Assets ────────────────────────────────────────────────
    if total_assets > 0:
        roa = (net_profit / total_assets) * 100
        results["return_on_assets"] = {
            "value": round(roa, 2),
            "formula": "[Logic: ROA = (Net Profit / Total Assets) × 100]",
            "status": "GREEN" if roa >= 5 else ("YELLOW" if roa >= 2 else "RED"),
            "unit": "%",
        }

    # ─── Return on Equity ────────────────────────────────────────────────
    if equity > 0:
        roe = (net_profit / equity) * 100
        results["return_on_equity"] = {
            "value": round(roe, 2),
            "formula": "[Logic: ROE = (Net Profit / Equity) × 100]",
            "status": "GREEN" if roe >= 15 else ("YELLOW" if roe >= 8 else "RED"),
            "unit": "%",
        }

    # ─── Working Capital ─────────────────────────────────────────────────
    wc = current_assets - current_liabilities
    results["working_capital"] = {
        "value": round(wc, 0),
        "formula": "[Logic: WC = Current Assets - Current Liabilities]",
        "status": "GREEN" if wc > 0 else "RED",
    }

    # ─── Promoter Contribution Check ─────────────────────────────────────
    promoter_pct = financial_data.get("promoter_holding_pct")
    if promoter_pct is not None:
        results["promoter_contribution"] = {
            "value": round(promoter_pct, 2),
            "formula": "[Logic: Promoter Shareholding % from Shareholding Pattern]",
            "status": "GREEN" if promoter_pct >= 26 else ("YELLOW" if promoter_pct >= 15 else "RED"),
            "benchmark": "RBI: Minimum promoter contribution varies by scheme",
            "unit": "%",
        }

    # ─── GST Compliance Score ────────────────────────────────────────────
    gstr1 = financial_data.get("gstr1_sales", 0)
    gstr3b = financial_data.get("gstr3b_sales", 0)
    if gstr1 > 0 and gstr3b > 0:
        gst_match = min(gstr1, gstr3b) / max(gstr1, gstr3b) * 100
        results["gst_compliance_score"] = {
            "value": round(gst_match, 1),
            "formula": "[Logic: GST Score = min(GSTR-1, GSTR-3B) / max(GSTR-1, GSTR-3B) × 100]",
            "status": "GREEN" if gst_match >= 95 else ("YELLOW" if gst_match >= 85 else "RED"),
            "unit": "%",
        }

    return results


def compute_risk_score(
    calculations: dict,
    evidence: dict,
    fraud_score: float = 0.0,
) -> float:
    """
    Compute overall risk score (0 = safest, 1 = highest risk).
    Weighted combination of financial ratios, evidence flags, and fraud signals.
    """
    score = 0.0
    total_weight = 0.0

    # Weight map for ratio signals
    ratio_weights = {
        "dscr": 20,
        "interest_coverage_ratio": 15,
        "current_ratio": 10,
        "debt_equity_ratio": 15,
        "net_profit_margin": 10,
    }

    for key, weight in ratio_weights.items():
        calc = calculations.get(key, {})
        status = calc.get("status", "YELLOW")
        if status == "GREEN":
            score += 0
        elif status == "YELLOW":
            score += weight * 0.5
        else:  # RED
            score += weight * 1.0
        total_weight += weight

    # Evidence flags weight
    evidence_weight = 20
    red_count = len(evidence.get("red", []))
    yellow_count = len(evidence.get("yellow", []))
    evidence_score = min(1.0, (red_count * 0.3 + yellow_count * 0.1))
    score += evidence_weight * evidence_score
    total_weight += evidence_weight

    # Fraud adjustment
    fraud_weight = 10
    score += fraud_weight * min(fraud_score, 1.0)
    total_weight += fraud_weight

    return round(score / total_weight, 2) if total_weight > 0 else 0.5
