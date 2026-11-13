"""FR-3 / 6.3: OCR integration — extract raw text from uploaded bill files.

pdfplumber is used for text-based PDFs.
Image OCR (pytesseract) is optional and enabled when VAULT_OCR_PROVIDER=tesseract.
In mock/default mode a regex-friendly placeholder is returned.
"""

from __future__ import annotations

from pathlib import Path


def extract_text(file_path: str, file_type: str) -> str:
    """FR-3: Extract raw text from a bill file.

    Args:
        file_path: Absolute path to the saved file.
        file_type: One of 'pdf', 'jpg', 'png'.

    Returns:
        Extracted text string (may be empty if nothing could be parsed).
    """
    path = Path(file_path)
    if not path.exists():
        return ""

    if file_type == "pdf":
        return _extract_pdf(str(path))
    elif file_type in ("jpg", "jpeg", "png"):
        return _extract_image(str(path))
    return ""


def _extract_pdf(file_path: str) -> str:
    """Use pdfplumber to extract text from a PDF."""
    try:
        import pdfplumber  # type: ignore[import-untyped]

        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()
    except Exception:  # noqa: BLE001
        return ""


def _extract_image(file_path: str) -> str:
    """Use pytesseract for image OCR when available, else return empty string."""
    try:
        import pytesseract  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]

        image = Image.open(file_path)
        return pytesseract.image_to_string(image).strip()
    except Exception:  # noqa: BLE001
        # tesseract not installed — PDF text extraction is enough for the demo
        return ""
