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
