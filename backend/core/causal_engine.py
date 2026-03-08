"""
Causal AI & Digital Twin Engine — Financial simulation and counterfactual analysis.
Simulates interest rate shocks, revenue declines, customer concentration risk,
and working capital cycle changes.
"""

import math
from typing import Any


class CausalEngine:
    """
    Financial Digital Twin that simulates how a borrower behaves
    under changing economic conditions.
    """

    def __init__(self, financial_data: dict = None):
        self.data = financial_data or {}
        self.base_metrics = self._compute_base_metrics()

    def _compute_base_metrics(self) -> dict:
        """Compute baseline metrics from extracted financial data."""
        revenue = self.data.get("revenue", 0)
        net_profit = self.data.get("net_profit", 0)
        ebitda = self.data.get("ebitda", 0)
        interest = self.data.get("interest_expense", 0)
        depreciation = self.data.get("depreciation", 0)
        debt = self.data.get("debt", 0)
        equity = self.data.get("equity", 0)
        current_assets = self.data.get("current_assets", 0)
        current_liabilities = self.data.get("current_liabilities", 0)
        operating_cf = self.data.get("operating_cash_flow", 0)

        # Base default probability using Altman Z-Score inspired model
        z_score = self._compute_z_score()
        exponent = max(-500, min(500, z_score - 2.5))  # Clamp to prevent overflow
        base_pd = max(0.01, min(0.99, 1 / (1 + math.exp(exponent))))

        annual_principal = debt * 0.1 if debt else 0
        dscr_denom = interest + annual_principal
        dscr = (net_profit + depreciation + interest) / dscr_denom if dscr_denom > 0 else 0

        return {
            "revenue": revenue,
            "net_profit": net_profit,
            "ebitda": ebitda,
            "interest_expense": interest,
            "depreciation": depreciation,
            "debt": debt,
            "equity": equity,
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "operating_cash_flow": operating_cf,
            "dscr": round(dscr, 2),
            "default_probability": round(base_pd, 4),
            "z_score": round(z_score, 2),
            "operating_margin": round(ebitda / revenue * 100, 1) if revenue else 0,
        }

    def _compute_z_score(self) -> float:
        """Simplified Altman Z-Score for private Indian companies."""
        ta = self.data.get("total_assets", 1)
        wc = self.data.get("current_assets", 0) - self.data.get("current_liabilities", 0)
        re = self.data.get("retained_earnings", self.data.get("net_profit", 0))
        ebit = self.data.get("ebitda", 0) - self.data.get("depreciation", 0)
        equity = self.data.get("equity", 1)
        debt = self.data.get("debt", 0)
        revenue = self.data.get("revenue", 0)

        if ta == 0:
            ta = 1

        x1 = wc / ta
        x2 = re / ta
        x3 = ebit / ta
        x4 = equity / max(debt, 1)
        x5 = revenue / ta

        return 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5

    def simulate_interest_rate_shock(self, delta_bps: float) -> dict:
        """
        Simulate RBI interest rate increase.
        delta_bps: basis points change (e.g., 100 = +1%)
        """
        delta_pct = delta_bps / 100
        base = self.base_metrics

        new_interest = base["interest_expense"] * (1 + delta_pct / 10)
        interest_increase = new_interest - base["interest_expense"]

        new_net_profit = base["net_profit"] - interest_increase
        new_ebitda = base["ebitda"]  # EBITDA unaffected by interest

        annual_principal = base["debt"] * 0.1
        new_dscr_denom = new_interest + annual_principal
        new_dscr = (
            (new_net_profit + base["depreciation"] + new_interest) / new_dscr_denom
            if new_dscr_denom > 0 else 0
        )

        # Impact on default probability
        pd_delta = delta_bps * 0.0005  # Each 100bps adds ~5% to PD
        new_pd = min(0.99, base["default_probability"] + pd_delta)

        return {
            "scenario_name": f"Interest Rate +{delta_bps}bps",
            "default_probability_before": base["default_probability"],
            "default_probability_after": round(new_pd, 4),
            "dscr_before": base["dscr"],
            "dscr_after": round(new_dscr, 2),
            "interest_expense_change": round(interest_increase, 0),
            "net_profit_impact": round(-interest_increase, 0),
            "risk_delta": round(new_pd - base["default_probability"], 4),
            "primary_drivers": [
                f"Interest expense increases by ₹{interest_increase:,.0f}",
                f"DSCR drops from {base['dscr']:.2f} to {new_dscr:.2f}",
                f"Default probability rises by {pd_delta * 100:.1f}%",
            ],
        }

    def simulate_revenue_shock(self, decline_pct: float) -> dict:
        """
        Simulate revenue decline.
        decline_pct: percentage decline (e.g., 10 = -10%)
        """
        base = self.base_metrics
        factor = 1 - (decline_pct / 100)

        new_revenue = base["revenue"] * factor
        # Assume operating margin holds partially (sticky costs)
        margin = base["operating_margin"] / 100 if base["operating_margin"] else 0.15
        cost_stickiness = 0.7  # 70% of costs are fixed short-term
        variable_cost_ratio = 1 - margin

        new_ebitda = new_revenue * margin - base["revenue"] * variable_cost_ratio * cost_stickiness * (decline_pct / 100)
        new_ebitda = max(0, new_ebitda)

        new_net_profit = new_ebitda - base["interest_expense"] - base["depreciation"]

        annual_principal = base["debt"] * 0.1
        dscr_denom = base["interest_expense"] + annual_principal
        new_dscr = (
            (new_net_profit + base["depreciation"] + base["interest_expense"]) / dscr_denom
            if dscr_denom > 0 else 0
        )

        pd_delta = decline_pct * 0.015  # Each 1% revenue drop adds ~1.5% to PD
        new_pd = min(0.99, base["default_probability"] + pd_delta)

        return {
            "scenario_name": f"Revenue Decline {decline_pct}%",
            "default_probability_before": base["default_probability"],
            "default_probability_after": round(new_pd, 4),
            "dscr_before": base["dscr"],
            "dscr_after": round(new_dscr, 2),
            "revenue_before": base["revenue"],
            "revenue_after": round(new_revenue, 0),
            "risk_delta": round(new_pd - base["default_probability"], 4),
            "primary_drivers": [
                f"Revenue drops from ₹{base['revenue']:,.0f} to ₹{new_revenue:,.0f}",
                f"DSCR drops from {base['dscr']:.2f} to {new_dscr:.2f}",
                f"Default probability rises by {pd_delta * 100:.1f}%",
                "High working capital cycle amplifies impact" if base.get("current_assets", 0) > base.get("current_liabilities", 0) * 2 else "Working capital provides buffer",
            ],
        }

    def simulate_customer_concentration(self, top_customer_pct: float = 0) -> dict:
        """
        Simulate loss of top customer.
        top_customer_pct: revenue share of top customer (auto-detected or provided)
        """
        base = self.base_metrics
        if top_customer_pct == 0:
            top_customer_pct = self.data.get("top_customer_share_pct", 25)

        revenue_loss = base["revenue"] * (top_customer_pct / 100)
        return self.simulate_revenue_shock(top_customer_pct)

    def simulate_churn(self, churn_increase_pct: float) -> dict:
        """
        Simulate increase in customer churn rate.
        Assumes SaaS-like revenue model with MRR.
        """
        base = self.base_metrics
        # Churn impacts future revenue — approximate as revenue decline
        effective_decline = churn_increase_pct * 0.8  # 5% churn increase ≈ 4% revenue hit
        result = self.simulate_revenue_shock(effective_decline)
        result["scenario_name"] = f"Churn Rate +{churn_increase_pct}%"
        result["primary_drivers"].append(
            f"Customer churn increase of {churn_increase_pct}% translates to ~{effective_decline:.1f}% revenue impact"
        )
        return result

    def simulate_working_capital_stress(self, days_delta: int) -> dict:
        """Simulate working capital cycle extension."""
        base = self.base_metrics
        daily_revenue = base["revenue"] / 365 if base["revenue"] else 0
        additional_wc_needed = daily_revenue * days_delta

        new_ca = base["current_assets"] + additional_wc_needed
        new_cr = new_ca / base["current_liabilities"] if base["current_liabilities"] > 0 else 0

        pd_delta = days_delta * 0.002
        new_pd = min(0.99, base["default_probability"] + pd_delta)

        return {
            "scenario_name": f"Working Capital +{days_delta} Days",
            "default_probability_before": base["default_probability"],
            "default_probability_after": round(new_pd, 4),
            "dscr_before": base["dscr"],
            "dscr_after": base["dscr"],  # DSCR not directly affected
            "additional_wc_needed": round(additional_wc_needed, 0),
            "current_ratio_after": round(new_cr, 2),
            "risk_delta": round(new_pd - base["default_probability"], 4),
            "primary_drivers": [
                f"Additional working capital of ₹{additional_wc_needed:,.0f} needed",
                f"Cash flow pressure increases",
                "Low liquidity buffer" if new_cr < 1.5 else "Adequate liquidity buffer",
            ],
        }

    def run_comprehensive_simulation(self, params: dict = None) -> dict:
        """
        Run all simulation scenarios and return combined results.
        """
        params = params or {}

        scenarios = []

        # Interest rate scenarios
        for bps in [100, 200]:
            scenarios.append(self.simulate_interest_rate_shock(bps))

        # Revenue scenarios
        for pct in [5, 10, 20]:
            scenarios.append(self.simulate_revenue_shock(pct))

        # Customer concentration
        scenarios.append(self.simulate_customer_concentration())

        # Churn
        if params.get("churn_rate_pct", 0) > 0:
            scenarios.append(self.simulate_churn(params["churn_rate_pct"]))
        else:
            scenarios.append(self.simulate_churn(5))

        # Working capital
        if params.get("working_capital_days_delta", 0) > 0:
            scenarios.append(
                self.simulate_working_capital_stress(params["working_capital_days_delta"])
            )

        # Custom simulation from params
        if params.get("interest_rate_delta_bps", 0) != 0:
            scenarios.append(
                self.simulate_interest_rate_shock(params["interest_rate_delta_bps"])
            )
        if params.get("revenue_change_pct", 0) != 0:
            scenarios.append(
                self.simulate_revenue_shock(abs(params["revenue_change_pct"]))
            )

        # Sensitivity analysis
        sensitivity = {
            "interest_rate_sensitivity": round(
                (scenarios[1]["default_probability_after"] - self.base_metrics["default_probability"]) / 200 * 10000, 2
            ) if len(scenarios) > 1 else 0,
            "revenue_sensitivity": round(
                (scenarios[3]["default_probability_after"] - self.base_metrics["default_probability"]) / 10 * 100, 2
            ) if len(scenarios) > 3 else 0,
        }

        # Counterfactual insights
        worst_case = max(scenarios, key=lambda s: s["default_probability_after"])
        counterfactuals = [
            f"Worst-case scenario: '{worst_case['scenario_name']}' raises default probability to {worst_case['default_probability_after']*100:.1f}%",
        ]

        if self.base_metrics["dscr"] < 1.5:
            counterfactuals.append(
                "Low DSCR makes the borrower highly sensitive to any revenue or interest shock"
            )

        return {
            "base_risk_score": self.base_metrics["default_probability"],
            "base_metrics": self.base_metrics,
            "scenarios": scenarios,
            "sensitivity_analysis": sensitivity,
            "counterfactual_insights": counterfactuals,
        }
