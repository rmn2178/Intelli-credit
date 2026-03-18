# 🏦 Intelli-Credit — AI-Powered Credit Decisioning Engine

> **Bank-grade credit intelligence. Automated. Auditable. Agentic.**

---

## 💡 Core Idea

**Intelli-Credit** is an autonomous, multi-agent AI system that transforms the way banks and NBFCs evaluate loan applications. It ingests raw financial documents — balance sheets, GST returns, ITRs, bank statements — and produces a fully reasoned, evidence-cited Credit Appraisal Memorandum (CAM) with fraud screening, regulatory compliance checks, and a simulated stress test, all without human intervention until the final decision gate.

---

## ⚠️ The Problem

Credit underwriting in India is **slow, inconsistent, and dangerously manual**.

A typical SME loan application sits on a credit analyst's desk for **10–21 working days**. The analyst manually extracts numbers from PDFs, builds ratios in spreadsheets, cross-checks GST filings against P&L statements, and writes a CAM from scratch — every single time. The process is:

- **Opaque** — decisions rely on analyst intuition with little documented reasoning
- **Inconsistent** — two analysts evaluating the same file often reach different conclusions
- **Slow** — multi-week turnarounds kill SME cash flow and borrower trust
- **Fraud-blind** — manual review misses sophisticated document manipulation and GST mismatches
- **Non-compliant by default** — RBI and Basel III ratio checks are often done informally or skipped

---

## 🔥 Effects of the Problem

| Impact Area | Real-World Effect |
|---|---|
| **SMEs** | Loan rejections due to poor documentation, not poor creditworthiness |
| **Banks** | NPA risk from approving loans based on fabricated financials |
| **Analysts** | Burnout from repetitive, low-value extraction tasks |
| **Regulators** | Audit trails are weak; CAMs rarely cite their evidence sources |
| **Economy** | Credit gap for India's 63 million MSMEs exceeds ₹25 lakh crore |

---

## ✅ The Solution

Intelli-Credit deploys a **pipeline of specialized AI agents**, each owning a distinct slice of the underwriting workflow:

1. **Document Routing Agent** — classifies uploaded files (structured PDFs, scanned images, unstructured text) and routes them to the right parser
2. **OCR Engine** — extracts text from scanned documents with layout awareness
3. **Financial Agent** — parses balance sheets and P&L statements into structured financial data
4. **GST Agent** — reconciles GSTR-1 vs P&L, GSTR-2A vs GSTR-3B, flagging turnover mismatches
5. **Fraud Radar Agent** — runs OSINT collection, cross-references registry data (CIN/GSTIN), and scores fraud probability
6. **Forensic Audit Agent** — detects document tampering, round-tripping, and anomalies using a causal reasoning engine
7. **Verification Agent** — validates all evidence items, classifying them as Green / Yellow / Red
8. **CAM Agent** — generates a bank-grade Credit Appraisal Memorandum with formula citations and source references
9. **Committee Agent** — runs a three-persona AI debate (Risk Officer, Compliance Officer, Business Officer) to simulate credit committee review
10. **Regulatory Engine** — checks RBI exposure norms, DSCR thresholds, and Basel III capital ratio compliance
11. **Simulation Engine** — stress-tests the borrower across worst-case revenue, rate, and expense scenarios

The result: a complete, auditable credit decision — in **minutes, not weeks**.

---

## 🆚 Existing Solutions vs. Intelli-Credit Innovations

| Dimension | Existing Tools | Intelli-Credit |
|---|---|---|
| **CAM Generation** | Analyst writes manually in Word | AI generates structured CAM with `[Source: Doc, Section]` and `[Logic: Formula]` citations |
| **Fraud Detection** | Rule-based flag lists | Multi-signal fraud radar: OSINT + GST reconciliation + forensic document analysis + causal engine |
| **Credit Committee** | Human meeting, unrecorded debate | Autonomous 3-persona AI committee with full transcript |
| **Stress Testing** | Static sensitivity table | Monte Carlo-style simulation across revenue, rate, and cost shock scenarios |
| **Regulatory Checks** | Post-approval compliance review | Real-time RBI/Basel III compliance enforced during underwriting |
| **Evidence Auditability** | Analyst notes in margin | Every claim tagged Green/Yellow/Red with traceable evidence trail |
| **Document Handling** | Analyst reads PDFs manually | Automated routing: OCR for scans, structured parser for digitals, LLM for unstructured text |
| **SMT Validation** | None | Satisfiability Modulo Theory validator cross-checks financial logical consistency |
| **Knowledge Graph** | None | Entity relationship graph links company, directors, GST, and registry data |
| **Federated Privacy** | Centralized sensitive data | Federated learning stub isolates sensitive borrower data per institution |

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.11+ |
| **API Framework** | FastAPI |
| **Agent Orchestration** | Custom async multi-agent pipeline (`asyncio`, `AsyncGenerator`) |
| **LLM Provider** | Ollama (local) — `llama3.2`, `lfm2.5-thinking`; optional OpenAI / Anthropic / Google APIs |
| **OCR** | Custom OCR engine (`core/ocr.py`) |
| **Knowledge Graph** | `core/knowledge_graph.py` — entity relationship mapping |
| **Causal Reasoning** | `core/causal_engine.py` — anomaly and causation detection |
| **SMT Validation** | `core/smt_validator.py` — logical consistency verification |
| **OSINT Collection** | `core/osint_collector.py` + `core/web_search.py` |
| **Regulatory Engine** | `core/regulatory_engine.py` — RBI / Basel III checks |
| **Forensic Engine** | `core/forensic_engine.py` — document integrity analysis |
| **Session Store** | `models/database.py` — in-memory session management |
| **Data Schemas** | Pydantic (`models/schemas.py`) |
| **Testing** | Pytest |

### Frontend

| Layer | Technology |
|---|---|
| **Framework** | Next.js 14 (App Router) |
| **Language** | TypeScript |
| **Styling** | Tailwind CSS + custom global CSS design system |
| **UI Pages** | Upload → Processing → Intelligence → Results → Regulatory → Simulator |
| **Fonts** | Inter, Public Sans (body) · JetBrains Mono (data/code) |

### Infrastructure & Config

| Layer | Technology |
|---|---|
| **Environment** | `.env` with `OLLAMA_BASE_URL`, optional cloud API keys |
| **API Bridge** | `NEXT_PUBLIC_API_URL` connects Next.js frontend to FastAPI backend |
| **Package Management** | `pip` (backend) · `npm` (frontend) |

---

## 🗂️ Project Structure

```
./
├── backend/
│   ├── agents/          # Specialized AI agents (CAM, GST, Fraud, Committee, etc.)
│   ├── core/            # Engines: OCR, LLM client, Forensic, Regulatory, OSINT, Knowledge Graph
│   ├── models/          # Database session store and Pydantic schemas
│   ├── tests/           # Pytest test suite
│   ├── main.py          # FastAPI application entry point
│   └── requirements.txt
└── frontend/
    ├── app/             # Next.js App Router pages
    │   ├── upload/      # Document upload
    │   ├── processing/  # Live agent processing stream
    │   ├── intelligence/# Analysis results
    │   ├── results/     # CAM output
    │   ├── regulatory/  # Compliance dashboard
    │   └── simulator/   # Stress test simulator
    ├── styles/          # Global CSS design system
    └── next.config.js
```

---

## 🚀 Quick Start

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Start Ollama and pull models
ollama pull llama3.2:latest

# 3. Run backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 4. Run frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — upload your financial documents and let the agents work.

---

*Built for Indian banking. Designed to RBI standards. Evidence-first by default.*
