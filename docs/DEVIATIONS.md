# Architectural & Specification Deviations

## DEV-001: Google Gemini LLM Provider Integration
- **Date:** 2026-11-14
- **Sections Overridden:** Section 6.3 & 7.2 (Rule 3)
- **Description:** Added Google Gemini LLM provider (`GeminiProvider`) to `backend/app/integrations/llm.py` enabled via environment variables:
  - `VAULT_LLM_PROVIDER=gemini`
  - `GEMINI_API_KEY=<api-key>`
  - `GEMINI_MODEL=<model-name>` (no hardcoded model name; documented in `.env.example`).
- **Behavior:**
  - When `VAULT_LLM_PROVIDER=gemini` and `GEMINI_API_KEY` is provided, sends sanitized bill text (PII stripped) with a strict JSON schema prompt at temperature 0, 8-second timeout, and 1 retry.
  - When `GEMINI_API_KEY` is unset or empty, automatically defaults to `MockProvider` so that no keys are required for testing or local setup.
- **Rationale:** Supports modern multimodal LLM bill parsing while adhering strictly to Rule 7.2 (runs with zero keys by default).

## DEV-002: Spending insights page (new, not in the original spec)
- **Date:** 2026-11-16
- **Sections Overridden:** None (new capability extending Section 6.1 and 6.4)
- **Description:** Added `GET /analytics/summary` backed by `backend/app/engines/analytics.py` and `backend/app/repositories/analytics_repository.py`, plus the `/insights` frontend page with Recharts visualizations, table view toggle, and CSV export.
- **Rationale:** Provides visual spending breakdown, cash-flow trends, spending pace, month-over-month category comparison, and net worth composition without altering existing spec endpoints.
