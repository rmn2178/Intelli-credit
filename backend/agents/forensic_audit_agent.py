"""
Forensic Audit Agent — Streams 30-checkpoint audit as SSE events.
Matches the existing agent pattern (async generator yielding messages).
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator

from core.forensic_engine import (
    CHECKPOINTS,
    extract_forensic_data,
    evaluate_checkpoint,
    compute_risk_grade,
    HARD_VETO_IDS,
)

logger = logging.getLogger("forensic_audit_agent")


class ForensicAuditAgent:
    """Runs the 30-checkpoint forensic audit, yielding live reasoning traces."""

    def __init__(self, session_id: str, session_store):
        self.session_id = session_id
        self.store = session_store

    async def run(self) -> AsyncGenerator[dict, None]:
        """
        Execute forensic audit.  Yields dicts with keys:
          - type: "checkpoint" | "veto" | "complete"
          - plus checkpoint-specific fields
        """
        session = self.store.get_session(self.session_id)
        if not session:
            yield {"type": "error", "message": "Session not found"}
            return

        # ── Step 1: Extract data ──────────────────────────────────────────
        fd = session.get("financial_data", {})
        docs = session.get("documents", {})
        extracted = extract_forensic_data(fd, docs)
        meta = extracted.get("_meta", {})

        # Save extracted data
        self.store.set_forensic_extracted(self.session_id, extracted)
        self.store.set_forensic_state(self.session_id, "running")

        completeness = meta.get("data_completeness_pct", 0)
        present = meta.get("present_count", 0)
        total = meta.get("total_required", 0)
        missing_count = meta.get("missing_count", 0)

        yield {
            "type": "info",
            "message": (
                f"📊 Forensic data extraction complete — "
                f"Data Completeness: {completeness}% ({present}/{total} fields, {missing_count} missing)\n"
                f"Starting 30-checkpoint audit"
            ),
        }

        # Log missing fields
        missing_fields = meta.get("missing_fields", [])
        if missing_fields:
            logger.warning(f"[{self.session_id}] Missing fields ({missing_count}): {', '.join(missing_fields[:20])}")

        # ── Step 2: Run checkpoints sequentially ─────────────────────────
        results = []
        total_score = 0
        vetoed = False
        veto_checkpoint = None

        for cp in CHECKPOINTS:
            # Small delay for live-streaming effect
            await asyncio.sleep(0.15)

            r = evaluate_checkpoint(cp, extracted)
            results.append(r)
            total_score += r["score_points"]

            # Build the reasoning trace message
            data_flag = " [DATA MISSING]" if r.get("data_missing") else ""
            trace_msg = (
                f"[CHECKPOINT {r['id']:02d}]: {r['name']} | "
                f"Calculated: {r['result_label']} | "
                f"Status: {r['score_tier']}{data_flag}"
            )

            yield {
                "type": "checkpoint",
                "checkpoint_id": r["id"],
                "checkpoint_name": r["name"],
                "category": r["cat"],
                "formula": r["formula"],
                "result_value": r["result_value"],
                "result_label": r["result_label"],
                "score_tier": r["score_tier"],
                "score_points": r["score_points"],
                "is_veto": r["is_veto"],
                "data_missing": r.get("data_missing", False),
                "progress": round(r["id"] / 30 * 100, 1),
                "message": trace_msg,
            }

            # ── Hard Veto check ───────────────────────────────────────────
            if r["is_veto"]:
                vetoed = True
                veto_checkpoint = r
                self.store.set_forensic_state(self.session_id, "rejected")

                yield {
                    "type": "veto",
                    "checkpoint_id": r["id"],
                    "checkpoint_name": r["name"],
                    "result_label": r["result_label"],
                    "message": (
                        f"⚠ HARD VETO: Potential Fraud / Default Detected — "
                        f"Checkpoint {r['id']} ({r['name']}) scored {r['score_tier']}"
                    ),
                }
                break  # ← STOP processing on hard veto

        # ── Save results ──────────────────────────────────────────────────
        risk_grade = "Reject" if vetoed else compute_risk_grade(total_score)

        self.store.set_forensic_scores(self.session_id, {
            "results": results,
            "aggregate_score": total_score,
            "risk_grade": risk_grade,
            "vetoed": vetoed,
            "veto_checkpoint": veto_checkpoint,
            "data_completeness": meta,
        })

        state = "rejected" if vetoed else "completed"
        self.store.set_forensic_state(self.session_id, state)

        # Count data-missing checkpoints
        data_missing_count = sum(1 for r in results if r.get("data_missing"))

        yield {
            "type": "complete",
            "aggregate_score": total_score,
            "max_score": 300,
            "risk_grade": risk_grade,
            "vetoed": vetoed,
            "checkpoints_completed": len(results),
            "data_completeness_pct": completeness,
            "data_missing_checkpoints": data_missing_count,
            "message": (
                f"✅ Forensic audit {'VETOED' if vetoed else 'complete'}: "
                f"{total_score}/300 — {risk_grade} | "
                f"Data: {completeness}% complete, {data_missing_count} checkpoints had missing data"
            ),
        }
