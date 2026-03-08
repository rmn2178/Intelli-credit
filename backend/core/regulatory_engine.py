"""
Constitutional Regulatory Engine — RBI Master Directions.
Embeds Indian banking regulations and checks compliance.
Supports multiple policy regimes (2022, 2024, future simulated).
"""

from typing import Any


# ─── RBI Regulatory Regimes ────────────────────────────────────────────────────

REGIMES = {
    "RBI Framework 2022": {
        "exposure_limit_individual_pct": 15,  # % of capital funds
        "exposure_limit_group_pct": 40,
        "msme_priority_sector_target_pct": 7.5,
        "capital_adequacy_minimum_pct": 9.0,
        "npa_classification_days": 90,
        "provisioning_standard_pct": 0.4,
        "provisioning_substandard_pct": 15,
        "provisioning_doubtful_pct": 25,
        "single_borrower_limit_cr": 250,
        "dscr_minimum": 1.25,
        "current_ratio_minimum": 1.33,
        "de_ratio_maximum": 3.0,
        "label": "RBI Framework 2022",
    },
    "RBI Framework 2024": {
        "exposure_limit_individual_pct": 20,
        "exposure_limit_group_pct": 25,
        "msme_priority_sector_target_pct": 8.0,
        "capital_adequacy_minimum_pct": 11.5,
        "npa_classification_days": 90,
        "provisioning_standard_pct": 0.4,
        "provisioning_substandard_pct": 15,
        "provisioning_doubtful_pct": 40,
        "single_borrower_limit_cr": 300,
        "dscr_minimum": 1.25,
        "current_ratio_minimum": 1.33,
        "de_ratio_maximum": 2.5,
        "label": "RBI Framework 2024",
        "ecl_model_required": True,
        "ind_as_109_applicable": True,
    },
    "Future Simulated": {
        "exposure_limit_individual_pct": 15,
        "exposure_limit_group_pct": 20,
        "msme_priority_sector_target_pct": 10.0,
        "capital_adequacy_minimum_pct": 13.0,
        "npa_classification_days": 60,
        "provisioning_standard_pct": 0.5,
        "provisioning_substandard_pct": 20,
        "provisioning_doubtful_pct": 50,
        "single_borrower_limit_cr": 200,
        "dscr_minimum": 1.5,
        "current_ratio_minimum": 1.5,
        "de_ratio_maximum": 2.0,
        "label": "Future Simulated (Stricter)",
        "ecl_model_required": True,
        "climate_risk_disclosure": True,
    },
}


class RegulatoryEngine:
    """
    Checks credit decisions against RBI Master Directions.
    Supports switching between regulatory regimes.
    """

    def __init__(self, regime: str = "RBI Framework 2024"):
        self.regime_name = regime
        self.rules = REGIMES.get(regime, REGIMES["RBI Framework 2024"])

    def set_regime(self, regime: str) -> None:
        """Switch regulatory regime."""
        self.regime_name = regime
        self.rules = REGIMES.get(regime, REGIMES["RBI Framework 2024"])

    def check_compliance(
        self,
        loan_amount: float,
        calculations: dict,
        financial_data: dict,
    ) -> dict:
        """
        Run all regulatory compliance checks.
        Returns dict with pass/fail for each rule.
        """
        results = {
            "regime": self.regime_name,
            "checks": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }

        # ─── 1. Exposure Limit ────────────────────────────────────────────
        limit_cr = self.rules["single_borrower_limit_cr"] * 1_00_00_000
        if loan_amount > 0:
            if loan_amount <= limit_cr:
                results["checks"].append({
                    "rule": "Single Borrower Exposure Limit",
                    "status": "PASS",
                    "detail": f"Loan ₹{loan_amount/1e7:.2f} Cr within limit of ₹{self.rules['single_borrower_limit_cr']} Cr",
                    "reference": f"RBI Master Direction — Large Exposures Framework ({self.regime_name})",
                })
                results["passed"] += 1
            else:
                results["checks"].append({
                    "rule": "Single Borrower Exposure Limit",
                    "status": "FAIL",
                    "detail": f"Loan ₹{loan_amount/1e7:.2f} Cr EXCEEDS limit of ₹{self.rules['single_borrower_limit_cr']} Cr",
                    "reference": f"RBI Master Direction — Large Exposures Framework ({self.regime_name})",
                })
                results["failed"] += 1

        # ─── 2. DSCR Check ───────────────────────────────────────────────
        dscr_val = calculations.get("dscr", {}).get("value", 0)
        dscr_min = self.rules["dscr_minimum"]
        if dscr_val >= dscr_min:
            results["checks"].append({
                "rule": "Debt Service Coverage Ratio",
                "status": "PASS",
                "detail": f"DSCR {dscr_val:.2f} ≥ {dscr_min} minimum",
                "reference": "RBI — Assessment of Working Capital",
            })
            results["passed"] += 1
        else:
            results["checks"].append({
                "rule": "Debt Service Coverage Ratio",
                "status": "FAIL",
                "detail": f"DSCR {dscr_val:.2f} < {dscr_min} minimum — inadequate debt servicing capacity",
                "reference": "RBI — Assessment of Working Capital",
            })
            results["failed"] += 1

        # ─── 3. Current Ratio ────────────────────────────────────────────
        cr_val = calculations.get("current_ratio", {}).get("value", 0)
        cr_min = self.rules["current_ratio_minimum"]
        if cr_val >= cr_min:
            results["checks"].append({
                "rule": "Current Ratio (Working Capital)",
                "status": "PASS",
                "detail": f"CR {cr_val:.2f} ≥ {cr_min} minimum",
                "reference": "RBI — Working Capital Finance Norms",
            })
            results["passed"] += 1
        else:
            results["checks"].append({
                "rule": "Current Ratio (Working Capital)",
                "status": "FAIL" if cr_val < 1.0 else "WARNING",
                "detail": f"CR {cr_val:.2f} {'<' if cr_val < cr_min else '≥'} {cr_min}",
                "reference": "RBI — Working Capital Finance Norms",
            })
            if cr_val < 1.0:
                results["failed"] += 1
            else:
                results["warnings"] += 1

        # ─── 4. Debt-Equity Ratio ────────────────────────────────────────
        de_val = calculations.get("debt_equity_ratio", {}).get("value", 0)
        de_max = self.rules["de_ratio_maximum"]
        if de_val <= de_max:
            results["checks"].append({
                "rule": "Debt-to-Equity Ratio",
                "status": "PASS",
                "detail": f"D/E {de_val:.2f} ≤ {de_max} maximum",
                "reference": f"RBI Prudential Norms ({self.regime_name})",
            })
            results["passed"] += 1
        else:
            results["checks"].append({
                "rule": "Debt-to-Equity Ratio",
                "status": "FAIL",
                "detail": f"D/E {de_val:.2f} > {de_max} maximum — overleveraged",
                "reference": f"RBI Prudential Norms ({self.regime_name})",
            })
            results["failed"] += 1

        # ─── 5. MSME Priority Sector ─────────────────────────────────────
        is_msme = financial_data.get("is_msme", False)
        if is_msme:
            results["checks"].append({
                "rule": "MSME Priority Sector Lending",
                "status": "PASS",
                "detail": f"MSME borrower — qualifies under priority sector target ({self.rules['msme_priority_sector_target_pct']}%)",
                "reference": "RBI — Priority Sector Lending Guidelines",
            })
            results["passed"] += 1

        # ─── 6. NPA History ──────────────────────────────────────────────
        npa_days = financial_data.get("overdue_days", 0)
        npa_limit = self.rules["npa_classification_days"]
        if npa_days < npa_limit:
            results["checks"].append({
                "rule": "NPA Classification Check",
                "status": "PASS",
                "detail": f"No overdue beyond {npa_limit} days (current: {npa_days} days)",
                "reference": "RBI — Income Recognition and Asset Classification",
            })
            results["passed"] += 1
        else:
            results["checks"].append({
                "rule": "NPA Classification Check",
                "status": "FAIL",
                "detail": f"Overdue {npa_days} days ≥ {npa_limit} days — NPA classification triggered",
                "reference": "RBI — IRAC Norms",
            })
            results["failed"] += 1

        # ─── 7. Capital Adequacy ─────────────────────────────────────────
        results["checks"].append({
            "rule": "Capital Adequacy Requirement",
            "status": "INFO",
            "detail": f"Bank must maintain CRAR ≥ {self.rules['capital_adequacy_minimum_pct']}% under {self.regime_name}",
            "reference": "RBI — Master Circular on Basel III Capital Regulations",
        })

        # Overall compliance
        results["overall_status"] = (
            "COMPLIANT" if results["failed"] == 0
            else "NON-COMPLIANT" if results["failed"] >= 2
            else "CONDITIONAL"
        )

        return results

    def recalculate_for_regime(
        self, regime: str, loan_amount: float, calculations: dict, financial_data: dict
    ) -> dict:
        """Recalculate compliance under a different regulatory regime."""
        self.set_regime(regime)
        return self.check_compliance(loan_amount, calculations, financial_data)

    def get_regime_comparison(
        self, loan_amount: float, calculations: dict, financial_data: dict
    ) -> dict:
        """Compare compliance across all regimes."""
        comparison = {}
        for regime_name in REGIMES:
            self.set_regime(regime_name)
            comparison[regime_name] = self.check_compliance(
                loan_amount, calculations, financial_data
            )
        return comparison
