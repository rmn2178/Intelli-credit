"""
Forensic Credit Audit Engine — 30-Checkpoint Validation Framework
Intelli-Credit v2.0

Deterministic, explainable audit engine with hard veto fraud detection,
missing-data awareness, and aggregate risk scoring (0-300 scale).
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any

logger = logging.getLogger("forensic_engine")

# ─── Scoring Weights ─────────────────────────────────────────────────────────

SCORING_WEIGHTS = {"Score_3": 10, "Score_2": 5, "Score_1": 0}

# ─── Hard Veto Checkpoint IDs ────────────────────────────────────────────────
# If any of these produce Score_1, immediate loan rejection.
HARD_VETO_IDS = {2, 5, 14}

# ─── Required Fields Per Category ────────────────────────────────────────────
REQUIRED_FIELDS = {
    "GST": [
        "actual_filing_date", "statutory_due_date", "gstr1_sales",
        "gstr3b_sales", "top_client_sales", "total_annual_sales",
        "gstr3b_itc", "gstr2a_itc", "gst_reg_date",
    ],
    "ITR_Financials": [
        "itr_turnover", "net_profit", "ebitda", "depreciation",
        "interest_expense", "total_liabilities", "cibil_outstanding",
        "principal_repayment", "income_26as",
    ],
    "Banking": [
        "monthly_average_balance", "monthly_credits", "monthly_debits",
        "inward_bounce_count_12mo", "director_transfers",
        "cash_withdrawals", "expected_emi",
    ],
    "Management_Legal": [
        "auditor_opinion", "contingent_liabilities", "rpt_value",
        "last_kmp_change_date", "pledged_shares", "total_promoter_shares",
        "active_litigation_count", "mca_charged_assets",
    ],
}

# ─── 30 Checkpoint Definitions ───────────────────────────────────────────────

CHECKPOINTS = [
    {"id": 1,  "cat": "GST",   "name": "Filing Discipline",       "formula": "Actual_Date - Due_Date"},
    {"id": 2,  "cat": "GST",   "name": "Sales Integrity",         "formula": "abs((GSTR1_Sales / GSTR3B_Sales) - 1) * 100"},
    {"id": 3,  "cat": "GST",   "name": "Turnover Trend",          "formula": "((Curr_Sales - Prev_Sales) / Prev_Sales) * 100"},
    {"id": 4,  "cat": "GST",   "name": "Customer Concentration",  "formula": "(Top_Client_Sales / Total_Sales) * 100"},
    {"id": 5,  "cat": "GST",   "name": "ITC Authenticity",        "formula": "(GSTR3B_ITC / GSTR2A_ITC) * 100"},
    {"id": 6,  "cat": "GST",   "name": "Business Age",            "formula": "Current_Date - GST_Reg_Date"},
    {"id": 7,  "cat": "ITR",   "name": "Revenue Integrity",       "formula": "abs((ITR_Turnover / Sum_12mo_GST) - 1) * 100"},
    {"id": 8,  "cat": "ITR",   "name": "Debt Disclosure",         "formula": "Total_ITR_Liabilities - CIBIL_Outstanding"},
    {"id": 9,  "cat": "ITR",   "name": "Repayment Power (DSCR)",  "formula": "(NP + Depr + Int) / (Int + Principal)"},
    {"id": 10, "cat": "ITR",   "name": "Tax Compliance Rate",     "formula": "(Tax_Paid / Turnover) * 100"},
    {"id": 11, "cat": "ITR",   "name": "26AS Verification",       "formula": "(Income_26AS / ITR_Income) * 100"},
    {"id": 12, "cat": "ITR",   "name": "Depreciation Logic",      "formula": "(Depr / Fixed_Assets) * 100"},
    {"id": 13, "cat": "Bank",  "name": "Liquidity Buffer",        "formula": "(MAB / Monthly_Credits) * 100"},
    {"id": 14, "cat": "Bank",  "name": "Conduct Score",           "formula": "Count(Inward_Bounces_12mo)"},
    {"id": 15, "cat": "Bank",  "name": "Fund Diversion",          "formula": "(Dir_Transfers / Total_Debits) * 100"},
    {"id": 16, "cat": "Bank",  "name": "Credit Velocity",         "formula": "Single_Max_Credit / Day_Opening_Bal"},
    {"id": 17, "cat": "Bank",  "name": "EMI Traceability",        "formula": "Sum(Expected_EMI) - Sum(Bank_EMI_Debits)"},
    {"id": 18, "cat": "Bank",  "name": "Cash Intensity",          "formula": "(Cash_WD / Total_Debits) * 100"},
    {"id": 19, "cat": "Audit", "name": "Opinion Sentiment",       "formula": "NLP_Classifier(Audit_Remarks)"},
    {"id": 20, "cat": "Audit", "name": "Contingent Burden",       "formula": "(Contingent_Liab / Net_Worth) * 100"},
    {"id": 21, "cat": "Audit", "name": "Conflict Check (RPT)",    "formula": "(RPT_Value / Revenue) * 100"},
    {"id": 22, "cat": "Mgmt",  "name": "KMP Stability",           "formula": "Days_Since_Last_KMP_Change"},
    {"id": 23, "cat": "Mgmt",  "name": "Share Pledge",            "formula": "(Pledged / Total_Promoter) * 100"},
    {"id": 24, "cat": "Mgmt",  "name": "Intent Alignment",        "formula": "Cosine_Similarity(Plan, Minutes)"},
    {"id": 25, "cat": "Legal", "name": "Litigation Impact",       "formula": "Count(Active_Cases)"},
    {"id": 26, "cat": "Legal", "name": "Rating Momentum",         "formula": "Current_Rating - Prev_Rating"},
    {"id": 27, "cat": "Site",  "name": "Operational Health",      "formula": "(Actual_Output / Max_Capacity) * 100"},
    {"id": 28, "cat": "Site",  "name": "News Sentiment",          "formula": "NLP_Sentiment(News_Feed)"},
    {"id": 29, "cat": "MCA",   "name": "Lien Check",              "formula": "Count(Assets_Charged_Elsewhere)"},
    {"id": 30, "cat": "Stock", "name": "Inventory Velocity",      "formula": "(Avg_Inv / COGS) * 365"},
]


# ─── Data Extraction ─────────────────────────────────────────────────────────

# Sentinel for "field was not found in any source"
_MISSING = object()


def _try_extract_from_documents(documents: dict | None, key: str) -> Any:
    """
    Attempt to find a value by scanning uploaded document text.
    This is a fallback when financial_data doesn't contain the field.
    Returns _MISSING if not found.
    """
    if not documents:
        return _MISSING
    # Simple keyword scan across all document texts
    for doc_type, doc_info in documents.items():
        text = ""
        if isinstance(doc_info, dict):
            text = doc_info.get("text", "")
        elif isinstance(doc_info, str):
            text = doc_info
        if not text:
            continue
        # Look for patterns like "key: value" or "key = value"
        import re
        patterns = [
            rf'(?i){re.escape(key)}\s*[:=]\s*([\d,]+\.?\d*)',
            rf'(?i){key.replace("_", " ")}\s*[:=]\s*([\d,]+\.?\d*)',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                try:
                    return float(m.group(1).replace(",", ""))
                except (ValueError, TypeError):
                    pass
    return _MISSING


def extract_forensic_data(
    financial_data: dict,
    documents: dict | None = None,
) -> dict:
    """
    Map session financial_data + document text into the forensic extraction schema.
    Tracks which fields are present vs missing for data quality reporting.
    """
    fd = financial_data or {}
    missing_fields: list[str] = []
    present_fields: list[str] = []

    def sf(key: str, *alt_keys: str, default: float | None = None) -> float | None:
        """Safe float — try key, then alt_keys, then documents, then default."""
        for k in (key, *alt_keys):
            v = fd.get(k)
            if v is not None:
                try:
                    val = float(v)
                    present_fields.append(key)
                    return val
                except (TypeError, ValueError):
                    pass
        # Try document extraction
        doc_val = _try_extract_from_documents(documents, key)
        if doc_val is not _MISSING:
            present_fields.append(key)
            try:
                return float(doc_val)
            except (TypeError, ValueError):
                pass
        # Not found anywhere
        if default is not None:
            missing_fields.append(key)
            return default
        missing_fields.append(key)
        return None

    def si(key: str, *alt_keys: str, default: int | None = None) -> int | None:
        """Safe int — try key, then alt_keys, then documents, then default."""
        for k in (key, *alt_keys):
            v = fd.get(k)
            if v is not None:
                try:
                    val = int(v)
                    present_fields.append(key)
                    return val
                except (TypeError, ValueError):
                    pass
        doc_val = _try_extract_from_documents(documents, key)
        if doc_val is not _MISSING:
            present_fields.append(key)
            try:
                return int(doc_val)
            except (TypeError, ValueError):
                pass
        if default is not None:
            missing_fields.append(key)
            return default
        missing_fields.append(key)
        return None

    def ss(key: str, *alt_keys: str, default: str = "") -> str:
        """Safe string — try key, then alt_keys, then default."""
        for k in (key, *alt_keys):
            v = fd.get(k)
            if v is not None and str(v).strip():
                present_fields.append(key)
                return str(v).strip()
        if default:
            missing_fields.append(key)
        else:
            missing_fields.append(key)
        return default

    gst = {
        "actual_filing_date": ss("gst_actual_filing_date", "actual_filing_date"),
        "statutory_due_date": ss("gst_statutory_due_date", "statutory_due_date"),
        "gstr1_sales": sf("gstr1_sales"),
        "gstr3b_sales": sf("gstr3b_sales"),
        "top_client_sales": sf("top_client_sales"),
        "total_annual_sales": sf("total_annual_sales", "revenue"),
        "gstr3b_itc": sf("gstr3b_itc"),
        "gstr2a_itc": sf("gstr2a_itc"),
        "gst_reg_date": ss("gst_reg_date", "gst_registration_date"),
        "prev_year_sales": sf("prev_year_sales"),
        "curr_year_sales": sf("curr_year_sales", "revenue"),
    }

    itr = {
        "itr_turnover": sf("itr_turnover", "revenue"),
        "net_profit": sf("net_profit"),
        "ebitda": sf("ebitda"),
        "depreciation": sf("depreciation"),
        "interest_expense": sf("interest_expense"),
        "total_liabilities": sf("total_liabilities", "debt"),
        "cibil_outstanding": sf("cibil_outstanding"),
        "principal_repayment": sf("principal_repayment"),
        "income_26as": sf("income_26as"),
        "itr_income": sf("itr_income", "revenue"),
        "tax_paid": sf("tax_paid"),
        "fixed_assets": sf("fixed_assets"),
        "net_worth": sf("net_worth", "equity"),
    }

    banking = {
        "monthly_average_balance": sf("monthly_average_balance", "mab"),
        "monthly_credits": sf("monthly_credits"),
        "monthly_debits": sf("monthly_debits"),
        "total_debits": sf("total_debits"),
        "inward_bounce_count_12mo": si("inward_bounce_count_12mo", "inward_bounces"),
        "director_transfers": sf("director_transfers"),
        "cash_withdrawals": sf("cash_withdrawals"),
        "expected_emi": sf("expected_emi"),
        "bank_emi_debits": sf("bank_emi_debits"),
        "single_max_credit": sf("single_max_credit"),
        "day_opening_balance": sf("day_opening_balance"),
    }

    # Derive total_debits from monthly if missing
    if banking["total_debits"] is None and banking["monthly_debits"] is not None:
        banking["total_debits"] = banking["monthly_debits"] * 12

    mgmt_legal = {
        "auditor_opinion": ss("auditor_opinion", default=""),
        "contingent_liabilities": sf("contingent_liabilities"),
        "rpt_value": sf("rpt_value"),
        "last_kmp_change_date": ss("last_kmp_change_date"),
        "pledged_shares": sf("pledged_shares"),
        "total_promoter_shares": sf("total_promoter_shares"),
        "active_litigation_count": si("active_litigation_count"),
        "mca_charged_assets": si("mca_charged_assets"),
        "actual_output": sf("actual_output"),
        "max_capacity": sf("max_capacity"),
        "current_rating": ss("current_rating"),
        "prev_rating": ss("prev_rating"),
        "avg_inventory": sf("avg_inventory"),
        "cogs": sf("cogs"),
        "news_sentiment": ss("news_sentiment"),
        "intent_alignment": ss("intent_alignment"),
    }

    # Compute data completeness
    total_required = sum(len(v) for v in REQUIRED_FIELDS.values())
    # De-duplicate present_fields
    unique_present = set(present_fields)
    unique_missing = set(missing_fields) - unique_present
    completeness_pct = min(round(len(unique_present) / total_required * 100, 1), 100.0) if total_required > 0 else 0

    for mf in unique_missing:
        logger.warning(f"Missing variable: {mf}")

    return {
        "GST": gst,
        "ITR_Financials": itr,
        "Banking": banking,
        "Management_Legal": mgmt_legal,
        "_meta": {
            "present_fields": sorted(unique_present),
            "missing_fields": sorted(unique_missing),
            "present_count": len(unique_present),
            "missing_count": len(unique_missing),
            "total_required": total_required,
            "data_completeness_pct": completeness_pct,
        },
    }


# ─── Checkpoint Evaluator ───────────────────────────────────────────────────


def _safe_div(a: float, b: float) -> float:
    """Safe division, returns 0 if divisor is 0."""
    return a / b if b != 0 else 0.0


def _parse_date(s: str) -> date | None:
    """Try to parse a date string in common formats."""
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _days_between(d1_str: str, d2_str: str) -> int | None:
    """Return days between two date strings (d1 - d2)."""
    d1 = _parse_date(d1_str)
    d2 = _parse_date(d2_str)
    if d1 and d2:
        return (d1 - d2).days
    return None


def _days_since(date_str: str) -> int | None:
    """Return days from a date to today."""
    d = _parse_date(date_str)
    if d:
        return (date.today() - d).days
    return None


def _rating_delta(current: str, prev: str) -> str:
    """Compare credit ratings.  Simple heuristic based on common scales."""
    rating_order = ["D", "C", "CC", "CCC", "B-", "B", "B+", "BB-", "BB", "BB+",
                    "BBB-", "BBB", "BBB+", "A-", "A", "A+", "AA-", "AA", "AA+", "AAA"]
    mapping = {r.upper(): i for i, r in enumerate(rating_order)}
    ci = mapping.get(current.strip().upper(), -1)
    pi = mapping.get(prev.strip().upper(), -1)
    if ci < 0 or pi < 0:
        return "Stable"
    if ci > pi:
        return "Upgrade"
    elif ci == pi:
        return "Stable"
    else:
        return "Downgrade"


def _is_present(val: Any) -> bool:
    """Check if a value is actually present (not None, not empty string, not 0 for numerics that matter)."""
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def _missing_result(cp: dict, field_names: list[str]) -> dict:
    """Return a standard 'Data Missing' result for a checkpoint."""
    logger.warning(f"Missing variable(s) for checkpoint {cp['id']} ({cp['name']}): {', '.join(field_names)}")
    return {
        "id": cp["id"],
        "name": cp["name"],
        "cat": cp["cat"],
        "formula": cp["formula"],
        "result_value": "Data Missing",
        "result_label": f"Data not available ({', '.join(field_names)})",
        "score_tier": "Score_1",
        "score_points": 0,
        "is_veto": cp["id"] in HARD_VETO_IDS,
        "data_missing": True,
    }


def evaluate_checkpoint(cp: dict, extracted: dict) -> dict:
    """
    Evaluate a single checkpoint against extracted data.
    Returns a result dict.  Missing data → Score_1 + 'Data Missing', never crashes.
    """
    cp_id = cp["id"]
    gst = extracted.get("GST", {})
    itr = extracted.get("ITR_Financials", {})
    bank = extracted.get("Banking", {})
    ml = extracted.get("Management_Legal", {})

    result_value = None
    result_label = ""
    score_tier = "Score_1"

    try:
        if cp_id == 1:  # Filing Discipline
            a = gst.get("actual_filing_date")
            d = gst.get("statutory_due_date")
            if not _is_present(a) or not _is_present(d):
                return _missing_result(cp, ["actual_filing_date", "statutory_due_date"])
            days = _days_between(a, d)
            if days is not None:
                result_value = days
                if days <= 0:
                    score_tier, result_label = "Score_3", f"{abs(days)} days early/on-time"
                elif days <= 5:
                    score_tier, result_label = "Score_2", f"{days} days delay"
                else:
                    score_tier, result_label = "Score_1", f"{days} days delay"
            else:
                return _missing_result(cp, ["actual_filing_date (unparseable)"])

        elif cp_id == 2:  # Sales Integrity
            g1 = gst.get("gstr1_sales")
            g3 = gst.get("gstr3b_sales")
            if g1 is None or g3 is None:
                return _missing_result(cp, ["gstr1_sales", "gstr3b_sales"])
            if g3 > 0 and g1 > 0:
                variance = abs((g1 / g3) - 1) * 100
                result_value = round(variance, 2)
                if variance < 1:
                    score_tier, result_label = "Score_3", f"{result_value}% variance"
                elif variance <= 3:
                    score_tier, result_label = "Score_2", f"{result_value}% variance"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% variance"
            else:
                return _missing_result(cp, ["gstr1_sales (zero)", "gstr3b_sales (zero)"])

        elif cp_id == 3:  # Turnover Trend
            curr = gst.get("curr_year_sales")
            prev = gst.get("prev_year_sales")
            if curr is None or prev is None:
                return _missing_result(cp, ["curr_year_sales", "prev_year_sales"])
            if prev > 0:
                trend = ((curr - prev) / prev) * 100
                result_value = round(trend, 1)
                abs_trend = abs(trend)
                if abs_trend <= 30:
                    score_tier, result_label = "Score_3", f"{result_value:+.1f}% growth"
                elif abs_trend <= 50:
                    score_tier, result_label = "Score_2", f"{result_value:+.1f}% spike"
                else:
                    score_tier, result_label = "Score_1", f"{result_value:+.1f}% spike"
            else:
                result_value = 0
                score_tier, result_label = "Score_3", "Stable (no prior year data)"

        elif cp_id == 4:  # Customer Concentration
            top = gst.get("top_client_sales")
            total = gst.get("total_annual_sales")
            if top is None or total is None:
                return _missing_result(cp, ["top_client_sales", "total_annual_sales"])
            if total > 0:
                conc = (top / total) * 100
                result_value = round(conc, 1)
                if conc < 25:
                    score_tier, result_label = "Score_3", f"{result_value}% concentration"
                elif conc <= 40:
                    score_tier, result_label = "Score_2", f"{result_value}% concentration"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% concentration"
            else:
                return _missing_result(cp, ["total_annual_sales (zero)"])

        elif cp_id == 5:  # ITC Authenticity
            itc3b = gst.get("gstr3b_itc")
            itc2a = gst.get("gstr2a_itc")
            if itc3b is None or itc2a is None:
                return _missing_result(cp, ["gstr3b_itc", "gstr2a_itc"])
            if itc2a > 0 and itc3b > 0:
                match = (itc3b / itc2a) * 100
                result_value = round(match, 1)
                if match >= 95:
                    score_tier, result_label = "Score_3", f"{result_value}% match"
                elif match >= 85:
                    score_tier, result_label = "Score_2", f"{result_value}% match"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% match"
            else:
                return _missing_result(cp, ["gstr3b_itc (zero)", "gstr2a_itc (zero)"])

        elif cp_id == 6:  # Business Age
            reg = gst.get("gst_reg_date")
            if not _is_present(reg):
                return _missing_result(cp, ["gst_reg_date"])
            days = _days_since(reg)
            if days is not None:
                years = days / 365.25
                result_value = round(years, 1)
                if years > 3:
                    score_tier, result_label = "Score_3", f"{result_value} years"
                elif years >= 1:
                    score_tier, result_label = "Score_2", f"{result_value} years"
                else:
                    score_tier, result_label = "Score_1", f"{result_value} years"
            else:
                return _missing_result(cp, ["gst_reg_date (unparseable)"])

        elif cp_id == 7:  # Revenue Integrity
            itr_t = itr.get("itr_turnover")
            gst_sum = gst.get("total_annual_sales")
            if itr_t is None or gst_sum is None:
                return _missing_result(cp, ["itr_turnover", "total_annual_sales"])
            if gst_sum > 0 and itr_t > 0:
                dev = abs((itr_t / gst_sum) - 1) * 100
                result_value = round(dev, 2)
                if dev < 5:
                    score_tier, result_label = "Score_3", f"{result_value}% deviation"
                elif dev <= 10:
                    score_tier, result_label = "Score_2", f"{result_value}% deviation"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% deviation"
            else:
                return _missing_result(cp, ["itr_turnover or total_annual_sales (zero)"])

        elif cp_id == 8:  # Debt Disclosure
            liab = itr.get("total_liabilities")
            cibil = itr.get("cibil_outstanding")
            if liab is None or cibil is None:
                return _missing_result(cp, ["total_liabilities", "cibil_outstanding"])
            diff = liab - cibil
            result_value = round(diff, 0)
            if abs(diff) < 100000:
                score_tier, result_label = "Score_3", "Match"
            elif abs(diff) < 500000:
                score_tier, result_label = "Score_2", "Minor Diff"
            else:
                score_tier, result_label = "Score_1", "Hidden Loans"

        elif cp_id == 9:  # Repayment Power (DSCR)
            np_ = itr.get("net_profit")
            dep = itr.get("depreciation")
            intr = itr.get("interest_expense")
            prin = itr.get("principal_repayment")
            missing = []
            if np_ is None: missing.append("net_profit")
            if dep is None: missing.append("depreciation")
            if intr is None: missing.append("interest_expense")
            if prin is None: missing.append("principal_repayment")
            if missing:
                return _missing_result(cp, missing)
            denom = intr + prin
            if denom <= 0:
                result_value = "Not Computable"
                score_tier = "Score_1"
                result_label = "DSCR not computable (zero debt service)"
            else:
                dscr = (np_ + dep + intr) / denom
                result_value = round(dscr, 2)
                if dscr >= 1.50:
                    score_tier, result_label = "Score_3", f"DSCR {result_value}"
                elif dscr >= 1.20:
                    score_tier, result_label = "Score_2", f"DSCR {result_value}"
                else:
                    score_tier, result_label = "Score_1", f"DSCR {result_value}"

        elif cp_id == 10:  # Tax Compliance Rate
            tax = itr.get("tax_paid")
            turnover = itr.get("itr_turnover")
            if tax is None or turnover is None:
                return _missing_result(cp, ["tax_paid", "itr_turnover"])
            if turnover > 0:
                rate = (tax / turnover) * 100
                result_value = round(rate, 2)
                if rate >= 1.5:
                    score_tier, result_label = "Score_3", f"{result_value}% tax rate"
                elif rate >= 0.5:
                    score_tier, result_label = "Score_2", f"{result_value}% slight deviation"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% near-zero tax"
            else:
                return _missing_result(cp, ["itr_turnover (zero)"])

        elif cp_id == 11:  # 26AS Verification
            as26 = itr.get("income_26as")
            itr_inc = itr.get("itr_income")
            if as26 is None or itr_inc is None:
                return _missing_result(cp, ["income_26as", "itr_income"])
            if itr_inc > 0 and as26 > 0:
                pct = (as26 / itr_inc) * 100
                result_value = round(pct, 1)
                if pct >= 100:
                    score_tier, result_label = "Score_3", f"{result_value}% verified"
                elif pct >= 90:
                    score_tier, result_label = "Score_2", f"{result_value}% verified"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% verified"
            else:
                return _missing_result(cp, ["income_26as or itr_income (zero)"])

        elif cp_id == 12:  # Depreciation Logic
            dep = itr.get("depreciation")
            fa = itr.get("fixed_assets")
            if dep is None or fa is None:
                return _missing_result(cp, ["depreciation", "fixed_assets"])
            if fa > 0:
                rate = (dep / fa) * 100
                result_value = round(rate, 1)
                if rate <= 15:
                    score_tier, result_label = "Score_3", f"{result_value}% consistent"
                elif rate <= 25:
                    score_tier, result_label = "Score_2", f"{result_value}% minor variance"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% aggressive"
            else:
                return _missing_result(cp, ["fixed_assets (zero)"])

        elif cp_id == 13:  # Liquidity Buffer
            mab = bank.get("monthly_average_balance")
            credits = bank.get("monthly_credits")
            if mab is None or credits is None:
                return _missing_result(cp, ["monthly_average_balance", "monthly_credits"])
            if credits > 0:
                buf = (mab / credits) * 100
                result_value = round(buf, 1)
                if buf > 10:
                    score_tier, result_label = "Score_3", f"{result_value}% buffer"
                elif buf >= 5:
                    score_tier, result_label = "Score_2", f"{result_value}% buffer"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% buffer"
            else:
                return _missing_result(cp, ["monthly_credits (zero)"])

        elif cp_id == 14:  # Conduct Score
            bounces = bank.get("inward_bounce_count_12mo")
            if bounces is None:
                return _missing_result(cp, ["inward_bounce_count_12mo"])
            result_value = bounces
            if bounces == 0:
                score_tier, result_label = "Score_3", "0 bounces"
            elif bounces <= 2:
                score_tier, result_label = "Score_2", f"{bounces} technical bounce(s)"
            else:
                score_tier, result_label = "Score_1", f"{bounces} bounces incl. EMI"

        elif cp_id == 15:  # Fund Diversion
            dt = bank.get("director_transfers")
            td = bank.get("total_debits")
            if dt is None or td is None:
                return _missing_result(cp, ["director_transfers", "total_debits"])
            if td > 0:
                pct = (dt / td) * 100
                result_value = round(pct, 2)
                if pct == 0:
                    score_tier, result_label = "Score_3", "0% diversion"
                elif pct < 5:
                    score_tier, result_label = "Score_2", f"{result_value}% occasional"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% frequent"
            else:
                return _missing_result(cp, ["total_debits (zero)"])

        elif cp_id == 16:  # Credit Velocity
            smc = bank.get("single_max_credit")
            dob = bank.get("day_opening_balance")
            if smc is None or dob is None:
                return _missing_result(cp, ["single_max_credit", "day_opening_balance"])
            if dob > 0 and smc > 0:
                ratio = smc / dob
                result_value = round(ratio, 2)
                if ratio <= 2:
                    score_tier, result_label = "Score_3", f"{result_value}x normal"
                elif ratio <= 5:
                    score_tier, result_label = "Score_2", f"{result_value}x spikes"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}x wash trade risk"
            else:
                return _missing_result(cp, ["single_max_credit or day_opening_balance (zero)"])

        elif cp_id == 17:  # EMI Traceability
            expected = bank.get("expected_emi")
            actual = bank.get("bank_emi_debits")
            if expected is None:
                return _missing_result(cp, ["expected_emi"])
            if expected > 0:
                actual = actual or 0
                diff = expected - actual
                result_value = round(diff, 0)
                if abs(diff) < expected * 0.05:
                    score_tier, result_label = "Score_3", "Matched"
                elif abs(diff) < expected * 0.2:
                    score_tier, result_label = "Score_2", "1-2 missing"
                else:
                    score_tier, result_label = "Score_1", "Paid outside"
            else:
                result_value = 0
                score_tier, result_label = "Score_3", "No EMI obligations"

        elif cp_id == 18:  # Cash Intensity
            cw = bank.get("cash_withdrawals")
            td = bank.get("total_debits")
            if cw is None or td is None:
                return _missing_result(cp, ["cash_withdrawals", "total_debits"])
            if td > 0:
                pct = (cw / td) * 100
                result_value = round(pct, 1)
                if pct < 5:
                    score_tier, result_label = "Score_3", f"{result_value}% cash"
                elif pct <= 15:
                    score_tier, result_label = "Score_2", f"{result_value}% cash"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% cash"
            else:
                return _missing_result(cp, ["total_debits (zero)"])

        elif cp_id == 19:  # Opinion Sentiment
            opinion = ml.get("auditor_opinion", "")
            if not _is_present(opinion):
                return _missing_result(cp, ["auditor_opinion"])
            opinion = opinion.lower().strip()
            if opinion in ("clean", "unqualified", "unmodified"):
                result_value = "Clean"
                score_tier, result_label = "Score_3", "Clean audit report"
            elif opinion in ("emphasis", "qualified", "emphasis of matter"):
                result_value = "Emphasis"
                score_tier, result_label = "Score_2", "Emphasis of matter"
            else:
                result_value = "Adverse"
                score_tier, result_label = "Score_1", "Adverse opinion"

        elif cp_id == 20:  # Contingent Burden
            cl = ml.get("contingent_liabilities")
            nw = itr.get("net_worth")
            if cl is None or nw is None:
                return _missing_result(cp, ["contingent_liabilities", "net_worth"])
            if nw > 0:
                pct = (cl / nw) * 100
                result_value = round(pct, 1)
                if pct < 10:
                    score_tier, result_label = "Score_3", f"{result_value}% burden"
                elif pct <= 20:
                    score_tier, result_label = "Score_2", f"{result_value}% burden"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% burden"
            else:
                return _missing_result(cp, ["net_worth (zero)"])

        elif cp_id == 21:  # Conflict Check (RPT)
            rpt = ml.get("rpt_value")
            rev = itr.get("itr_turnover")
            if rpt is None or rev is None:
                return _missing_result(cp, ["rpt_value", "itr_turnover"])
            if rev > 0:
                pct = (rpt / rev) * 100
                result_value = round(pct, 1)
                if pct < 5:
                    score_tier, result_label = "Score_3", f"{result_value}% RPT"
                elif pct <= 10:
                    score_tier, result_label = "Score_2", f"{result_value}% RPT"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% RPT"
            else:
                return _missing_result(cp, ["itr_turnover (zero)"])

        elif cp_id == 22:  # KMP Stability
            kmp = ml.get("last_kmp_change_date")
            if not _is_present(kmp):
                return _missing_result(cp, ["last_kmp_change_date"])
            days = _days_since(kmp)
            if days is not None:
                years = days / 365.25
                result_value = round(years, 1)
                if years >= 2:
                    score_tier, result_label = "Score_3", f"{result_value} yrs stable"
                elif years >= 1:
                    score_tier, result_label = "Score_2", "1 planned change"
                else:
                    score_tier, result_label = "Score_1", "Sudden resignation"
            else:
                return _missing_result(cp, ["last_kmp_change_date (unparseable)"])

        elif cp_id == 23:  # Share Pledge
            pledged = ml.get("pledged_shares")
            total = ml.get("total_promoter_shares")
            if pledged is None or total is None:
                return _missing_result(cp, ["pledged_shares", "total_promoter_shares"])
            if total > 0:
                pct = (pledged / total) * 100
                result_value = round(pct, 1)
                if pct < 10:
                    score_tier, result_label = "Score_3", f"{result_value}% pledged"
                elif pct <= 30:
                    score_tier, result_label = "Score_2", f"{result_value}% pledged"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% pledged"
            else:
                return _missing_result(cp, ["total_promoter_shares (zero)"])

        elif cp_id == 24:  # Intent Alignment
            alignment = ml.get("intent_alignment", "")
            if not _is_present(alignment):
                return _missing_result(cp, ["intent_alignment"])
            alignment = alignment.lower().strip()
            if alignment in ("aligned", "strong", "high"):
                result_value = "Aligned"
                score_tier, result_label = "Score_3", "Aligned"
            elif alignment in ("minor shift", "moderate", "partial"):
                result_value = "Minor Shift"
                score_tier, result_label = "Score_2", "Minor shift"
            else:
                result_value = "Divergent"
                score_tier, result_label = "Score_1", "Divergent"

        elif cp_id == 25:  # Litigation Impact
            cases = ml.get("active_litigation_count")
            if cases is None:
                return _missing_result(cp, ["active_litigation_count"])
            result_value = cases
            if cases == 0:
                score_tier, result_label = "Score_3", "No active litigation"
            elif cases <= 2:
                score_tier, result_label = "Score_2", f"{cases} minor civil"
            else:
                score_tier, result_label = "Score_1", f"{cases} cases (Criminal/NCLT)"

        elif cp_id == 26:  # Rating Momentum
            curr = ml.get("current_rating", "")
            prev = ml.get("prev_rating", "")
            if not _is_present(curr) or not _is_present(prev):
                return _missing_result(cp, ["current_rating", "prev_rating"])
            delta = _rating_delta(curr, prev)
            result_value = delta
            if delta in ("Upgrade", "Stable"):
                score_tier, result_label = "Score_3", f"{delta} ({curr})"
            elif "BBB" in curr.upper():
                score_tier, result_label = "Score_2", f"BBB Stable"
            else:
                score_tier, result_label = "Score_1", f"Downgrade to {curr}"

        elif cp_id == 27:  # Operational Health
            actual = ml.get("actual_output")
            cap = ml.get("max_capacity")
            if actual is None or cap is None:
                return _missing_result(cp, ["actual_output", "max_capacity"])
            if cap > 0:
                util = (actual / cap) * 100
                result_value = round(util, 1)
                if util > 80:
                    score_tier, result_label = "Score_3", f"{result_value}% utilization"
                elif util >= 50:
                    score_tier, result_label = "Score_2", f"{result_value}% utilization"
                else:
                    score_tier, result_label = "Score_1", f"{result_value}% utilization"
            else:
                return _missing_result(cp, ["max_capacity (zero)"])

        elif cp_id == 28:  # News Sentiment
            sentiment = ml.get("news_sentiment", "")
            if not _is_present(sentiment):
                return _missing_result(cp, ["news_sentiment"])
            sentiment = sentiment.lower().strip()
            if sentiment in ("positive", "good", "favorable"):
                result_value = "Positive"
                score_tier, result_label = "Score_3", "Positive sentiment"
            elif sentiment in ("headwinds", "neutral", "mixed"):
                result_value = "Headwinds"
                score_tier, result_label = "Score_2", "Headwinds detected"
            else:
                result_value = "Fraud Alert"
                score_tier, result_label = "Score_1", "Fraud alert in news"

        elif cp_id == 29:  # Lien Check
            charged = ml.get("mca_charged_assets")
            if charged is None:
                return _missing_result(cp, ["mca_charged_assets"])
            result_value = charged
            if charged == 0:
                score_tier, result_label = "Score_3", "Free & clear"
            elif charged <= 2:
                score_tier, result_label = "Score_2", "Pari-passu"
            else:
                score_tier, result_label = "Score_1", f"{charged} assets charged"

        elif cp_id == 30:  # Inventory Velocity
            inv = ml.get("avg_inventory")
            cogs = ml.get("cogs")
            if inv is None or cogs is None:
                return _missing_result(cp, ["avg_inventory", "cogs"])
            if cogs > 0 and inv > 0:
                days = (inv / cogs) * 365
                result_value = round(days, 0)
                if days <= 60:
                    score_tier, result_label = "Score_3", f"{int(result_value)} days — fast"
                elif days <= 120:
                    score_tier, result_label = "Score_2", f"{int(result_value)} days — slow"
                else:
                    score_tier, result_label = "Score_1", f"{int(result_value)} days — obsolete"
            else:
                return _missing_result(cp, ["avg_inventory or cogs (zero)"])

    except Exception as e:
        logger.error(f"Error evaluating checkpoint {cp_id} ({cp['name']}): {e}")
        score_tier = "Score_1"
        result_label = f"Evaluation error: {str(e)[:80]}"
        result_value = None

    is_veto = (cp_id in HARD_VETO_IDS) and (score_tier == "Score_1")

    return {
        "id": cp_id,
        "name": cp["name"],
        "cat": cp["cat"],
        "formula": cp["formula"],
        "result_value": result_value,
        "result_label": result_label,
        "score_tier": score_tier,
        "score_points": SCORING_WEIGHTS[score_tier],
        "is_veto": is_veto,
        "data_missing": False,
    }


# ─── Aggregate Scoring ──────────────────────────────────────────────────────


def compute_risk_grade(total_score: int) -> str:
    """Map aggregate score (0-300) to risk grade."""
    if total_score >= 260:
        return "Prime Borrower"
    elif total_score >= 220:
        return "Strong Borrower"
    elif total_score >= 180:
        return "Moderate Risk"
    else:
        return "Reject"


def run_full_audit(extracted_data: dict) -> dict:
    """
    Execute all 30 checkpoints sequentially.
    STOPS IMMEDIATELY on hard veto.
    """
    results = []
    total_score = 0
    vetoed = False
    veto_checkpoint = None

    for cp in CHECKPOINTS:
        r = evaluate_checkpoint(cp, extracted_data)
        results.append(r)
        total_score += r["score_points"]

        if r["is_veto"] and not vetoed:
            vetoed = True
            veto_checkpoint = r
            break  # ← STOP processing on hard veto

    return {
        "results": results,
        "aggregate_score": total_score,
        "risk_grade": "Reject" if vetoed else compute_risk_grade(total_score),
        "vetoed": vetoed,
        "veto_checkpoint": veto_checkpoint,
        "data_completeness": extracted_data.get("_meta", {}),
    }
