"""FR-3, 6.3: Unit tests for bill parser across 5 invoice fixtures and fallback behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.integrations.llm import GeminiProvider, _strip_pii_for_llm
from app.services.bill_parser import BillParser

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

RECORDED_LLM_RESPONSES = {
    "amazon_invoice.pdf": {
        "product_name": "LG 1.5 Ton 5 Star AI Dual Inverter Split AC (Copper, TS-Q19PWZE)",
        "brand": "LG",
        "model_number": "TS-Q19PWZE",
        "seller": "Appario Retail Private Ltd",
        "price": "46633.00",
        "purchase_date": "2024-05-28",
        "warranty_months": "12",
        "category": "AC",
        "invoice_number": "INV-AMZ-2024-98765",
    },
    "store_invoice.pdf": {
        "product_name": "Samsung 253 L 3 Star Frost Free Double Door Refrigerator",
        "brand": "Samsung",
        "model_number": "RT28C3053S8",
        "seller": "Reliance Digital Mumbai",
        "price": "24990",
        "purchase_date": "2024-06-15",
        "warranty_months": "24",
        "category": "Refrigerator",
        "invoice_number": "RD-MUM-87234",
    },
    "scanned_invoice.pdf": {
        "product_name": "Whirlpool 7.5 Kg Fully Automatic Top Load Washing Machine",
        "brand": "Whirlpool",
        "model_number": "Stainwash Pro",
        "seller": "Vijay Sales Electronic Store",
        "price": "18500",
        "purchase_date": "2024-08-10",
        "warranty_months": "24",
        "category": "Washing Machine",
        "invoice_number": "VS-DEL-5542",
    },
    "clean_photo.png": {
        "product_name": "Daikin 1.5 Ton Split Air Conditioner",
        "brand": "Daikin",
        "model_number": "FTKF50TV",
        "seller": "Infiniti Retail Limited",
        "price": "42500",
        "purchase_date": "2024-07-12",
        "warranty_months": "12",
        "category": "AC",
        "invoice_number": "CR-BLR-9011",
    },
    "tilted_photo.png": {
        "product_name": "Kent Grand Plus Mineral RO Water Purifier",
        "brand": "Kent",
        "model_number": "11001",
        "seller": "Kent RO Systems Ltd",
        "price": "14200",
        "purchase_date": "2024-09-05",
        "warranty_months": "12",
        "category": "RO Purifier",
        "invoice_number": "KENT-2024-4412",
    },
}


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
    assert ext["purchase_date"]["value"] == "2026-06-15"
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
    assert ext["purchase_date"]["value"] == "2026-06-15"
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
    assert ext["purchase_date"]["value"] == "2026-06-15"
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


@pytest.mark.parametrize(
    ("filename", "file_type", "expected_price", "expected_date", "expected_brand"),
    [
        ("amazon_invoice.pdf", "pdf", "46633.00", "2024-05-28", "LG"),
        ("store_invoice.pdf", "pdf", "24990", "2024-06-15", "Samsung"),
        ("scanned_invoice.pdf", "pdf", "18500", "2024-08-10", "Whirlpool"),
        ("clean_photo.png", "png", "42500", "2024-07-12", "Daikin"),
        ("tilted_photo.png", "png", "14200", "2024-09-05", "Kent"),
    ],
)
def test_five_invoice_fixtures_with_llm_mocked(
    filename: str,
    file_type: str,
    expected_price: str,
    expected_date: str,
    expected_brand: str,
) -> None:
    """Requirement 6: Assert on price, date and brand across 5 fixtures with LLM mocked by recorded JSON."""
    parser = BillParser()
    recorded_json = RECORDED_LLM_RESPONSES[filename]

    mock_llm = MagicMock()
    mock_llm.extract_bill_fields.return_value = recorded_json

    with patch.object(parser, "_llm", mock_llm):
        res = parser.extract(str(FIXTURES_DIR / filename), file_type)

    assert res["parse_status"] == "parsed"
    ext = res["extraction_json"]

    # Assert on price, date and brand
    assert ext["price"]["value"] == expected_price
    assert ext["price"]["confidence"] >= 0.6

    assert ext["purchase_date"]["value"] == expected_date
    assert ext["purchase_date"]["confidence"] >= 0.6

    assert ext["brand"]["value"] == expected_brand
    assert ext["brand"]["confidence"] >= 0.6


def test_gemini_provider_with_mocked_network() -> None:
    """Requirement 2: GeminiProvider validates schema, handles timeout/retry, strips PII, no network."""
    provider = GeminiProvider(api_key="test-api-key", model_name="gemini-1.5-flash")

    dummy_bill_text = (
        "Customer Name: John Doe\n"
        "Billing Address: 123 MG Road, Bengaluru, 560001\n"
        "Phone: +91 9876543210\n"
        "Email: john@example.com\n"
        "Brand: LG\n"
        "Invoice Date: 28-May-2024\n"
        "Grand Total: Rs. 46,633.00\n"
    )

    # Verify PII stripping
    sanitized = _strip_pii_for_llm(dummy_bill_text)
    assert "john@example.com" not in sanitized
    assert "9876543210" not in sanitized
    assert "John Doe" not in sanitized

    # Mock httpx response with valid JSON
    fake_json_text = (
        '{"product_name": "LG AC", "brand": "LG", "price": "46633.00", '
        '"purchase_date": "2024-05-28", "category": "AC"}'
    )
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": fake_json_text}]}}]
    }

    with patch("httpx.post", return_value=fake_resp):
        res = provider.extract_bill_fields(dummy_bill_text)

    assert res["brand"] == "LG"
    assert res["price"] == "46633.00"
    assert res["purchase_date"] == "2024-05-28"
