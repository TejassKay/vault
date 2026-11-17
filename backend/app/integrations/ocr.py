"""FR-3 / 6.3: OCR integration — extract raw text from uploaded bill files.

pdfplumber is used for text-based PDFs.
pytesseract with preprocessing is used for images and scanned PDFs.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

try:
    import pytesseract  # type: ignore[import-untyped]
except ImportError:
    pytesseract = None


class TesseractNotFoundError(Exception):
    """Raised when tesseract binary is not installed or available."""


def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for optimal Tesseract OCR.

    1. Convert to grayscale.
    2. Upscale if small.
    3. Light threshold.
    """
    gray = image.convert("L")
    w, h = gray.size
    if w < 1200 or h < 800:
        factor = max(2, int(1600 / max(w, h)))
        gray = gray.resize((w * factor, h * factor), Image.Resampling.LANCZOS)

    thresh = gray.point(lambda p: 255 if p > 160 else 0)
    return thresh


def ocr_image(image: Image.Image) -> str:
    """Run pytesseract on a PIL Image with preprocessing.

    Raises:
        TesseractNotFoundError: If tesseract binary is missing.
    """
    if pytesseract is None or not shutil.which("tesseract"):
        raise TesseractNotFoundError("Tesseract OCR binary is not installed on the system.")

    processed = preprocess_image(image)
    try:
        text = pytesseract.image_to_string(processed)
        return text.strip()
    except Exception as e:
        if "not installed or it's not in your PATH" in str(e) or isinstance(e, FileNotFoundError):
            raise TesseractNotFoundError(
                "Tesseract OCR binary is not installed on the system."
            ) from e
        return ""


def extract_text(file_path: str, file_type: str) -> tuple[str, bool]:
    """FR-3: Extract raw text from a bill file.

    Args:
        file_path: Absolute path to the saved file.
        file_type: One of 'pdf', 'jpg', 'jpeg', 'png'.

    Returns:
        tuple of (extracted_text, is_ocr)
    Raises:
        TesseractNotFoundError: If OCR was required but tesseract binary is missing.
    """
    path = Path(file_path)
    if not path.exists():
        return "", False

    if file_type == "pdf":
        return _extract_pdf(str(path))
    elif file_type in ("jpg", "jpeg", "png"):
        return _extract_image(str(path))
    return "", False


def _extract_pdf(file_path: str) -> tuple[str, bool]:
    """Use pdfplumber to extract text from a PDF; fall back to OCR if scanned."""
    try:
        import pdfplumber  # type: ignore[import-untyped]

        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages).strip()

            # If extracted text is nearly empty, render pages to images and OCR them
            if len(text) < 30:
                ocr_pages = []
                for page in pdf.pages:
                    page_img = page.to_image(resolution=300).original
                    page_text = ocr_image(page_img)
                    if page_text:
                        ocr_pages.append(page_text)
                return "\n".join(ocr_pages).strip(), True

            return text, False
    except TesseractNotFoundError:
        raise
    except Exception:
        return "", False


def _extract_image(file_path: str) -> tuple[str, bool]:
    """Use pytesseract with preprocessing for image OCR."""
    try:
        image = Image.open(file_path)
        return ocr_image(image), True
    except TesseractNotFoundError:
        raise
    except Exception:
        return "", True
