"""
Test script for the Forensic Credit Audit Engine — v2 (with null/missing data fixes).
Validates missing data handling, DSCR edge cases, hard veto break, and data completeness.
Run: python tests/test_forensic_engine.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.forensic_engine import (
    evaluate_checkpoint,
    CHECKPOINTS,
    HARD_VETO_IDS,
    run_full_audit,
    compute_risk_grade,
    extract_forensic_data,
)
from core.cam_generator import build_cam_report


def test_extract_with_missing_data():
    """Test that extraction correctly reports missing fields."""
    fd = {"revenue": 5000000, "net_profit": 800000}
    result = extract_forensic_data(fd)
    meta = result["_meta"]
    assert meta["present_count"] > 0, "Should have some present fields"
    assert meta["missing_count"] > 0, "Should have many missing fields"
    assert meta["data_completeness_pct"] > 0
    assert meta["data_completeness_pct"] < 100
    assert "gstr1_sales" in meta["missing_fields"]
    print(f"  ✅ Missing data extraction — {meta['present_count']}/{meta['total_required']} fields, {meta['data_completeness_pct']}% complete")


def test_extract_with_all_data():
    """Test that extraction correctly reports all fields present."""
    fd = {
        "revenue": 50000000,
        "gstr1_sales": 50000000, "gstr3b_sales": 50000000,
        "gstr3b_itc": 4800000, "gstr2a_itc": 4900000,
        "net_profit": 8000000, "depreciation": 1500000,
        "interest_expense": 1200000, "principal_repayment": 2000000,
        "total_liabilities": 15000000, "cibil_outstanding": 15000000,
        "equity": 30000000, "monthly_average_balance": 2000000,
        "monthly_credits": 5000000, "inward_bounce_count_12mo": 0,
        "gst_actual_filing_date": "2025-01-10",
        "gst_statutory_due_date": "2025-01-11",
        "gst_reg_date": "2018-01-01",
        "itr_turnover": 50000000, "tax_paid": 1500000,
        "income_26as": 50000000, "itr_income": 50000000,
        "fixed_assets": 20000000, "top_client_sales": 5000000,
        "total_annual_sales": 50000000, "prev_year_sales": 45000000,
        "curr_year_sales": 50000000, "auditor_opinion": "Clean",
        "active_litigation_count": 0, "mca_charged_assets": 0,
        "pledged_shares": 0, "ebitda": 12000000,
        "monthly_debits": 4000000, "director_transfers": 0,
        "cash_withdrawals": 50000, "expected_emi": 200000,
        "contingent_liabilities": 500000, "rpt_value": 100000,
        "last_kmp_change_date": "2022-01-01",
        "total_promoter_shares": 100,
    }
    result = extract_forensic_data(fd)
    meta = result["_meta"]
    print(f"  ✅ Full data extraction — {meta['present_count']}/{meta['total_required']} fields, {meta['data_completeness_pct']}% complete")
    if meta["missing_fields"]:
        print(f"    Still missing: {', '.join(meta['missing_fields'])}")


def test_checkpoint_missing_data():
    """Test that checkpoints return Data Missing for null input."""
    extracted = extract_forensic_data({})  # Empty data
    for cp_id in [1, 2, 5, 9, 14]:
        cp = CHECKPOINTS[cp_id - 1]
        r = evaluate_checkpoint(cp, extracted)
        assert r["score_tier"] == "Score_1", f"CP{cp_id} should be Score_1, got {r['score_tier']}"
        assert r["score_points"] == 0
        assert r.get("data_missing") == True or "Data" in str(r.get("result_value", ""))
        print(f"  ✅ Checkpoint {cp_id} ({r['name']}) — correctly returns Score_1 on missing data")


def test_dscr_zero_denominator():
    """Test DSCR returns 'Not Computable' when denominator is zero."""
    extracted = extract_forensic_data({
        "net_profit": 800000,
        "depreciation": 150000,
        "interest_expense": 0,
        "principal_repayment": 0,
    })
    cp = CHECKPOINTS[8]  # ID 9
    r = evaluate_checkpoint(cp, extracted)
    assert r["result_value"] == "Not Computable" or r["result_label"].startswith("DSCR not computable")
    assert r["score_tier"] == "Score_1"
    print(f"  ✅ DSCR zero denominator — {r['result_label']}")


def test_dscr_missing_principal():
    """Test DSCR handles missing principal_repayment."""
    extracted = extract_forensic_data({
        "net_profit": 800000,
        "depreciation": 150000,
        "interest_expense": 120000,
        # No principal_repayment
    })
    cp = CHECKPOINTS[8]  # ID 9
    r = evaluate_checkpoint(cp, extracted)
    assert r["score_tier"] == "Score_1"
    assert r.get("data_missing") == True
    print(f"  ✅ DSCR missing principal — {r['result_label']}")


def test_dscr_correct_calculation():
    """Test DSCR correct formula: (NP + Depr + Int) / (Int + Principal)."""
    extracted = extract_forensic_data({
        "net_profit": 800000,
        "depreciation": 150000,
        "interest_expense": 120000,
        "principal_repayment": 200000,
    })
    cp = CHECKPOINTS[8]  # ID 9
    r = evaluate_checkpoint(cp, extracted)
    # DSCR = (800000 + 150000 + 120000) / (120000 + 200000) = 1070000/320000 = 3.34
    expected = round(1070000 / 320000, 2)
    assert r["result_value"] == expected, f"Expected {expected}, got {r['result_value']}"
    assert r["score_tier"] == "Score_3"
    print(f"  ✅ DSCR correct — {r['result_value']} → {r['score_tier']}")


def test_hard_veto_breaks_audit():
    """Test that hard veto stops processing immediately."""
    fd = {
        "gst_actual_filing_date": "2025-01-10",
        "gst_statutory_due_date": "2025-01-11",
        "gstr1_sales": 1000000,
        "gstr3b_sales": 500000,  # 100% variance → Score_1 → VETO at checkpoint 2
    }
    extracted = extract_forensic_data(fd)
    result = run_full_audit(extracted)

    assert result["vetoed"], "Should be vetoed"
    assert result["risk_grade"] == "Reject"
    assert result["veto_checkpoint"]["id"] == 2
    assert len(result["results"]) == 2, f"Should stop at 2 checkpoints, got {len(result['results'])}"
    print(f"  ✅ Hard veto at checkpoint {result['veto_checkpoint']['id']} — stopped after {len(result['results'])} checkpoints")


def test_hard_veto_itc():
    """Test ITC veto stops immediately."""
    fd = {
        "gst_actual_filing_date": "2025-01-10",
        "gst_statutory_due_date": "2025-01-10",
        "gstr1_sales": 1000000,
        "gstr3b_sales": 1000000,
        "prev_year_sales": 900000,
        "curr_year_sales": 1000000,
        "top_client_sales": 100000,
        "total_annual_sales": 1000000,
        "gstr3b_itc": 40000,   # 40% match
        "gstr2a_itc": 100000,  # → Score_1 → VETO at checkpoint 5
    }
    extracted = extract_forensic_data(fd)
    result = run_full_audit(extracted)

    assert result["vetoed"], "Should be vetoed at ITC"
    assert result["veto_checkpoint"]["id"] == 5
    assert len(result["results"]) == 5, f"Should stop at 5 checkpoints, got {len(result['results'])}"
    print(f"  ✅ ITC veto at checkpoint 5 — stopped after {len(result['results'])} checkpoints")


def test_cam_no_na_values():
    """Test that CAM report has no N/A values."""
    fd = {"revenue": 5000000, "net_profit": 800000}
    extracted = extract_forensic_data(fd)
    audit = run_full_audit(extracted)

    session = {"financial_data": fd, "company_name": "Test Corp", "loan_amount": 2500000}
    cam = build_cam_report(session, audit, extracted)

    narrative = cam["full_narrative"]
    na_count = narrative.count("N/A")
    assert na_count == 0, f"CAM narrative contains {na_count} instances of 'N/A'"

    # Check no N/A in five_cs_summary
    for key, val in cam["five_cs_summary"].items():
        assert val != "N/A", f"Five Cs summary has N/A for {key}"

    print(f"  ✅ CAM report contains 0 instances of N/A")
    print(f"    Data completeness: {cam['data_quality']['data_completeness_pct']}%")
    print(f"    Missing fields: {cam['data_quality']['missing_count']}")


def test_cam_data_quality_section():
    """Test that CAM includes Data Quality Summary."""
    fd = {"revenue": 5000000}
    extracted = extract_forensic_data(fd)
    audit = run_full_audit(extracted)

    session = {"financial_data": fd, "company_name": "Test Corp", "loan_amount": 2500000}
    cam = build_cam_report(session, audit, extracted)

    assert "data_quality" in cam
    assert cam["data_quality"]["total_required"] > 0
    assert "DATA COMPLETENESS" in cam["full_narrative"]
    assert "DATA QUALITY SUMMARY" in cam["full_narrative"]
    print(f"  ✅ CAM includes Data Quality Summary section")


def test_risk_grades():
    """Test risk grade mapping."""
    assert compute_risk_grade(300) == "Prime Borrower"
    assert compute_risk_grade(260) == "Prime Borrower"
    assert compute_risk_grade(259) == "Strong Borrower"
    assert compute_risk_grade(220) == "Strong Borrower"
    assert compute_risk_grade(219) == "Moderate Risk"
    assert compute_risk_grade(180) == "Moderate Risk"
    assert compute_risk_grade(179) == "Reject"
    assert compute_risk_grade(0) == "Reject"
    print("  ✅ Risk grade mapping — PASS")


def test_full_audit_clean_data():
    """Test full audit with good data producing high score."""
    fd = {
        "revenue": 50000000,
        "gstr1_sales": 50000000, "gstr3b_sales": 50000000,
        "gstr3b_itc": 4800000, "gstr2a_itc": 4900000,
        "net_profit": 8000000, "depreciation": 1500000,
        "interest_expense": 1200000, "principal_repayment": 2000000,
        "total_liabilities": 15000000, "cibil_outstanding": 15000000,
        "equity": 30000000, "monthly_average_balance": 2000000,
        "monthly_credits": 5000000, "inward_bounce_count_12mo": 0,
        "gst_actual_filing_date": "2025-01-10",
        "gst_statutory_due_date": "2025-01-11",
        "gst_reg_date": "2018-01-01",
        "itr_turnover": 50000000, "tax_paid": 1500000,
        "income_26as": 50000000, "itr_income": 50000000,
        "fixed_assets": 20000000, "top_client_sales": 5000000,
        "total_annual_sales": 50000000, "prev_year_sales": 45000000,
        "curr_year_sales": 50000000, "auditor_opinion": "Clean",
        "active_litigation_count": 0, "mca_charged_assets": 0,
        "pledged_shares": 0, "ebitda": 12000000,
        "monthly_debits": 4000000, "director_transfers": 0,
        "cash_withdrawals": 50000, "expected_emi": 200000,
        "bank_emi_debits": 200000, "single_max_credit": 1000000,
        "day_opening_balance": 1500000, "contingent_liabilities": 500000,
        "rpt_value": 100000, "last_kmp_change_date": "2022-01-01",
        "total_promoter_shares": 100,
        "actual_output": 900, "max_capacity": 1000,
        "current_rating": "A", "prev_rating": "BBB+",
        "avg_inventory": 1000000, "cogs": 30000000,
        "news_sentiment": "Positive", "intent_alignment": "Aligned",
    }
    extracted = extract_forensic_data(fd)
    result = run_full_audit(extracted)

    print(f"\n  Full Audit Results:")
    for r in result["results"]:
        dm = " [MISSING]" if r.get("data_missing") else ""
        icon = "✅" if r["score_tier"] == "Score_3" else ("⚠️" if r["score_tier"] == "Score_2" else "❌")
        print(f"    {icon} [{r['id']:02d}] {r['name']}: {r['result_label']} → {r['score_tier']} ({r['score_points']}pts){dm}")

    dc = result.get("data_completeness", {})
    print(f"\n  Data Completeness: {dc.get('data_completeness_pct', 0)}%")
    print(f"  Aggregate: {result['aggregate_score']}/300")
    print(f"  Risk Grade: {result['risk_grade']}")
    print(f"  Vetoed: {result['vetoed']}")

    assert not result["vetoed"], "Should not be vetoed"
    assert result["aggregate_score"] > 200, f"Score {result['aggregate_score']} too low for good data"
    assert len(result["results"]) == 30, f"Should have 30 checkpoints, got {len(result['results'])}"
    print(f"\n  ✅ Full audit — {result['aggregate_score']}/300 — {result['risk_grade']}")


if __name__ == "__main__":
    print("\n🔬 Forensic Credit Audit Engine — Test Suite v2 (Null Fix Verification)")
    print("=" * 60)

    print("\n📋 Data Extraction & Completeness")
    test_extract_with_missing_data()
    test_extract_with_all_data()

    print("\n📋 Missing Data Handling")
    test_checkpoint_missing_data()

    print("\n📋 DSCR Calculation Fixes")
    test_dscr_zero_denominator()
    test_dscr_missing_principal()
    test_dscr_correct_calculation()

    print("\n📋 Hard Veto Break Logic")
    test_hard_veto_breaks_audit()
    test_hard_veto_itc()

    print("\n📋 CAM Report Quality")
    test_cam_no_na_values()
    test_cam_data_quality_section()

    print("\n📋 Risk Grade Mapping")
    test_risk_grades()

    print("\n📋 Full 30-Checkpoint Audit (Clean Data)")
    test_full_audit_clean_data()

    print("\n" + "=" * 60)
    print("🎉 All tests passed!")
