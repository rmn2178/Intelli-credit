"""
OCR & Document Processing Pipeline for Indian Financial Documents.
Includes Pan-and-Scan cropping, noise reduction, and confidence scoring.
"""

import re
import tempfile
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None


# ─── Indian Abbreviation Map ──────────────────────────────────────────────────

INDIAN_ABBREV_MAP = {
    "dep & amort": "depreciation_and_amortization",
    "dep and amort": "depreciation_and_amortization",
    "pbt": "profit_before_tax",
    "pat": "profit_after_tax",
    "opex": "operating_expenses",
    "sundry debtors": "trade_receivables",
    "sundry creditors": "trade_payables",
    "s. debtors": "trade_receivables",
    "s. creditors": "trade_payables",
    "p&l": "profit_and_loss",
    "b/s": "balance_sheet",
    "wc": "working_capital",
    "o/s": "outstanding",
    "adv.": "advance",
    "int.": "interest",
    "cap.": "capital",
    "res.": "reserves",
    "dept.": "department",
    "qty.": "quantity",
    "amt.": "amount",
    "cr.": "crore",
    "l.": "lakh",
    "lac": "lakh",
}


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extract text from a PDF file using pdfplumber.
    Returns dict with keys: text, pages, page_texts, tables.
    """
    result = {"text": "", "pages": 0, "page_texts": [], "tables": []}

    if pdfplumber is None:
        result["text"] = _read_as_text(pdf_path)
        return result

    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["pages"] = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                result["page_texts"].append(
                    {"page": i + 1, "text": page_text}
                )
                # Extract tables
                tables = page.extract_tables() or []
                for table in tables:
                    result["tables"].append(
                        {"page": i + 1, "data": table}
                    )
            result["text"] = "\n\n".join(
                pt["text"] for pt in result["page_texts"]
            )
    except Exception:
        result["text"] = _read_as_text(pdf_path)

    return result


def extract_text_from_image(image_path: str) -> str:
    """OCR extraction from image using Tesseract with Indian doc processing."""
    if pytesseract is None or Image is None:
        return ""
    try:
        img = Image.open(image_path)
        img = _preprocess_indian_doc(img)
        text = pytesseract.image_to_string(img, lang="eng")
        return _clean_ocr_text(text)
    except Exception:
        return ""


def pan_and_scan_extract(image_path: str, grid_size: int = 4) -> str:
    """
    Pan-and-Scan cropping algorithm for high-resolution Indian tax filings.
    Splits image into grid cells and OCRs each, then merges.
    """
    if Image is None or pytesseract is None:
        return extract_text_from_image(image_path)

    try:
        img = Image.open(image_path)
        width, height = img.size
        cell_w = width // grid_size
        cell_h = height // grid_size

        all_text = []
        for row in range(grid_size):
            row_texts = []
            for col in range(grid_size):
                box = (
                    col * cell_w,
                    row * cell_h,
                    min((col + 1) * cell_w, width),
                    min((row + 1) * cell_h, height),
                )
                cell = img.crop(box)
                cell = _preprocess_indian_doc(cell)
                text = pytesseract.image_to_string(cell, lang="eng")
                row_texts.append(text.strip())
            all_text.append(" | ".join(row_texts))

        return "\n".join(all_text)
    except Exception:
        return extract_text_from_image(image_path)


def extract_financial_values(text: str) -> dict[str, Optional[float]]:
    """
    Regex-based extraction of common Indian financial values from text.
    Returns dict of field_name -> numeric_value.
    """
    patterns = {
        "revenue": [
            r"(?:total\s+)?revenue[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
            r"turnover[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
            r"sales[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "net_profit": [
            r"(?:net\s+)?profit[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
            r"PAT[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "ebitda": [
            r"EBITDA[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "total_assets": [
            r"total\s+assets[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "total_liabilities": [
            r"total\s+liabilities[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "equity": [
            r"(?:shareholders?\s+)?equity[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "debt": [
            r"(?:total\s+)?(?:long.?term\s+)?debt[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
            r"borrowings?[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "interest_expense": [
            r"interest\s+(?:expense|paid|cost)[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "depreciation": [
            r"depreciation[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "current_assets": [
            r"current\s+assets[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "current_liabilities": [
            r"current\s+liabilities[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "operating_cash_flow": [
            r"(?:net\s+)?cash\s+(?:from|flow)[\s\w]*operat[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "gstr1_sales": [
            r"(?:GSTR.?1|gstr.?1)\s+.*?(?:total|sales)[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "gstr3b_sales": [
            r"(?:GSTR.?3B|gstr.?3b)\s+.*?(?:total|taxable)[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "gstr3b_tax_paid": [
            r"(?:GSTR.?3B|gstr.?3b)\s+.*?(?:tax\s+paid|igst|cgst)[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "gstr2a_itc_available": [
            r"(?:GSTR.?2A|gstr.?2a)\s+.*?(?:ITC|input\s+tax)[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
        "form26as_tds": [
            r"(?:26AS|form.?26)\s+.*?(?:TDS|total)[:\s]+[₹Rs.]*\s*([\d,]+\.?\d*)",
        ],
    }

    extracted = {}
    text_lower = text.lower()
    for field, regexes in patterns.items():
        for regex in regexes:
            match = re.search(regex, text_lower, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1).replace(",", ""))
                    extracted[field] = val
                    break
                except ValueError:
                    continue
    return extracted


def score_confidence(value: Optional[float], source: str) -> str:
    """Assign extraction confidence: HIGH / MEDIUM / LOW."""
    if value is None:
        return "LOW"
    if source in ("regex", "table"):
        return "HIGH"
    return "MEDIUM"


# ─── Internal Helpers ──────────────────────────────────────────────────────────

def _read_as_text(path: str) -> str:
    """Fallback: read file as raw text."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _preprocess_indian_doc(img):
    """Preprocess image for Indian financial OCR: grayscale + contrast."""
    try:
        img = img.convert("L")  # grayscale
        # Simple contrast enhancement
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
    except Exception:
        pass
    return img


def _clean_ocr_text(text: str) -> str:
    """Clean OCR output: remove noise, normalize Indian abbreviations."""
    # Remove common OCR artifacts
    text = re.sub(r"[|}{]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Apply abbreviation normalization info
    for abbrev, full in INDIAN_ABBREV_MAP.items():
        text = re.sub(
            re.escape(abbrev), full, text, flags=re.IGNORECASE
        )
    return text.strip()
