"""FR-3, 6.3: LLM integration — extract structured data from bill text.

Providers:
  mock   — returns template JSON; works with zero API keys (default)
  openai — real OpenAI API (requires VAULT_OPENAI_API_KEY)
  claude — real Anthropic API (requires VAULT_ANTHROPIC_API_KEY)

Selected via VAULT_LLM_PROVIDER env var.

The LLM must never feed a calculation or a decision (7.2 hybrid AI rule).
It is called only to fill extraction fields; all numbers come from the engines.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings

# Fields the LLM should return
EXTRACTION_FIELDS = [
    "product_name",
    "brand",
    "model_number",
    "seller",
    "price",
    "purchase_date",
    "warranty_months",
    "category",
]

ExtractionResult = dict[str, Any]  # {field: value_or_None}


class LLMProvider(ABC):
    """Abstract provider interface."""

    @abstractmethod
    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        """Return a dict mapping each EXTRACTION_FIELDS key to its value or None."""

    def explain_recommendation(self, plan_item: dict[str, Any]) -> str | None:
        """Explain a validated plan item in plain language using only provided numbers."""
        return None


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------

_MOCK_PATTERNS: dict[str, re.Pattern[str]] = {
    "product_name": re.compile(
        r"(?:product(?:\s*name)?|item(?:\s*description)?|description)[:\s]+([A-Za-z0-9 _\-\.\(\)\/]+)",
        re.IGNORECASE,
    ),
    "brand": re.compile(r"(?:brand|make)[:\s]+([A-Za-z0-9 _\-]+)", re.IGNORECASE),
    "model_number": re.compile(
        r"(?:model\s*(?:no\.?|number|#)|model)[:\s]+([A-Za-z0-9 _\-\/]+)",
        re.IGNORECASE,
    ),
    "seller": re.compile(
        r"(?:sold\s*by|seller|vendor|store|dealer)[:\s.]+([A-Za-z0-9 &.,\-]+)",
        re.IGNORECASE,
    ),
    "price": re.compile(
        r"(?:(?:grand\s*total|net\s*amount|total\s*amount|total|amount|price|mrp)[:\s.]*(?:rs\.?|inr|₹)?|(?:rs\.?|inr|₹))\s*([\d,]+(?:\.\d{1,2})?)",
        re.IGNORECASE,
    ),
    "purchase_date": re.compile(
        r"(?:invoice\s*date|bill\s*date|date\s*of\s*invoice|purchase\s*date|date)[:\s.]+(\d{1,2}[/-](?:[A-Za-z]{3,9}|\d{1,2})[/-]\d{2,4}|\d{1,2}\s+(?:[A-Za-z]{3,9})\s+\d{2,4}|\d{4}-\d{2}-\d{2})",
        re.IGNORECASE,
    ),
    "warranty_months": re.compile(
        r"(?:warranty(?:\s*period)?)[:\s.]+(\d+)\s*(months?|yrs?|years?)",
        re.IGNORECASE,
    ),
    "category": re.compile(r"(?:category|type)[:\s]+([A-Za-z0-9 _\-]+)", re.IGNORECASE),
}


def _regex_extract(text: str) -> ExtractionResult:
    """Apply simple regex rules to extract bill fields from raw text."""
    result: ExtractionResult = {}
    for field, pattern in _MOCK_PATTERNS.items():
        m = pattern.search(text)
        if m:
            value = m.group(1).strip().rstrip(".,;")
            # Normalise price: remove commas
            if field == "price":
                value = value.replace(",", "")
            # Normalise warranty: convert years to months
            if field == "warranty_months":
                orig = m.group(0).lower()
                if "yr" in orig or "year" in orig:
                    try:
                        value = str(int(value) * 12)
                    except ValueError:
                        pass
            result[field] = value
        else:
            result[field] = None
    return result


class MockProvider(LLMProvider):
    """FR-3 mock mode: regex rules only, no API calls."""

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        return _regex_extract(raw_text)


# ---------------------------------------------------------------------------
# Real providers (stubs — enabled by env vars)
# ---------------------------------------------------------------------------


class OpenAIProvider(LLMProvider):
    """Real OpenAI extraction (requires VAULT_OPENAI_API_KEY)."""

    _SYSTEM = (
        "You are a bill parser. Extract the following fields from the bill text as JSON: "
        + ", ".join(EXTRACTION_FIELDS)
        + ". Use null for missing fields. "
        "Return ONLY valid JSON, no prose. "
        "price must be a number string without currency symbols. "
        "purchase_date must be YYYY-MM-DD. warranty_months must be an integer."
    )

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        try:
            import openai  # type: ignore[import-untyped]

            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._SYSTEM},
                    {"role": "user", "content": raw_text[:8000]},
                ],
                temperature=0,
                max_tokens=512,
            )
            text = response.choices[0].message.content or ""
            data = json.loads(text)
            # ensure all keys present
            return {f: data.get(f) for f in EXTRACTION_FIELDS}
        except Exception:  # noqa: BLE001
            return _regex_extract(raw_text)

    def explain_recommendation(self, plan_item: dict[str, Any]) -> str | None:
        try:
            import openai  # type: ignore[import-untyped]

            client = openai.OpenAI(api_key=self._api_key)
            prompt = (
                "You are an educational financial decision support assistant. "
                "Explain the following recommendation plan item in plain, neutral language. "
                "CRITICAL RULES: Use ONLY the numbers present in the JSON. Add NO numbers, NO products, "
                "and NO promises or guarantees. Keep response under 150 words.\n\n"
                f"Plan JSON:\n{json.dumps(plan_item)}"
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You explain financial recommendations without adding numbers or guarantees.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=256,
            )
            return response.choices[0].message.content
        except Exception:  # noqa: BLE001
            return None


class ClaudeProvider(LLMProvider):
    """Real Anthropic Claude extraction (requires VAULT_ANTHROPIC_API_KEY)."""

    _SYSTEM = (
        "Extract the following fields from the bill text as JSON: "
        + ", ".join(EXTRACTION_FIELDS)
        + ". Use null for missing fields. "
        "Return ONLY valid JSON. "
        "price: number string without symbols. "
        "purchase_date: YYYY-MM-DD. warranty_months: integer."
    )

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def extract_bill_fields(self, raw_text: str) -> ExtractionResult:
        try:
            import anthropic  # type: ignore[import-untyped]

            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=512,
                system=self._SYSTEM,
                messages=[{"role": "user", "content": raw_text[:8000]}],
            )
            text = message.content[0].text if message.content else ""
            data = json.loads(text)
            return {f: data.get(f) for f in EXTRACTION_FIELDS}
        except Exception:  # noqa: BLE001
            return _regex_extract(raw_text)

    def explain_recommendation(self, plan_item: dict[str, Any]) -> str | None:
        try:
            import anthropic  # type: ignore[import-untyped]

            client = anthropic.Anthropic(api_key=self._api_key)
            prompt = (
                "You are an educational financial decision support assistant. "
                "Explain the following recommendation plan item in plain, neutral language. "
                "CRITICAL RULES: Use ONLY the numbers present in the JSON. Add NO numbers, NO products, "
                "and NO promises or guarantees. Keep response under 150 words.\n\n"
                f"Plan JSON:\n{json.dumps(plan_item)}"
            )
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=256,
                system="You explain financial recommendations without adding numbers or guarantees.",
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else None
        except Exception:  # noqa: BLE001
            return None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider (default: mock)."""
    provider = settings.VAULT_LLM_PROVIDER.lower()
    if provider == "openai":
        api_key = getattr(settings, "VAULT_OPENAI_API_KEY", "")
        if api_key:
            return OpenAIProvider(api_key)
    elif provider == "claude":
        api_key = getattr(settings, "VAULT_ANTHROPIC_API_KEY", "")
        if api_key:
            return ClaudeProvider(api_key)
    return MockProvider()
