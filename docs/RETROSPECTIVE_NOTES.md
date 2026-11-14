# Vault — Retrospective Notes

Software Engineering Lab | Team: Vartika Sharma, Tejas Kaushik, Isha Shrivastav, Sudarshan Gupta

---

## 1. Project Overview & Objectives

Vault was conceived to solve possession leakage (expired warranties, forgotten free services, lost bills) and decision leakage (untracked spending, loans disconnected from investment planning, underfunded goals) by connecting documents, assets, liabilities, and investments into a single unified financial platform.

---

## 2. What Went Well (Successes)

- **Pure Engine Architecture:** Keeping calculation engines (`financial_engine`, `investment_engine`, `risk_engine`, `goal_engine`, `budget_engine`, `service_scheduler`, `dashboard_aggregator`) completely decoupled from database, network, and clock state allowed 100% deterministic testing and >= 90% test coverage across all financial math.
- **Strict User Isolation & Security:** Every database query filters by authenticated `user_id`. Automated tests confirm that user A cannot inspect or modify user B's records (HTTP 403 / 404).
- **Explainability & Hybrid AI Guardrails:** The LLM integration is constrained strictly to extracting fields and formatting human explanations with deterministic number-guard verification (rejecting fabricated returns or forbidden claims like "guaranteed").
- **Reproducible Local Development & CI:** Docker Compose for PostgreSQL, Alembic migrations for schema lifecycle, and GitHub Actions CI running ruff, pytest, vitest, and eslint ensured high reliability across PRs.

---

## 3. Challenges & Gaps

- **PostgreSQL Test Isolation:** Isolating transactions during integration test suites required nested savepoints to prevent test interactions while allowing FastAPI endpoints to execute internal transaction commits.
- **Date Clamping Edge Cases:** Warranty end dates and EMI due dates across leap years (Feb 29) and month-ends (e.g. Aug 31 -> Nov 30) required explicit clamping logic.
- **Scope Discipline:** Deferring direct bank account aggregation, SMS scraping, and trade execution avoided regulatory licensing boundaries (SEBI IA) and kept the MVP delivery feasible within the 14-day schedule.

---

## 4. Key Metrics & Evidence

- **Engine Coverage:** 95% total engine coverage (694 statements, 38 missed).
- **Backend Test Suite:** 82 passing tests (unit, integration, isolation, security, golden scenarios).
- **Frontend Test Suite:** Vitest component tests and production TypeScript build passing cleanly.
- **Code Quality:** Ruff lint/format checks clean across all backend modules; ESLint clean across React code.

---

## 5. Team Reflections & Individual Contributions

*(Team members to add their individual reflections and learnings for Experiment 12)*

- **Vartika Sharma (Document Intelligence):**
- **Tejas Kaushik (Frontend & UI Engineering):**
- **Isha Shrivastav (Financial Engine & Advisor Rules):**
- **Sudarshan Gupta (Backend Infrastructure, Auth & CI/CD):**
