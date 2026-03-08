"""
Structured Document Agent — OCR + LLM extraction for financial documents.
Handles Balance Sheet, P&L, Cash Flow, GST returns, ITR, Form 26AS, Bank Statement.
"""
import asyncio, json, re
from typing import AsyncGenerator
from core.llm_client import PRIMARY_MODEL, chat_completion, OllamaResponseError
from core.ocr import extract_text_from_pdf, extract_financial_values, score_confidence
from core.doc_router import is_structured, get_doc_label
from models.database import SessionStore

FINANCIAL_KEYS = [
    "revenue","net_profit","ebitda","total_assets","total_liabilities",
    "equity","debt","cash","bank_balance","operating_cash_flow",
    "current_assets","current_liabilities","interest_expense","depreciation",
    "gstr1_sales","gstr3b_sales","gstr3b_tax_paid","gstr2a_itc_available",
    "form26as_tds","mab","monthly_credits","itr_profit",
]

class StructuredDocAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store
        self._extracted: dict = {}

    async def run_ocr(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return
        docs = session.get("documents", {})
        structured = {k: v for k, v in docs.items() if is_structured(k)}
        if not structured:
            yield "⚠ No structured documents found"; return

        yield f"📄 Processing {len(structured)} structured documents...\n"
        for doc_type, doc_info in structured.items():
            label = get_doc_label(doc_type)
            yield f"\n🔍 OCR: {label}..."
            path = doc_info.get("path", "")
            text = doc_info.get("text", "")
            if not text and path:
                try:
                    result = extract_text_from_pdf(path)
                    text = result["text"]
                    doc_info["text"] = text
                    doc_info["pages"] = result.get("pages", 0)
                except Exception as e:
                    yield f"  ⚠ OCR failed for {label}: {e}"
                    continue
            if not text:
                yield f"  ⚠ No text extracted from {label}"
                continue

            yield f"  ✓ Extracted {len(text)} chars from {label}"
            # Regex extraction
            regex_vals = extract_financial_values(text)
            yield f"  📊 Regex found {len(regex_vals)} values"

            # LLM extraction
            try:
                llm_vals = await _extract_values_with_ollama(doc_type, text[:4000])
                yield f"  🤖 LLM extracted {len(llm_vals)} values"
                merged = _merge_values(regex_vals, llm_vals)
            except Exception:
                merged = regex_vals

            normalized = _normalize_doc_values(doc_type, merged)
            for k, v in normalized.items():
                if v and v != 0:
                    self._extracted[k] = v
                    conf = score_confidence(v, "regex" if k in regex_vals else "llm")
                    yield f"  → {k}: ₹{v:,.0f} [{conf}]"

        self.store.set_financial_data(self.session_id, self._extracted)
        yield f"\n✅ Structured extraction complete. {len(self._extracted)} fields extracted."

    async def run_structuring(self) -> AsyncGenerator[str, None]:
        yield "📋 Structuring extracted data..."
        yield json.dumps(self._extracted, indent=2, default=str)
        yield "✅ Data structured."

async def _extract_values_with_ollama(doc_type: str, text: str) -> dict:
    prompt = f"""You are analyzing an Indian corporate {get_doc_label(doc_type)}.
Extract these financial values as a JSON object. Use Indian numbering (Lakhs/Crores).
Keys: {', '.join(FINANCIAL_KEYS)}
Return ONLY a JSON object. If a value is not found, omit the key. Never invent values.

Document text:
{text}"""
    try:
        raw = await chat_completion(prompt)
        return _extract_json_object(raw)
    except (OllamaResponseError, Exception):
        return {}

def _extract_json_object(raw: str) -> dict:
    patterns = [r'\{[^{}]*\}', r'```json\s*(\{[^`]*\})\s*```']
    for p in patterns:
        match = re.search(p, raw, re.DOTALL)
        if match:
            try: return json.loads(match.group(1) if '```' in p else match.group(0))
            except json.JSONDecodeError: continue
    return {}

def _merge_values(regex_values: dict, llm_values: dict) -> dict:
    merged = dict(regex_values)
    for k, v in llm_values.items():
        if k not in merged and v:
            merged[k] = v
    return merged

def _normalize_doc_values(doc_type: str, values: dict) -> dict:
    mapping = {
        "gstr_1": {"sales": "gstr1_sales","total": "gstr1_sales"},
        "gstr_3b": {"sales": "gstr3b_sales","tax_paid": "gstr3b_tax_paid","taxable": "gstr3b_sales"},
        "gstr_2a": {"itc": "gstr2a_itc_available","input_tax": "gstr2a_itc_available"},
        "form_26as": {"tds": "form26as_tds","total": "form26as_tds"},
    }
    doc_map = mapping.get(doc_type, {})
    normalized = {}
    for k, v in values.items():
        new_key = doc_map.get(k, k)
        if new_key in FINANCIAL_KEYS:
            try: normalized[new_key] = float(v) if v else 0
            except (ValueError, TypeError): pass
    return normalized
