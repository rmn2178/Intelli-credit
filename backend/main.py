"""
Intelli-Credit Decisioning Engine — FastAPI Backend
Autonomous Corporate Credit Intelligence Operating System
"""
import uuid, asyncio, json
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from models.database import SessionStore
from models.schemas import LoanInitRequest, SimulationRequest, RegulatoryRegime
from agents.structured_doc_agent import StructuredDocAgent
from agents.unstructured_doc_agent import UnstructuredDocAgent
from agents.financial_agent import FinancialAgent
from agents.gst_agent import GSTAgent
from agents.verification_agent import VerificationAgent
from agents.fraud_radar_agent import FraudRadarAgent
from agents.cam_agent import CAMAgent
from agents.committee_agent import CommitteeAgent
from core.evidence_classifier import classify_evidence
from core.calculations import run_intermediate_calculations, compute_risk_score
from core.causal_engine import CausalEngine
from core.regulatory_engine import RegulatoryEngine
from core.doc_router import classify_document

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

session_store = SessionStore()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Intelli-Credit Decisioning Engine starting...")
    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="Intelli-Credit Decisioning Engine",
    description="Autonomous Corporate Credit Intelligence Operating System",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:3001"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Health & Root ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"name": "Intelli-Credit Decisioning Engine", "version": "2.0.0", "status": "operational", "components": ["Fraud Radar","Digital Twin","Credit Committee","CAM Generator","Regulatory Engine","Knowledge Graph"]}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ─── Session Management ───────────────────────────────────────────────────────

@app.post("/api/sessions")
async def initialize_session(request: LoanInitRequest):
    sid = session_store.create_session(
        company_name=request.company_name,
        cin=request.cin,
        gstin=request.gstin,
        loan_amount=request.loan_amount,
        loan_purpose=request.loan_purpose,
    )
    return {"session_id": sid, "status": "initialized", "company": request.company_name}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    s = session_store.get_session(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s

# ─── Document Upload ──────────────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/upload")
async def upload_documents(session_id: str, files: list[UploadFile] = File(...), doc_types: str = Form(...)):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    types_list = [t.strip() for t in doc_types.split(",")]
    uploaded = []
    for i, file in enumerate(files):
        doc_type = types_list[i] if i < len(types_list) else classify_document(file.filename or "unknown")
        save_path = UPLOAD_DIR / session_id / f"{doc_type}_{file.filename}"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        save_path.write_bytes(content)

        text = ""
        if file.filename and file.filename.lower().endswith(('.md', '.txt', '.csv')):
            text = content.decode("utf-8", errors="ignore")

        session_store.add_document(session_id, doc_type, file.filename or "unknown", str(save_path), text=text)
        uploaded.append({"filename": file.filename, "doc_type": doc_type, "size": len(content)})

    session_store.update_session(session_id, status="documents_uploaded")
    return {"uploaded": uploaded, "total": len(uploaded)}

# ─── Processing Stream (SSE) ─────────────────────────────────────────────────

@app.get("/api/sessions/{session_id}/process")
async def process_documents(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    async def event_stream():
        queue = asyncio.Queue()

        async def run_producer(generator, tag):
            try:
                async for msg in generator:
                    await queue.put(_sse(tag, {"message": msg}))
            except Exception as e:
                await queue.put(_sse(tag, {"message": f"❌ Error in {tag}: {e}"}))

        async def pipeline():
            # Stage 1: Structured Document Processing
            await queue.put(_sse("stage", {"stage": "ocr", "status": "running"}))
            agent = StructuredDocAgent(session_id, session_store)
            async for msg in agent.run_ocr():
                await queue.put(_sse("ocr", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "ocr", "status": "complete"}))

            # Stage 2: Unstructured Document Processing
            await queue.put(_sse("stage", {"stage": "unstructured", "status": "running"}))
            ua = UnstructuredDocAgent(session_id, session_store)
            async for msg in ua.run():
                await queue.put(_sse("unstructured", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "unstructured", "status": "complete"}))

            # Stage 3: Evidence Classification
            await queue.put(_sse("stage", {"stage": "evidence", "status": "running"}))
            s = session_store.get_session(session_id)
            fd = s.get("financial_data", {})
            dt = s.get("doc_types", [])
            evidence = classify_evidence(fd, dt)
            session_store.set_evidence(session_id, evidence)
            await queue.put(_sse("evidence", {"message": f"Evidence: {len(evidence['green'])} GREEN, {len(evidence['yellow'])} YELLOW, {len(evidence['red'])} RED"}))
            await queue.put(_sse("stage", {"stage": "evidence", "status": "complete"}))

            # Stage 4: Financial Analysis + Digital Twin
            await queue.put(_sse("stage", {"stage": "financial", "status": "running"}))
            fa = FinancialAgent(session_id, session_store)
            async for msg in fa.run():
                await queue.put(_sse("financial", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "financial", "status": "complete"}))

            # Stage 5: GST Reconciliation
            await queue.put(_sse("stage", {"stage": "gst", "status": "running"}))
            ga = GSTAgent(session_id, session_store)
            async for msg in ga.run():
                await queue.put(_sse("gst", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "gst", "status": "complete"}))

            # Stage 6: Fraud Radar
            await queue.put(_sse("stage", {"stage": "fraud", "status": "running"}))
            fr = FraudRadarAgent(session_id, session_store)
            async for msg in fr.run():
                await queue.put(_sse("fraud", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "fraud", "status": "complete"}))

            # Stage 7: External Verification + OSINT
            await queue.put(_sse("stage", {"stage": "osint", "status": "running"}))
            va = VerificationAgent(session_id, session_store)
            async for msg in va.run_verification():
                await queue.put(_sse("verification", {"message": msg}))
            async for msg in va.run_osint():
                await queue.put(_sse("osint", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "osint", "status": "complete"}))

            # Stage 8: CAM Generation
            await queue.put(_sse("stage", {"stage": "cam", "status": "running"}))
            ca = CAMAgent(session_id, session_store)
            async for msg in ca.run():
                await queue.put(_sse("cam", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "cam", "status": "complete"}))

            # Stage 9: Credit Committee
            await queue.put(_sse("stage", {"stage": "committee", "status": "running"}))
            cc = CommitteeAgent(session_id, session_store)
            async for msg in cc.run():
                await queue.put(_sse("committee", {"message": msg}))
            await queue.put(_sse("stage", {"stage": "committee", "status": "complete"}))

            # Final Decision
            s = session_store.get_session(session_id)
            debate = s.get("committee_debate", {})
            decision = {
                "borrower": s.get("company_name", ""),
                "risk_score": s.get("financial_data", {}).get("risk_score", 0),
                "decision": debate.get("final_decision", "Manual Review"),
                "fraud_score": s.get("fraud_report", {}).get("fraud_probability", 0),
                "confidence": 0.91,
            }
            session_store.set_credit_decision(session_id, decision)
            await queue.put(_sse("decision", decision))
            await queue.put(_sse("complete", {"status": "done"}))
            await queue.put(None)

        asyncio.create_task(pipeline())
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ─── Simulation API (Credit Flight Simulator) ────────────────────────────────

@app.post("/api/sessions/{session_id}/simulate")
async def run_simulation(session_id: str, request: SimulationRequest):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    fd = session.get("financial_data", {})
    engine = CausalEngine(fd)
    results = {"scenarios": []}

    if request.interest_rate_delta_bps:
        results["scenarios"].append(engine.simulate_interest_rate_shock(request.interest_rate_delta_bps))
    if request.revenue_change_pct:
        results["scenarios"].append(engine.simulate_revenue_shock(abs(request.revenue_change_pct)))
    if request.churn_rate_pct:
        results["scenarios"].append(engine.simulate_churn(request.churn_rate_pct))
    if request.top_customer_exit:
        results["scenarios"].append(engine.simulate_customer_concentration())
    if request.working_capital_days_delta:
        results["scenarios"].append(engine.simulate_working_capital_stress(request.working_capital_days_delta))

    if not results["scenarios"]:
        results = engine.run_comprehensive_simulation(request.model_dump())

    results["base_metrics"] = engine.base_metrics
    return results

# ─── Regulatory Time Machine ─────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/regulatory")
async def regulatory_check(session_id: str, regime: str = "RBI Framework 2024"):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    fd = session.get("financial_data", {})
    calcs = session.get("calculations", {})
    loan = session.get("loan_amount", 0)

    engine = RegulatoryEngine(regime)
    result = engine.check_compliance(loan, calcs, fd)
    return result

@app.get("/api/sessions/{session_id}/regulatory/compare")
async def regulatory_compare(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    fd = session.get("financial_data", {})
    calcs = session.get("calculations", {})
    loan = session.get("loan_amount", 0)

    engine = RegulatoryEngine()
    return engine.get_regime_comparison(loan, calcs, fd)

# ─── Results API ──────────────────────────────────────────────────────────────

@app.get("/api/sessions/{session_id}/results")
async def get_results(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "credit_decision": session.get("credit_decision", {}),
        "evidence": session.get("evidence", {}),
        "calculations": session.get("calculations", {}),
        "fraud_report": session.get("fraud_report", {}),
        "simulation_results": session.get("simulation_results", {}),
        "cam_report": session.get("cam_report", {}),
        "committee_debate": session.get("committee_debate", {}),
        "gst_report": session.get("gst_report", {}),
    }

@app.get("/api/sessions/{session_id}/cam")
async def get_cam(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.get("cam_report", {})

@app.get("/api/sessions/{session_id}/fraud")
async def get_fraud(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.get("fraud_report", {})

def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
