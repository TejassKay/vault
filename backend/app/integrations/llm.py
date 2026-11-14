"""FR-3, 6.3: LLM integration — extract structured data from bill text.

Providers:
  mock   — returns regex-extracted JSON; works with zero API keys (default)
  gemini — real Google Gemini API (requires GEMINI_API_KEY)
  openai — real OpenAI API (requires VAULT_OPENAI_API_KEY)
  claude — real Anthropic API (requires VAULT_ANTHROPIC_API_KEY)

Selected via VAULT_LLM_PROVIDER env var.

The LLM must never feed a calculation or a decision (7.2 hybrid AI rule).
It is called only to fill extraction fields; all numbers come from the engines.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Fields the LLM and rule-based extractor should return
EXTRACTION_FIELDS = [
    "product_name",
    "brand",
    "model_number",
    "seller",
    "price",
    "purchase_date",
    "warranty_months",
    "category",
    "invoice_number",
]

ExtractionResult = dict[str, Any]  # {field: value_or_None}

SEEDED_CATEGORIES = [
    "AC",
    "Refrigerator",
    "Washing Machine",
    "RO Purifier",
    "Geyser",
    "Chimney",
]

INDIAN_APPLIANCE_BRANDS = [
    "Samsung",
    "LG",
    "Whirlpool",
    "Daikin",
    "Voltas",
    "Godrej",
    "Haier",
    "Hitachi",
    "Blue Star",
    "Carrier",
    "Panasonic",
    "IFB",
    "Bosch",
    "Siemens",
    "Lloyd",
    "Kent",
    "Aquaguard",
    "Eureka Forbes",
    "Pureit",
    "Havells",
    "Bajaj",
    "Crompton",
    "AO Smith",
    "V-Guard",
    "Faber",
    "Glen",
    "Elica",
    "Hindware",
    "Sunflame",
    "Prestige",
    "Kaff",
    "Usha",
    "Morphy Richards",
    "Philips",
    "Mi",
    "Xiaomi",
    "TCL",
    "Onida",
    "BPL",
    "Livpure",
    "Symphony",
    "Kenstar",
]

CATEGORY_KEYWORD_MAP: dict[str, list[str]] = {
    "AC": [
        "air conditioner",
        "split ac",
        "window ac",
        "inverter ac",
        "dual inverter",
        r"\bac\b",
        "ton ac",
        "cassette ac",
    ],
    "Refrigerator": [
        "refrigerator",
        "fridge",
        "frost free",
        "single door",
        "double door",
        "side by side",
        "deep freezer",
    ],
    "Washing Machine": [
        "washing machine",
        "washer",
        "front load",
        "top load",
        "semi-automatic",
        "fully automatic",
        "washer dryer",
    ],
    "RO Purifier": [
        "water purifier",
        "ro purifier",
        "ro+uv",
        "ro+uf",
        "aquaguard",
        "pureit",
        "kent ro",
        r"\bro\b purifier",
        "water filter",
        "mineral ro",
    ],
    "Geyser": [
        "geyser",
        "water heater",
        "storage water heater",
        "instant water heater",
        "immersion rod",
    ],
    "Chimney": [
        "chimney",
        "kitchen hood",
        "auto clean chimney",
        "baffle filter chimney",
        "exhaust hood",
    ],
}


class LLMProvider(ABC):
    """Abstract provider interface."""

    @abstractmethod
    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        """Return a dict mapping each EXTRACTION_FIELDS key to its value or None."""

    def explain_recommendation(self, plan_item: dict[str, Any]) -> str | None:
        """Explain a validated plan item in plain language using only provided numbers."""
        return None


# ---------------------------------------------------------------------------
# Privacy helper: strip customer names and addresses before sending to LLM
# ---------------------------------------------------------------------------


def _strip_pii_for_llm(raw_text: str) -> str:
    """Never send customer names, addresses, phones or emails to LLM."""
    lines: list[str] = []
    skip_lines = 0
    for line in raw_text.splitlines():
        # Check for customer address headers to omit
        if re.search(
            r"(?:bill\s*to|ship\s*to|deliver\s*to|buyer|customer\s*name|billing\s*address|shipping\s*address)[:\s]",
            line,
            re.IGNORECASE,
        ):
            skip_lines = 2
            continue
        if skip_lines > 0:
            skip_lines -= 1
            continue

        # Redact emails and Indian phone numbers
        line = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL REDACTED]", line)
        line = re.sub(r"(?:\+91[\-\s]?)?[6-9]\d{9}", "[PHONE REDACTED]", line)
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rule-based fallback extractor
# ---------------------------------------------------------------------------


def _normalize_date_to_iso(date_str: str | None) -> str | None:
    """Convert various Indian invoice date formats to ISO YYYY-MM-DD."""
    if not date_str:
        return None
    cleaned = date_str.strip().rstrip(".,;")
    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d-%B-%Y",
        "%d %B %Y",
    ):
        try:
            return datetime.datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return cleaned


def _extract_brand(text: str) -> str | None:
    """Find brand from explicit label or dictionary of common Indian appliance brands."""
    m = re.search(r"(?:brand|make)[:\s]+([A-Za-z0-9 _\-]+)", text, re.IGNORECASE)
    if m:
        val = m.group(1).strip().rstrip(".,;")
        for b in INDIAN_APPLIANCE_BRANDS:
            if b.lower() == val.lower():
                return b
        if len(val) >= 2:
            return val

    # Dictionary lookup with word boundaries
    for b in INDIAN_APPLIANCE_BRANDS:
        if re.search(rf"\b{re.escape(b)}\b", text, re.IGNORECASE):
            return b
    return None


def _extract_category(text: str) -> str | None:
    """Map category to one of the 6 seeded categories using keyword map."""
    m = re.search(r"(?:category|type)[:\s]+([A-Za-z0-9 _\-]+)", text, re.IGNORECASE)
    if m:
        val = m.group(1).strip().rstrip(".,;")
        for cat in SEEDED_CATEGORIES:
            if cat.lower() == val.lower():
                return cat

    for cat, kw_list in CATEGORY_KEYWORD_MAP.items():
        for kw in kw_list:
            if re.search(rf"{kw}", text, re.IGNORECASE):
                return cat
    return None


def _extract_price(text: str) -> str | None:
    """Extract price near 'Grand Total', 'Net Amount', or 'Total', ignoring tax lines."""
    priorities = [
        r"(?:grand\s*total|total\s*payable|amount\s*payable|invoice\s*total)",
        r"(?:net\s*amount|total\s*amount)",
        r"(?:total[:\s.]*(?:rs\.?|inr|₹)?)",
        r"(?:price|mrp|amount)",
    ]
    for prio in priorities:
        for line in text.splitlines():
            line_clean = line.strip()
            # Ignore tax/discount/unit price lines unless matching Grand Total
            if prio != priorities[0] and re.search(
                r"tax|cgst|sgst|igst|gst|vat|subtotal|sub\s*total|unit\s*price|tax\s*amount",
                line_clean,
                re.IGNORECASE,
            ):
                continue
            if re.search(prio, line_clean, re.IGNORECASE):
                numbers = re.findall(
                    r"(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
                    line_clean,
                    re.IGNORECASE,
                )
                candidates: list[str] = []
                for n in numbers:
                    clean_n = n.replace(",", "").strip()
                    try:
                        val = float(clean_n)
                        if val > 10.0:  # exclude quantities, percentages, single digits
                            candidates.append(clean_n)
                    except ValueError:
                        pass
                if candidates:
                    return candidates[-1]
    return None


def _extract_warranty(text: str) -> str | None:
    """Extract warranty period and normalize to months string ('12', '24')."""
    m = re.search(
        r"(?:warranty(?:\s*period)?)[:\s.]*(\d+)\s*(months?|yrs?|years?)",
        text,
        re.IGNORECASE,
    )
    if m:
        num = m.group(1)
        unit = m.group(2).lower()
        if "yr" in unit or "year" in unit:
            try:
                return str(int(num) * 12)
            except ValueError:
                pass
        return str(int(num))

    # Pattern without label: '1 year warranty', '2 yrs warranty', '12 months warranty'
    m2 = re.search(
        r"(\d+)\s*(months?|yrs?|years?)\s+(?:comprehensive\s+)?warranty",
        text,
        re.IGNORECASE,
    )
    if m2:
        num = m2.group(1)
        unit = m2.group(2).lower()
        if "yr" in unit or "year" in unit:
            try:
                return str(int(num) * 12)
            except ValueError:
                pass
        return str(int(num))
    return None


def _regex_extract(text: str) -> ExtractionResult:
    """Apply rule-based regex and dictionary extraction to raw bill text."""
    result: ExtractionResult = {}

    # 1. Product Name
    p_match = re.search(
        r"(?:product(?:\s*name)?|item(?:\s*description)?|description)[:\s]+([A-Za-z0-9 _\-\.\(\)\/]+)",
        text,
        re.IGNORECASE,
    )
    if p_match:
        result["product_name"] = p_match.group(1).strip().rstrip(".,;")
    else:
        # Fallback: check lines containing brand and appliance keywords
        found_line: str | None = None
        for line in text.splitlines():
            line_s = line.strip()
            if any(b.lower() in line_s.lower() for b in INDIAN_APPLIANCE_BRANDS) and any(
                w in line_s.lower()
                for w in [
                    "ac",
                    "inverter",
                    "refrigerator",
                    "washing",
                    "purifier",
                    "geyser",
                    "chimney",
                ]
            ):
                found_line = line_s
                break
        result["product_name"] = found_line

    # 2. Brand
    result["brand"] = _extract_brand(text)

    # 3. Model Number
    m_match = re.search(
        r"(?:model\s*(?:no\.?|number|#)|item\s*model(?:\s*number)?|model)[:\s.]+([A-Za-z0-9 _\-\/]+)",
        text,
        re.IGNORECASE,
    )
    result["model_number"] = m_match.group(1).strip().rstrip(".,;") if m_match else None

    # 4. Seller
    s_match = re.search(
        r"(?:sold\s*by|seller|vendor|store|dealer)[:\s.]+([A-Za-z0-9 &.,\-]+)",
        text,
        re.IGNORECASE,
    )
    result["seller"] = s_match.group(1).strip().rstrip(".,;") if s_match else None

    # 5. Price
    result["price"] = _extract_price(text)

    # 6. Purchase Date
    d_match = re.search(
        r"(?:invoice\s*date|bill\s*date|date\s*of\s*invoice|purchase\s*date|date)[:\s.]+(\d{1,2}[/-](?:[A-Za-z]{3,9}|\d{1,2})[/-]\d{2,4}|\d{1,2}\s+(?:[A-Za-z]{3,9})\s+\d{2,4}|\d{4}-\d{2}-\d{2})",
        text,
        re.IGNORECASE,
    )
    result["purchase_date"] = _normalize_date_to_iso(d_match.group(1)) if d_match else None

    # 7. Warranty Months
    result["warranty_months"] = _extract_warranty(text)

    # 8. Category
    result["category"] = _extract_category(text)

    # 9. Invoice Number
    inv_match = re.search(
        r"(?:invoice\s*(?:no\.?|number|#)|bill\s*(?:no\.?|number|#)|invoice#)[:\s.]+([A-Za-z0-9\-\/]+)",
        text,
        re.IGNORECASE,
    )
    result["invoice_number"] = inv_match.group(1).strip().rstrip(".,;") if inv_match else None

    return result


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------


class MockProvider(LLMProvider):
    """FR-3 mock mode: rule-based regex extraction, zero API keys required."""

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        return _regex_extract(raw_text)


# ---------------------------------------------------------------------------
# Gemini Provider
# ---------------------------------------------------------------------------


class GeminiProvider(LLMProvider):
    """Google Gemini LLM extraction (requires GEMINI_API_KEY)."""

    def __init__(self, api_key: str, model_name: str | None = None) -> None:
        self._api_key = api_key
        self._model = model_name or os.environ.get("GEMINI_MODEL") or "gemini-1.5-flash"
        self._system_prompt = (
            "You are a structured bill extraction engine. Extract the following fields from the bill text as a valid JSON object:\n"
            "- product_name: string or null\n"
            "- brand: string or null\n"
            "- model_number: string or null\n"
            "- seller: string or null\n"
            "- price: string or number (total paid without currency symbols) or null\n"
            "- purchase_date: ISO date YYYY-MM-DD or null\n"
            "- warranty_months: integer number of months or null\n"
            '- category: one of ["AC", "Refrigerator", "Washing Machine", "RO Purifier", "Geyser", "Chimney"] or null\n'
            "- invoice_number: string or null\n"
            "Return ONLY JSON, no markdown, no explanation."
        )

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        sanitized_text = _strip_pii_for_llm(raw_text)

        # Temperature 0, validate JSON schema, 1 retry, short timeout
        for attempt in range(2):
            try:
                data = self._call_gemini(sanitized_text)
                if data and self._validate_schema(data):
                    # Clean and normalize fields
                    normalized: ExtractionResult = {}
                    for f in EXTRACTION_FIELDS:
                        val = data.get(f)
                        if val is not None and str(val).strip() != "":
                            if f == "purchase_date":
                                val = _normalize_date_to_iso(str(val))
                            elif f == "warranty_months":
                                val = str(val)
                            elif f == "price":
                                val = (
                                    str(val)
                                    .replace(",", "")
                                    .replace("₹", "")
                                    .replace("Rs.", "")
                                    .strip()
                                )
                            normalized[f] = val
                        else:
                            normalized[f] = None
                    return normalized
            except Exception as e:
                logger.warning("Gemini extraction attempt %d failed: %s", attempt + 1, e)

        # Fallback to rule-based extractor
        return _regex_extract(raw_text)

    def _call_gemini(self, text: str) -> dict[str, Any] | None:
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{self._system_prompt}\n\nInvoice Text:\n{text[:8000]}"}]}
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }
        resp = httpx.post(url, json=payload, timeout=8.0)
        if resp.status_code == 200:
            res_data = resp.json()
            candidates = res_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    raw_content = parts[0].get("text", "")
                    return json.loads(raw_content)
        return None

    def _validate_schema(self, data: dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        return any(k in data for k in EXTRACTION_FIELDS)


# ---------------------------------------------------------------------------
# OpenAI and Claude providers (stubs)
# ---------------------------------------------------------------------------


class OpenAIProvider(LLMProvider):
    """Real OpenAI extraction (requires VAULT_OPENAI_API_KEY)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        try:
            import openai  # type: ignore[import-untyped]

            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract the following fields from the bill text as JSON: "
                            + ", ".join(EXTRACTION_FIELDS)
                            + ". Return ONLY valid JSON."
                        ),
                    },
                    {"role": "user", "content": _strip_pii_for_llm(raw_text)[:8000]},
                ],
                temperature=0,
                max_tokens=512,
            )
            text = response.choices[0].message.content or ""
            data = json.loads(text)
            return {f: data.get(f) for f in EXTRACTION_FIELDS}
        except Exception:
            return _regex_extract(raw_text)


class ClaudeProvider(LLMProvider):
    """Real Anthropic Claude extraction (requires VAULT_ANTHROPIC_API_KEY)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        try:
            import anthropic  # type: ignore[import-untyped]

            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=512,
                system=(
                    "Extract the following fields from the bill text as JSON: "
                    + ", ".join(EXTRACTION_FIELDS)
                    + ". Return ONLY valid JSON."
                ),
                messages=[{"role": "user", "content": _strip_pii_for_llm(raw_text)[:8000]}],
            )
            text = message.content[0].text if message.content else ""
            data = json.loads(text)
            return {f: data.get(f) for f in EXTRACTION_FIELDS}
        except Exception:
            return _regex_extract(raw_text)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider (default: mock)."""
    provider = getattr(settings, "VAULT_LLM_PROVIDER", "mock").lower()
    if provider == "gemini":
        api_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
        if api_key:
            model_name = getattr(settings, "GEMINI_MODEL", None) or os.environ.get("GEMINI_MODEL")
            return GeminiProvider(api_key, model_name=model_name)
        logger.info(
            "VAULT_LLM_PROVIDER=gemini set but GEMINI_API_KEY is empty; defaulting to mock provider"
        )
        return MockProvider()

    elif provider == "openai":
        api_key = getattr(settings, "VAULT_OPENAI_API_KEY", "") or os.environ.get(
            "VAULT_OPENAI_API_KEY", ""
        )
        if api_key:
            return OpenAIProvider(api_key)
        return MockProvider()

    elif provider == "claude":
        api_key = getattr(settings, "VAULT_ANTHROPIC_API_KEY", "") or os.environ.get(
            "VAULT_ANTHROPIC_API_KEY", ""
        )
        if api_key:
            return ClaudeProvider(api_key)
        return MockProvider()

    return MockProvider()
