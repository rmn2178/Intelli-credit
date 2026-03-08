"""
Pydantic schemas for the Intelli-Credit Decisioning Engine.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── Enums ─────────────────────────────────────────────────────────────────────

class CreditDecisionType(str, Enum):
    APPROVE = "Approve"
    CONDITIONAL_APPROVE = "Conditional Approval"
    REJECT = "Reject"


class EvidenceSeverity(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class RegulatoryRegime(str, Enum):
    RBI_2022 = "RBI Framework 2022"
    RBI_2024 = "RBI Framework 2024"
    FUTURE_SIM = "Future Simulated"


class FraudSignalType(str, Enum):
    CIRCULAR_TRADING = "Circular GST Trading"
    FAKE_INVOICE = "Fake Invoice Chain"
    SHELL_COMPANY = "Shell Company Network"
    FUND_DIVERSION = "Promoter Fund Diversion"
    SUSPICIOUS_VENDOR = "Suspicious Vendor Cluster"


# ─── Request Models ────────────────────────────────────────────────────────────

class LoanInitRequest(BaseModel):
    company_name: str
    cin: Optional[str] = None
    gstin: Optional[str] = None
    loan_amount: Optional[float] = None
    loan_purpose: Optional[str] = None


class SimulationRequest(BaseModel):
    session_id: str
    interest_rate_delta_bps: float = 0
    revenue_change_pct: float = 0
    churn_rate_pct: float = 0
    working_capital_days_delta: int = 0
    gst_compliance_score: float = 100
    mrr_growth_rate: float = 0
    top_customer_exit: bool = False
    regime: RegulatoryRegime = RegulatoryRegime.RBI_2024


# ─── Evidence & Classification ─────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    variable: str
    value: Any = None
    source_document: str = ""
    source_page: Optional[int] = None
    char_offset: Optional[str] = None
    confidence: float = 0.0
    severity: EvidenceSeverity = EvidenceSeverity.GREEN
    summary: str = ""
    formula: Optional[str] = None


class EvidenceReport(BaseModel):
    green: list[EvidenceItem] = Field(default_factory=list)
    yellow: list[EvidenceItem] = Field(default_factory=list)
    red: list[EvidenceItem] = Field(default_factory=list)


# ─── Fraud Radar ───────────────────────────────────────────────────────────────

class FraudSignal(BaseModel):
    signal_type: FraudSignalType
    probability: float = 0.0
    entities_involved: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    description: str = ""
    transaction_ids: list[str] = Field(default_factory=list)


class FraudRadarReport(BaseModel):
    overall_fraud_probability: float = 0.0
    signals: list[FraudSignal] = Field(default_factory=list)
    graph_summary: dict = Field(default_factory=dict)
    key_findings: list[str] = Field(default_factory=list)


# ─── Digital Twin Simulation ───────────────────────────────────────────────────

class ScenarioResult(BaseModel):
    scenario_name: str
    default_probability_before: float = 0.0
    default_probability_after: float = 0.0
    dscr_before: float = 0.0
    dscr_after: float = 0.0
    primary_drivers: list[str] = Field(default_factory=list)
    risk_delta: float = 0.0


class DigitalTwinReport(BaseModel):
    base_risk_score: float = 0.0
    simulated_risk_score: float = 0.0
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    sensitivity_analysis: dict = Field(default_factory=dict)
    counterfactual_insights: list[str] = Field(default_factory=list)


# ─── Committee Debate ──────────────────────────────────────────────────────────

class CommitteePersona(BaseModel):
    role: str  # Risk Officer, Compliance Officer, Business Officer
    position: str  # approve / conditional / reject
    arguments: list[str] = Field(default_factory=list)
    evidence_cited: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = 0.0


class CommitteeDebate(BaseModel):
    personas: list[CommitteePersona] = Field(default_factory=list)
    debate_transcript: str = ""
    final_decision: CreditDecisionType = CreditDecisionType.REJECT
    consensus_score: float = 0.0
    conditions: list[str] = Field(default_factory=list)
    rationale: str = ""


# ─── CAM Report ────────────────────────────────────────────────────────────────

class CAMReport(BaseModel):
    executive_summary: str = ""
    company_profile: dict = Field(default_factory=dict)
    financial_analysis: dict = Field(default_factory=dict)
    gst_reconciliation: dict = Field(default_factory=dict)
    bureau_assessment: dict = Field(default_factory=dict)
    collateral_analysis: dict = Field(default_factory=dict)
    risk_matrix: dict = Field(default_factory=dict)
    fraud_assessment: dict = Field(default_factory=dict)
    recommendation: dict = Field(default_factory=dict)
    evidence_trail: list[EvidenceItem] = Field(default_factory=list)
    full_narrative: str = ""


# ─── Credit Decision ──────────────────────────────────────────────────────────

class CreditDecision(BaseModel):
    borrower: str = ""
    risk_score: float = 0.0
    decision: CreditDecisionType = CreditDecisionType.REJECT
    recommended_limit: str = ""
    interest_rate: str = ""
    tenure_months: int = 0
    collateral_requirements: str = ""
    confidence: float = 0.0
    evidence: list[EvidenceItem] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)


# ─── Self-Updating Intelligence ────────────────────────────────────────────────

class IntelligenceSignal(BaseModel):
    source: str = ""
    headline: str = ""
    impact_type: str = ""  # sector_risk, regulatory, sentiment
    risk_delta_pct: float = 0.0
    timestamp: str = ""
    confidence: float = 0.0


class IntelligenceUpdate(BaseModel):
    signals: list[IntelligenceSignal] = Field(default_factory=list)
    updated_risk_score: float = 0.0
    summary: str = ""


# ─── Forensic Audit Engine ────────────────────────────────────────────────────

class ForensicCheckpointResult(BaseModel):
    id: int
    name: str = ""
    cat: str = ""
    formula: str = ""
    result_value: Any = None
    result_label: str = ""
    score_tier: str = "Score_1"
    score_points: int = 0
    is_veto: bool = False


class ForensicAuditReport(BaseModel):
    results: list[ForensicCheckpointResult] = Field(default_factory=list)
    aggregate_score: int = 0
    risk_grade: str = ""
    vetoed: bool = False
    veto_checkpoint: Optional[ForensicCheckpointResult] = None


class CAMFiveCsReport(BaseModel):
    company_name: str = ""
    loan_amount: float = 0
    loan_purpose: str = ""
    generated_at: str = ""
    character: dict = Field(default_factory=dict)
    capacity: dict = Field(default_factory=dict)
    capital: dict = Field(default_factory=dict)
    collateral: dict = Field(default_factory=dict)
    conditions: dict = Field(default_factory=dict)
    decision: dict = Field(default_factory=dict)
    five_cs_summary: dict = Field(default_factory=dict)
    full_narrative: str = ""

