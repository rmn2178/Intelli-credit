"""
Document Router — classifies files into 17+ Indian corporate document types.
Uses heuristic filename/content matching with LLM fallback.
"""

import re
from pathlib import Path

# ─── Document Type Registry ────────────────────────────────────────────────────

DOC_TYPES = {
    "balance_sheet": {
        "label": "Balance Sheet",
        "category": "financial",
        "patterns": ["balance.?sheet", "b/s", "bs_"],
    },
    "profit_loss": {
        "label": "Profit & Loss Statement",
        "category": "financial",
        "patterns": ["profit.?(?:and|&)?.?loss", "p&l", "p_l", "income.?statement"],
    },
    "cash_flow": {
        "label": "Cash Flow Statement",
        "category": "financial",
        "patterns": ["cash.?flow", "cf_statement"],
    },
    "gstr_1": {
        "label": "GSTR-1 (Sales Filings)",
        "category": "gst",
        "patterns": ["gstr.?1", "gst.?r1", "gst.?sales"],
    },
    "gstr_3b": {
        "label": "GSTR-3B (Tax Payment)",
        "category": "gst",
        "patterns": ["gstr.?3b", "gst.?r3b", "gst.?return"],
    },
    "gstr_2a": {
        "label": "GSTR-2A (Vendor Credit)",
        "category": "gst",
        "patterns": ["gstr.?2a", "gst.?r2a", "gst.?vendor", "gst.?input"],
    },
    "itr": {
        "label": "Income Tax Return",
        "category": "tax",
        "patterns": ["itr", "income.?tax.?return", "tax.?return"],
    },
    "form_26as": {
        "label": "Form 26AS",
        "category": "tax",
        "patterns": ["26as", "form.?26", "tds.?statement"],
    },
    "bank_statement": {
        "label": "12-Month Bank Statement",
        "category": "financial",
        "patterns": ["bank.?statement", "bank.?stmt", "account.?statement"],
    },
    "certificate_of_incorporation": {
        "label": "Certificate of Incorporation",
        "category": "legal",
        "patterns": ["incorporat", "coi", "certificate.?of.?inc"],
    },
    "moa": {
        "label": "Memorandum of Association",
        "category": "legal",
        "patterns": ["memorandum.?of.?assoc", "moa", "memo.?of.?assoc"],
    },
    "aoa": {
        "label": "Articles of Association",
        "category": "legal",
        "patterns": ["articles?.?of.?assoc", "aoa"],
    },
    "annual_report": {
        "label": "Annual Report",
        "category": "corporate",
        "patterns": ["annual.?report", "ar_fy", "yearly.?report"],
    },
    "business_plan": {
        "label": "Business Plan",
        "category": "corporate",
        "patterns": ["business.?plan", "biz.?plan", "b_plan"],
    },
    "board_resolution": {
        "label": "Board Resolution",
        "category": "legal",
        "patterns": ["board.?resolution", "board.?res", "resolution.?borrow"],
    },
    "shareholding_pattern": {
        "label": "Shareholding Pattern",
        "category": "corporate",
        "patterns": ["shareholding", "share.?pattern", "ownership.?pattern"],
    },
    "industry_report": {
        "label": "Industry Report",
        "category": "corporate",
        "patterns": ["industry.?report", "sector.?report", "market.?report"],
    },
    "legal_declaration": {
        "label": "Legal Compliance Declaration",
        "category": "legal",
        "patterns": [
            "legal.?(?:compliance)?.?declar",
            "compliance.?declar",
            "legal.?cert",
        ],
    },
}

STRUCTURED_TYPES = {
    "balance_sheet", "profit_loss", "cash_flow",
    "gstr_1", "gstr_3b", "gstr_2a",
    "itr", "form_26as", "bank_statement",
}

UNSTRUCTURED_TYPES = {
    "certificate_of_incorporation", "moa", "aoa",
    "annual_report", "business_plan", "board_resolution",
    "shareholding_pattern", "industry_report", "legal_declaration",
}


def classify_document(filename: str, text: str = "") -> str:
    """
    Classify a single document by filename heuristic, then content heuristic.
    Returns the doc_type key string.
    """
    name_lower = filename.lower()

    # Priority-ordered heuristic checks
    # Check GSTR-1 before generic GST
    # Check Board Resolution before Board Minutes
    # Check Legal Declaration before Legal Notice
    priority_order = [
        "gstr_1", "gstr_3b", "gstr_2a",
        "form_26as", "itr",
        "board_resolution", "legal_declaration",
        "balance_sheet", "profit_loss", "cash_flow",
        "bank_statement",
        "certificate_of_incorporation", "moa", "aoa",
        "annual_report", "business_plan",
        "shareholding_pattern", "industry_report",
    ]

    for doc_type in priority_order:
        info = DOC_TYPES[doc_type]
        for pattern in info["patterns"]:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return doc_type

    # Content-based heuristic
    if text:
        text_lower = text[:3000].lower()
        for doc_type in priority_order:
            info = DOC_TYPES[doc_type]
            for pattern in info["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return doc_type

    return "unknown"


def classify_documents(
    files: list[dict],
) -> list[dict]:
    """
    Classify a batch of documents.
    Each file dict should have 'filename' and optionally 'text'.
    Returns list of dicts with added 'doc_type' field.
    """
    results = []
    for f in files:
        doc_type = classify_document(
            f.get("filename", ""),
            f.get("text", ""),
        )
        results.append({**f, "doc_type": doc_type})
    return results


def is_structured(doc_type: str) -> bool:
    """Check if a document type is structured (financial/numeric)."""
    return doc_type in STRUCTURED_TYPES


def is_unstructured(doc_type: str) -> bool:
    """Check if a document type is unstructured (qualitative/legal)."""
    return doc_type in UNSTRUCTURED_TYPES


def get_doc_label(doc_type: str) -> str:
    """Get human-readable label for a document type."""
    return DOC_TYPES.get(doc_type, {}).get("label", doc_type)
