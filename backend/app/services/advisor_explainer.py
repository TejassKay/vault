"""FR-25, Spec 6.10, NFR-8, NFR-9, NFR-10: Advisor Explainer & Number-Guard.

Explains validated recommendation plans in neutral, plain language:
- Input is the plan JSON only (anonymized numbers and category names; NO personal/account identifiers).
- Number-guard extracts every number from generated text and verifies it matches a value in the plan JSON.
- Rejects explanations containing forbidden phrases ('guaranteed', 'risk-free', 'assured returns', 'will earn').
- Falls back to deterministic template explanation on rejection, timeout, or mock mode.
- Sets explanation_source to 'llm' or 'template'.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from app.engines.advisor_engine import RecommendationPlanItem
from app.integrations.llm import get_llm_provider

FORBIDDEN_PHRASES = [
    "guaranteed",
    "risk-free",
    "assured returns",
    "will earn",
]

# Regex to match numeric tokens in prose, e.g.: 18,750, 14,625.00, 41.18%, ₹35,000, 3, 6, 12
NUMBER_REGEX = re.compile(
    r"(?<![A-Za-z0-9_])(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d+)?)\s*%?(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


def extract_numbers_from_text(text: str) -> list[float]:
    """Extract all numeric values from text, stripping commas, currency symbols and percentage signs."""
    numbers: list[float] = []
    for match in NUMBER_REGEX.finditer(text):
        raw = match.group(1).replace(",", "")
        try:
            val = float(raw)
            numbers.append(val)
        except ValueError:
            continue
    return numbers


def collect_allowed_numbers(data: Any) -> set[float]:
    """Recursively collect all numeric values present in a dict/list/primitive."""
    allowed: set[float] = set()

    def _traverse(val: Any) -> None:
        if isinstance(val, (int, float, Decimal)):
            num = float(val)
            allowed.add(num)
            allowed.add(round(num, 0))
            allowed.add(round(num, 2))
        elif isinstance(val, dict):
            for _k, v in val.items():
                # Some keys might be categories or numbers
                _traverse(v)
        elif isinstance(val, (list, tuple, set)):
            for item in val:
                _traverse(item)
        elif isinstance(val, str):
            # Also extract numbers already explicitly written in fields like action or reason
            nums = extract_numbers_from_text(val)
            for n in nums:
                allowed.add(n)
                allowed.add(round(n, 0))
                allowed.add(round(n, 2))

    _traverse(data)
    return allowed


def number_guard(text: str, allowed_numbers: set[float]) -> tuple[bool, str]:
    """Guard rule (Spec 6.10):

    1. Reject if text contains forbidden phrases ('guaranteed', 'risk-free', 'assured returns', 'will earn').
    2. Extract every number from text; each must equal a value in allowed_numbers (within 0.05 tolerance).
    Returns: (is_valid, reason)
    """
    text_lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text_lower:
            return False, f"Forbidden phrase detected: '{phrase}'"

    extracted = extract_numbers_from_text(text)
    for num in extracted:
        # Check against allowed set with small floating point tolerance
        matched = any(abs(num - allowed) <= 0.05 for allowed in allowed_numbers)
        if not matched:
            return False, f"Unknown numeric value '{num}' not present in verified plan inputs"

    return True, "Passed number guard"


def generate_template_explanation(item: RecommendationPlanItem) -> str:
    """Deterministic template fallback explanation (Spec 6.10)."""
    trigger_part = f" Review trigger: {item.review_trigger}." if item.review_trigger else ""
    return f"{item.action}. {item.reason}{trigger_part}"


def sanitize_item_for_llm(item: RecommendationPlanItem) -> dict[str, Any]:
    """NFR-9: Strip all PII (names, emails, accounts, lender names). Provide only numbers and categories."""
    return {
        "priority_rank": item.priority_rank,
        "rec_type": item.rec_type,
        "action": item.action,
        "reason": item.reason,
        "assumptions": item.assumptions,
        "review_trigger": item.review_trigger,
        "inputs_snapshot": item.inputs_snapshot,
    }


def explain_and_guard_recommendation(item: RecommendationPlanItem) -> None:
    """Explain a single recommendation with number-guard and template fallback."""
    allowed = collect_allowed_numbers(sanitize_item_for_llm(item))
    provider = get_llm_provider()

    # If provider is MockProvider, generate template directly or check provider
    candidate_text: str | None = None
    if hasattr(provider, "explain_recommendation"):
        try:
            candidate_text = provider.explain_recommendation(sanitize_item_for_llm(item))
        except Exception:  # noqa: BLE001
            candidate_text = None

    if candidate_text:
        is_valid, _reason = number_guard(candidate_text, allowed)
        if is_valid:
            item.explanation_text = candidate_text.strip()
            item.explanation_source = "llm"
            return

    # Fallback to deterministic template
    item.explanation_text = generate_template_explanation(item)
    item.explanation_source = "template"


def explain_plan_recommendations(items: list[RecommendationPlanItem]) -> None:
    """Explain each recommendation in the list in place."""
    for item in items:
        explain_and_guard_recommendation(item)
