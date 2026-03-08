"""
LLM client wrapper — Ollama-first with provider abstraction.
Configured for Indian Corporate Credit Intelligence with strict citation protocol.
"""

import json
import os
from typing import AsyncGenerator

import httpx

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
PRIMARY_MODEL = os.getenv("OLLAMA_PRIMARY_MODEL", "llama3.2:latest")
SECONDARY_MODEL = os.getenv("OLLAMA_SECONDARY_MODEL", "mixtral")

SYSTEM_PROMPT = """You are the AI brain of Intelli-Credit, an Autonomous Corporate Credit Intelligence Operating System designed for the Indian banking ecosystem.

STRICT RULES — FOLLOW THESE EXACTLY:
1. Use ONLY the provided extracted data. NEVER invent or assume financial figures.
2. Never fabricate revenue, profit, debt, balance, or ratio numbers.
3. If data is missing, state exactly: "Data not available in submitted documents."
4. Interpret and classify only; do not generate synthetic values.
5. Flag inconsistencies with evidence and source references.
6. Keep responses concise, professional, and structured.

INDIAN CONTEXT MANDATES:
- Use Indian numbering: Lakhs (₹1,00,000) and Crores (₹1,00,00,000). NEVER use Millions/Billions.
- Apply Ind AS (Indian Accounting Standards) awareness for financial analysis.
- Reference RBI Master Directions, SEBI regulations, and CBIC guidelines where applicable.
- Understand Schedule III Balance Sheet format (Companies Act 2013).
- Know Indian tax structures: GST (CGST, SGST, IGST), TDS (Form 26AS), ITR-6.

CITATION PROTOCOL (MANDATORY):
- Every financial claim MUST cite: [Source: {Document_Name}, Page {X}, Section {Y}]
- Every formula MUST cite: [Logic: {Formula}]
- Every cross-verification MUST cite both sources being compared
- NEVER make a claim without a citation

FORENSIC EXTRACTION DIRECTIVES:
- For noisy scanned documents: ignore notary stamps, watermarks, handwritten margin notes
- For ambiguous values: report extraction confidence (HIGH/MEDIUM/LOW)
- For unreadable values: return null, never hallucinate
- Fuzzy match Indian abbreviations: Dep & Amort, PBT, PAT, Opex, Sundry Debtors/Creditors
"""


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama is not reachable."""


class OllamaResponseError(RuntimeError):
    """Raised when Ollama response payload is invalid."""


async def is_ollama_available() -> bool:
    """Check whether local Ollama server is available."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def ensure_ollama_available() -> None:
    """Ensure Ollama is up before starting model-dependent stages."""
    if not await is_ollama_available():
        raise OllamaUnavailableError(
            "Ollama is not running. Start it with `ollama serve`."
        )


async def chat_completion(
    prompt: str,
    model: str = PRIMARY_MODEL,
    system: str = SYSTEM_PROMPT,
) -> str:
    """Single-shot completion against Ollama."""
    await ensure_ollama_available()

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            chat_payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }
            resp = await client.post(f"{OLLAMA_BASE}/api/chat", json=chat_payload)
            if resp.status_code == 404:
                gen_payload = {
                    "model": model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                }
                gen = await client.post(
                    f"{OLLAMA_BASE}/api/generate", json=gen_payload
                )
                if gen.status_code == 404:
                    tags = await client.get(f"{OLLAMA_BASE}/api/tags")
                    tags.raise_for_status()
                    models = tags.json().get("models") or []
                    fallback = (models[0] or {}).get("name") if models else None
                    if not fallback:
                        gen.raise_for_status()
                    gen_payload["model"] = fallback
                    resp = await client.post(
                        f"{OLLAMA_BASE}/api/generate", json=gen_payload
                    )
                else:
                    resp = gen
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise OllamaResponseError(f"Ollama chat request failed: {exc}") from exc

    content = (
        (data.get("message", {}) or {}).get("content", "").strip()
        or data.get("response", "").strip()
    )
    if not content:
        raise OllamaResponseError("Ollama returned an empty chat response.")
    return content


async def stream_completion(
    prompt: str,
    model: str = PRIMARY_MODEL,
    system: str = SYSTEM_PROMPT,
) -> AsyncGenerator[str, None]:
    """Stream completion chunks from Ollama."""
    await ensure_ollama_available()

    try:
        async with httpx.AsyncClient(timeout=240.0) as client:
            chat_payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": True,
            }
            async with client.stream(
                "POST", f"{OLLAMA_BASE}/api/chat", json=chat_payload
            ) as resp:
                if resp.status_code == 404:
                    await resp.aclose()
                    gen_payload = {
                        "model": model,
                        "prompt": prompt,
                        "system": system,
                        "stream": True,
                    }
                    async with client.stream(
                        "POST", f"{OLLAMA_BASE}/api/generate", json=gen_payload
                    ) as gen_resp:
                        if gen_resp.status_code == 404:
                            await gen_resp.aclose()
                            tags = await client.get(f"{OLLAMA_BASE}/api/tags")
                            tags.raise_for_status()
                            models = tags.json().get("models") or []
                            fallback = (
                                (models[0] or {}).get("name") if models else None
                            )
                            if not fallback:
                                raise httpx.HTTPError("No available models in Ollama.")
                            gen_payload["model"] = fallback
                            async with client.stream(
                                "POST",
                                f"{OLLAMA_BASE}/api/generate",
                                json=gen_payload,
                            ) as gen2_resp:
                                gen2_resp.raise_for_status()
                                async for line in gen2_resp.aiter_lines():
                                    if not line or not line.strip():
                                        continue
                                    try:
                                        chunk = json.loads(line)
                                    except json.JSONDecodeError:
                                        continue
                                    text = chunk.get("response", "")
                                    if text:
                                        yield text
                                return
                        gen_resp.raise_for_status()
                        async for line in gen_resp.aiter_lines():
                            if not line or not line.strip():
                                continue
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            text = chunk.get("response", "")
                            if text:
                                yield text
                        return
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = (chunk.get("message", {}) or {}).get("content", "")
                    if text:
                        yield text
    except httpx.HTTPError as exc:
        raise OllamaResponseError(
            f"Ollama streaming request failed: {exc}"
        ) from exc
