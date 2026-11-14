# Vault — Test Plan and Verification Matrix (Experiment 8 & 11)

Software Engineering Lab | Team: Vartika Sharma, Tejas Kaushik, Isha Shrivastav, Sudarshan Gupta

---

## 1. Scope & Strategy

This document establishes the test plan, verification methodology, and test execution matrix for the Vault MVP.
Testing encompasses:
- **Unit Testing (Deterministic Calculations):** Pure engine arithmetic (cash flow, net worth, DTI, coverage, investment capacity, risk scoring, asset allocation, goal projections, warranty dates, service scheduler, budget nudges).
- **Integration Testing:** FastAPI endpoints, database persistence via PostgreSQL & SQLAlchemy, JWT authorization, file parsing, and daily background jobs.
- **Security & Multi-Tenant Isolation:** Verifying that no user can access, modify, or infer another user's financial records, appliances, or bills (returning HTTP 403 or 404).
- **Contract & Guardrail Verification:** Ensuring LLM output passes the number-guard and forbidden-terms filter.

---

## 2. Test Execution Matrix

*Status and Actual Result columns are provided for tracking test executions during Experiments 8, 10, and 11.*

| ID | FR / NFR | Test Case Summary | Preconditions & Inputs | Execution Steps | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-01 | FR-1 | User Signup & Consent | Valid email, password, consent=True | `POST /api/v1/auth/signup` with credentials | HTTP 201, User created with hashed password and consent timestamp | | |
| TC-02 | FR-1 | User Login & JWT Generation | Registered user credentials | `POST /api/v1/auth/login` | HTTP 200, JWT access token returned with user claims | | |
| TC-03 | FR-2 | Bill Document Upload | Valid PDF/PNG/JPEG bill document (< 10MB) | `POST /api/v1/bills/upload` with multipart file | HTTP 201, Bill stored with extraction confidence values | | |
| TC-04 | FR-2 | Reject Oversized Bill | File exceeding 10MB limit | `POST /api/v1/bills/upload` with >10MB payload | HTTP 422/400 validation error, file rejected | | |
| TC-05 | FR-3 | Bill Review & Field Correction | Extracted bill draft with confidence scores | `PUT /api/v1/bills/{id}/correct` with corrected details | HTTP 200, Bill fields updated, marked as user-verified | | |
| TC-06 | FR-4 | Confirm Appliance Record | Verified bill or manual appliance details | `POST /api/v1/appliances` | HTTP 201, Appliance record created, linked to category | | |
| TC-07 | FR-5 | Service Schedule Calculation | Category with 6-month interval, purchase date | Auto-triggered on appliance creation | Periodic service records created within 12-month horizon | | |
| TC-08 | FR-5 | Warranty End Date Clamping | Purchase date on month-end (e.g. Aug 31 + 3 mo) | Calculation via `warranty_end_date` | Clamped to valid month-end (Nov 30), leap years clamped to Feb 29 | | |
| TC-09 | FR-6 | Appliance Warranty Reminders | Appliance with warranty end date | Creation of appliance | Reminders generated at 30 days and 7 days prior to expiry | | |
| TC-10 | FR-6 | Daily Reminder Background Job | Due reminder records in database (remind_on <= today) | Run `run_daily_reminders(db, today)` | Due reminders marked `sent=True`; future reminders untouched | | |
| TC-11 | FR-7 | Transaction CRUD & Category Filter | Authenticated session | `POST`, `GET`, `DELETE` on `/api/v1/finance/transactions` | HTTP 200/201, Transactions stored with valid category | | |
| TC-12 | FR-8 | Budgeting Nudge Trigger | MTD spending exceeds prior month or pace > 110% | Invoke `compute_budget_nudge` | Nudge generated with neutral tone naming largest increased category | | |
| TC-13 | FR-9 | Goal Contributions (0% Scenario) | Target ₹50,000, Saved ₹5,000, 12 months left | Compute required contribution at 0% rate | Required contribution is exactly ₹3,750.00/month | | |
| TC-14 | FR-9 | Goal Multi-Scenario Projections | Goal horizon > 60 months | `POST /api/v1/goals` | Projections computed for 0%, 6%, and 10% annual returns | | |
| TC-15 | FR-10 | Financial Snapshot Aggregation | Income sources, transactions, liabilities, holdings | `GET /api/v1/dashboard/summary` | Deterministic cash flow, DTI, net worth, and coverage returned | | |
| TC-16 | FR-11 | Unified Dashboard Overview | Scenario with appliances, liabilities, goals | `GET /api/v1/dashboard/summary` | Top recommendation, upcoming obligations, asset alerts displayed | | |
| TC-17 | FR-12 | Timeline Events Ordering | Reminders, EMIs, services, goal deadlines | `GET /api/v1/dashboard/timeline` | Events sorted chronologically with high-urgency priority | | |
| TC-18 | FR-15 | Income Sources Management | User income streams (monthly, weekly, yearly) | `POST /api/v1/finance/income-sources` | Normalized monthly income calculated accurately | | |
| TC-19 | FR-16 | Liability Recording & EMI Due Day | Active personal loan or home loan | `POST /api/v1/finance/liabilities` | Liability created and monthly EMI reminder scheduled 3d before due | | |
| TC-20 | FR-17 | Financial Holdings Tracking | Liquid reserves, mutual funds, provident fund | `POST /api/v1/finance/holdings` | Emergency reserves and overall net worth updated accurately | | |
| TC-21 | FR-18 | Net Worth Pure Formula | Holdings sum minus active liability principals | `FinancialEngine.compute_financial_snapshot` | Net worth equals holdings - debt; physical assets reported separately | | |
| TC-22 | FR-19 | Emergency Coverage Calculation | Liquid reserves divided by monthly burn | `FinancialEngine.compute_financial_snapshot` | Exact months of coverage returned; 999.00 if burn is zero | | |
| TC-23 | FR-20 | Freshness Indicators | Holdings/liabilities updated > 30 days ago | Financial snapshot evaluation | `is_stale=True` with explicit audit reasons returned | | |
| TC-24 | FR-21 | Capacity Gate: Negative Cash Flow | Essential expenses + EMI exceed monthly income | `InvestmentEngine.compute_investment_capacity` | Capacity blocked, status="blocked", reason="NEGATIVE_CASH_FLOW" | | |
| TC-25 | FR-21 | Capacity Gate: Low Emergency Fund | Emergency coverage < 3 months | `InvestmentEngine.compute_investment_capacity` | Capacity blocked, status="blocked", reason="EMERGENCY_FUND_LOW" | | |
| TC-26 | FR-21 | Capacity Gate: High Interest Debt | Active loan with interest rate >= 12% | `InvestmentEngine.compute_investment_capacity` | Capacity blocked, status="blocked", reason="HIGH_INTEREST_DEBT" | | |
| TC-27 | FR-21 | Golden Scenario A Capacity | Scenario A benchmark data (Spec 6.6) | Full pipeline execution | Capacity blocked with reason EMERGENCY_FUND_LOW | | |
| TC-28 | FR-21 | Golden Scenario B Capacity | Scenario B benchmark data (Spec 6.6) | Full pipeline execution | Sustainable capacity equals surplus after 10% buffer and goals | | |
| TC-29 | FR-22 | Risk Questionnaire Scoring | 5 standard risk questionnaire answers | `RiskEngine.score_questionnaire` | Accurate score (5 to 25) mapped to conservative/moderate/aggressive | | |
| TC-30 | FR-22 | Risk Capacity "Lower-Of" Rule | High risk tolerance but low financial capacity | `RiskEngine.compute_effective_level` | Effective risk level capped by financial capacity level | | |
| TC-31 | FR-23 | Advisor Rules Priority Order | Multiple triggers present (debt + low coverage) | `AdvisorEngine.build_advisor_plan` | Recommendations ordered strictly by priority rank 0 to 7 | | |
| TC-32 | FR-24 | Recommendation Decision Status | Proposed recommendation item | `POST /api/v1/advisor/recommendations/{id}/decision` | Decision recorded as "accepted" or "dismissed" with timestamp | | |
| TC-33 | FR-25 | Number-Guard Faithful Text | Explainer text matching input numbers | `AdvisorExplainer.verify_text` | Text accepted with guard check passed | | |
| TC-34 | FR-25 | Number-Guard Rejects Hallucination | Explainer text with invented return/number | `AdvisorExplainer.verify_text` | Text rejected; deterministic template fallback activated | | |
| TC-35 | FR-25 | Number-Guard Rejects Forbidden Terms | Explainer containing "guaranteed" or "assured" | `AdvisorExplainer.verify_text` | Guard rejects statement; fallback template used | | |
| TC-36 | FR-26 | Statutory Disclaimer Display | Any recommendation plan response | `GET /api/v1/advisor/recommendations` | Required SEBI decision support disclaimer present in payload & UI | | |
| TC-37 | FR-29 | Insufficient Data Warning | New user with no income or expense data | `GET /api/v1/advisor/recommendations` | Status "insufficient_data" returned with list of missing items | | |
| TC-38 | FR-30 | Account Data Export | User with bills, appliances, finances, goals | `GET /api/v1/auth/export-data` | Complete JSON payload returned containing all user records | | |
| TC-39 | FR-30 | Account Data Purge (Right to be Forgotten)| User requests account deletion | `DELETE /api/v1/auth/delete-account` | User and all associated data permanently deleted | | |
| TC-40 | NFR-3 | Multi-Tenant User Isolation | User A attempts to access User B's record | `GET /api/v1/appliances/{b_id}` with User A token | HTTP 404 or 403 returned, access strictly denied | | |
| TC-41 | NFR-6 | Health & Readiness Probe | Service runtime active | `GET /health` | HTTP 200 `{"status": "ok", "app": "vault"}` | | |
| TC-42 | NFR-7 | Decision Support Framing | UI and backend recommendation interfaces | Inspection of all generated outputs | Free of named financial products, trade execution, or buy signals | | |

---

## 3. Automated Test Execution Commands

```bash
# Run all backend unit & integration tests with engine coverage verification
cd backend && ../.venv/bin/pytest --cov=app/engines --cov-report=term-missing tests/

# Run frontend test suite
cd frontend && npm test

# Run frontend build & lint
cd frontend && npm run build && npm run lint
```
