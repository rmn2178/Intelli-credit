"""
In-memory session store for Intelli-Credit Decisioning Engine.
Stores all processing artifacts, CAM reports, committee debates, simulation results.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional


class SessionStore:
    """Thread-safe in-memory session store."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, company_name: str, **kwargs) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "id": session_id,
            "company_name": company_name,
            "cin": kwargs.get("cin"),
            "gstin": kwargs.get("gstin"),
            "loan_amount": kwargs.get("loan_amount"),
            "loan_purpose": kwargs.get("loan_purpose"),
            "created_at": datetime.utcnow().isoformat(),
            "status": "initialized",
            # Document storage
            "documents": {},       # doc_type -> {filename, path, text, pages}
            "doc_types": [],
            # Extracted financial data
            "financial_data": {},
            # Evidence classification
            "evidence": {"green": [], "yellow": [], "red": []},
            # Calculations
            "calculations": {},
            # Knowledge graph data
            "graph_data": {},
            # Fraud radar
            "fraud_report": {},
            # Digital twin / simulation
            "simulation_results": {},
            # Committee debate
            "committee_debate": {},
            # CAM report
            "cam_report": {},
            # OSINT / CRM
            "osint_findings": [],
            "crm_report": "",
            # Credit decision
            "credit_decision": {},
            # Intelligence updates
            "intelligence_updates": [],
            # Processing logs
            "processing_logs": [],
            # Forensic Audit Engine
            "forensic_audit": {
                "extracted_data": {},
                "audit_scores": [],
                "processing_state": "pending",
                "aggregate_score": 0,
                "risk_grade": "",
                "vetoed": False,
                "veto_checkpoint": None,
                "cam_five_cs": {},
                "data_completeness_score": 0,
            },
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.update(kwargs)

    def add_document(
        self,
        session_id: str,
        doc_type: str,
        filename: str,
        path: str,
        text: str = "",
        pages: int = 0,
    ) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["documents"][doc_type] = {
                "filename": filename,
                "path": path,
                "text": text,
                "pages": pages,
            }
            if doc_type not in session["doc_types"]:
                session["doc_types"].append(doc_type)

    def set_financial_data(self, session_id: str, data: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["financial_data"].update(data)

    def set_evidence(self, session_id: str, evidence: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["evidence"] = evidence

    def set_calculations(self, session_id: str, calcs: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["calculations"] = calcs

    def set_fraud_report(self, session_id: str, report: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["fraud_report"] = report

    def set_simulation_results(self, session_id: str, results: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["simulation_results"] = results

    def set_committee_debate(self, session_id: str, debate: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["committee_debate"] = debate

    def set_cam_report(self, session_id: str, report: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["cam_report"] = report

    def set_credit_decision(self, session_id: str, decision: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["credit_decision"] = decision

    # ─── Forensic Audit Methods ──────────────────────────────────────────────
    def set_forensic_extracted(self, session_id: str, data: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["forensic_audit"]["extracted_data"] = data

    def set_forensic_scores(self, session_id: str, scores: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["forensic_audit"]["audit_scores"] = scores.get("results", [])
            session["forensic_audit"]["aggregate_score"] = scores.get("aggregate_score", 0)
            session["forensic_audit"]["risk_grade"] = scores.get("risk_grade", "")
            session["forensic_audit"]["vetoed"] = scores.get("vetoed", False)
            session["forensic_audit"]["veto_checkpoint"] = scores.get("veto_checkpoint")
            # Data completeness from extraction meta
            dc = scores.get("data_completeness", {})
            session["forensic_audit"]["data_completeness_score"] = dc.get("data_completeness_pct", 0)

    def set_forensic_state(self, session_id: str, state: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["forensic_audit"]["processing_state"] = state

    def set_forensic_cam(self, session_id: str, cam: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["forensic_audit"]["cam_five_cs"] = cam

    def add_log(self, session_id: str, stage: str, message: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["processing_logs"].append({
                "stage": stage,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            })
