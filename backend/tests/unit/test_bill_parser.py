"""FR-3, 6.3: Unit tests for bill parser (text PDF, scanned PDF, clean PNG, missing-tesseract fallback)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from app.services.bill_parser import BillParser

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_text_pdf_extraction() -> None:
    """FR-3, 6.3: Text PDF extracted via pdfplumber with 0.9 confidence."""
    parser = BillParser()
    file_path = str(FIXTURES_DIR / "sample_bill.pdf")
    res = parser.extract(file_path, "pdf")

    assert res["parse_status"] == "parsed"
    ext = res["extraction_json"]
    assert ext["product_name"]["value"] == "Samsung AC 1.5 Ton"
    assert ext["product_name"]["confidence"] == 0.9
    assert ext["brand"]["value"] == "Samsung"
    assert ext["model_number"]["value"] == "AR18BYNYBWK"
    assert ext["price"]["value"] == "42500"
    assert ext["purchase_date"]["value"] == "15/06/2026"
    assert ext["warranty_months"]["value"] == "12"


def test_scanned_pdf_extraction() -> None:
    """FR-3, 6.3: Scanned PDF falls back to OCR with lowered confidence (0.8)."""
    parser = BillParser()
    file_path = str(FIXTURES_DIR / "scanned_bill.pdf")
    res = parser.extract(file_path, "pdf")

    assert res["parse_status"] == "parsed"
    ext = res["extraction_json"]
    assert ext["product_name"]["value"] == "Samsung AC 1.5 Ton"
    assert ext["product_name"]["confidence"] == 0.8
    assert ext["model_number"]["value"] == "AR18BYNYBWK"
    assert ext["price"]["value"] == "42500"
    assert ext["purchase_date"]["value"] == "15/06/2026"
    assert ext["warranty_months"]["value"] == "12"


def test_clean_png_extraction() -> None:
    """FR-3, 6.3: Clean PNG bill extracted via OCR with preprocessing and lowered confidence (0.8)."""
    parser = BillParser()
    file_path = str(FIXTURES_DIR / "clean_bill.png")
    res = parser.extract(file_path, "png")

    assert res["parse_status"] == "parsed"
    ext = res["extraction_json"]
    assert ext["product_name"]["value"] == "Samsung AC 1.5 Ton"
    assert ext["product_name"]["confidence"] == 0.8
    assert ext["brand"]["value"] == "Samsung"
    assert ext["model_number"]["value"] == "AR18BYNYBWK"
    assert ext["price"]["value"] == "42500"
    assert ext["purchase_date"]["value"] == "15/06/2026"
    assert ext["warranty_months"]["value"] == "12"


def test_missing_tesseract_fallback() -> None:
    """FR-3: If tesseract binary is missing, return clear error and manual-entry form, never crash."""
    parser = BillParser()
    file_path = str(FIXTURES_DIR / "clean_bill.png")
    with patch("shutil.which", return_value=None):
        res = parser.extract(file_path, "png")

    assert res["parse_status"] == "needs_review"
    assert "error" in res
    assert "Tesseract" in res["error"]
    ext = res["extraction_json"]
    assert ext["product_name"]["value"] is None
    assert ext["product_name"]["confidence"] == 0.0
    assert ext["price"]["confidence"] == 0.0
    assert ext["purchase_date"]["confidence"] == 0.0
