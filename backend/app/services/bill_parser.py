"""FR-3, 6.3: Bill parser service — combines OCR + LLM extraction with confidence scoring.

Confidence per field (6.3):
  LLM and regex agree → 0.9 (0.8 for OCR)
  Only one source      → 0.6 (0.5 for OCR)
  Missing              → 0.0

parse_status (6.3):
  'parsed'       — product_name, price, purchase_date all ≥ 0.6
  'needs_review' — otherwise
"""

from __future__ import annotations

from typing import Any

from app.integrations.llm import (
    EXTRACTION_FIELDS,
    ExtractionResult,
    _regex_extract,
    get_llm_provider,
)
from app.integrations.ocr import TesseractNotFoundError, extract_text

REQUIRED_FIELDS = ("product_name", "price", "purchase_date")
CONFIDENCE_THRESHOLD = 0.6


def _normalise_value(value: Any) -> str | None:
    """Strip and lower for comparison (None → None)."""
    if value is None:
        return None
    s = str(value).strip().lower()
    return s if s else None


def _compute_confidence(llm_val: Any, regex_val: Any, is_ocr: bool = False) -> float:
    """6.3: Agree → 0.9; one source → 0.6; both missing → 0.0. Lower for OCR."""
    left = _normalise_value(llm_val)
    right = _normalise_value(regex_val)
    if left is None and right is None:
        return 0.0
    if left is not None and right is not None:
        # Treat as agree if one starts with the other or matches first 4 chars
        if left.startswith(right) or right.startswith(left) or left[:4] == right[:4]:
            return 0.8 if is_ocr else 0.9
        return 0.5 if is_ocr else 0.6
    return 0.5 if is_ocr else 0.6


def _build_extraction_json(
    llm_result: ExtractionResult, regex_result: ExtractionResult, is_ocr: bool = False
) -> dict[str, Any]:
    """Build the JSONB extraction_json: {field: {value, confidence}}."""
    fields = set(llm_result) | set(regex_result) | set(EXTRACTION_FIELDS)
    extraction: dict[str, Any] = {}
    for field in fields:
        llm_val = llm_result.get(field)
        regex_val = regex_result.get(field)
        confidence = _compute_confidence(llm_val, regex_val, is_ocr=is_ocr)
        # Prefer LLM value; fall back to regex
        value = llm_val if llm_val is not None else regex_val
        extraction[field] = {"value": value, "confidence": confidence}
    return extraction


def _determine_parse_status(extraction: dict[str, Any]) -> str:
    """6.3: 'parsed' if product_name, price, purchase_date all ≥ 0.6."""
    for field in REQUIRED_FIELDS:
        field_data = extraction.get(field, {})
        if isinstance(field_data, dict):
            conf = field_data.get("confidence", 0.0)
        else:
            conf = 0.0
        if conf < CONFIDENCE_THRESHOLD:
            return "needs_review"
    return "parsed"


class BillParser:
    """FR-3: Orchestrates OCR + LLM extraction with confidence scoring."""

    def __init__(self) -> None:
        self._llm = get_llm_provider()

    def extract(self, file_path: str, file_type: str) -> dict[str, Any]:
        """Extract fields from a bill file and return a structured result.

        Returns:
            {
              "raw_text": str,
              "extraction_json": {field: {value, confidence}},
              "parse_status": "parsed" | "needs_review",
              "error": str | None,
            }
        """
        try:
            raw_text, is_ocr = extract_text(file_path, file_type)
            error = None
        except TesseractNotFoundError as e:
            raw_text = ""
            is_ocr = True
            error = str(e)

        if error:
            empty_extraction = {
                field: {"value": None, "confidence": 0.0} for field in EXTRACTION_FIELDS
            }
            return {
                "raw_text": "",
                "extraction_json": empty_extraction,
                "parse_status": "needs_review",
                "error": error,
            }

        # Both sources
        llm_result: ExtractionResult = self._llm.extract_bill_fields(raw_text)
        regex_result: ExtractionResult = _regex_extract(raw_text)

        extraction = _build_extraction_json(llm_result, regex_result, is_ocr=is_ocr)
        parse_status = _determine_parse_status(extraction)

        return {
            "raw_text": raw_text,
            "extraction_json": extraction,
            "parse_status": parse_status,
        }
