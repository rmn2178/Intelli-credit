"""
Unstructured Document Agent — Processes qualitative/legal documents.
MOA, AOA, Annual Report, Business Plan, Board Resolution, etc.
"""
import json
from typing import AsyncGenerator
from core.llm_client import chat_completion, stream_completion
from core.ocr import extract_text_from_pdf
from core.doc_router import is_unstructured, get_doc_label
from models.database import SessionStore

class UnstructuredDocAgent:
    def __init__(self, session_id: str, store: SessionStore):
        self.session_id = session_id
        self.store = store

    async def run(self) -> AsyncGenerator[str, None]:
        session = self.store.get_session(self.session_id)
        if not session:
            yield "❌ Session not found"; return
        docs = session.get("documents", {})
        unstructured = {k: v for k, v in docs.items() if is_unstructured(k)}
        if not unstructured:
            yield "⚠ No unstructured documents found"; return

        yield f"📝 Processing {len(unstructured)} qualitative documents...\n"
        insights = {}
        for doc_type, doc_info in unstructured.items():
            label = get_doc_label(doc_type)
            yield f"\n📎 Analyzing: {label}..."
            text = doc_info.get("text", "")
            if not text and doc_info.get("path"):
                try:
                    result = extract_text_from_pdf(doc_info["path"])
                    text = result["text"]
                    doc_info["text"] = text
                except Exception as e:
                    yield f"  ⚠ Extraction failed: {e}"; continue

            if not text:
                yield f"  ⚠ No content for {label}"; continue

            prompt = f"""Analyze this Indian corporate document ({label}).
Extract key qualitative insights relevant to credit assessment:
- Promoter background and integrity indicators
- Related party transactions
- Audit qualifications or emphasis of matter
- Business model strengths/weaknesses
- Corporate governance red flags
- Legal compliance status
Every finding MUST cite [Source: {label}, relevant section].
Be concise. Return structured findings.

Document text (first 3000 chars):
{text[:3000]}"""
            try:
                analysis = await chat_completion(prompt)
                insights[doc_type] = analysis
                yield f"  ✓ {label} analyzed"
                yield f"  {analysis[:200]}..."
            except Exception as e:
                yield f"  ⚠ LLM analysis failed: {e}"

        session["unstructured_insights"] = insights
        yield f"\n✅ Qualitative analysis complete. {len(insights)} documents analyzed."
