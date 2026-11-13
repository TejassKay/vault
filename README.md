# Vault — Connected Personal Finance & Asset-Protection Platform

Vault connects what a user **owns** (appliances, invoices, warranties, service schedules), **owes** (loans, EMIs, credit liabilities), and **saves** (goals, holdings, cash flow) into an actionable, explainable decision-support system.

Built strictly according to the specifications in [`docs/VAULT_SPEC.md`](./docs/VAULT_SPEC.md).

---

## 1. System Architecture & Tech Stack

Vault is structured as a **Layered Monolith**:
* **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL.
* **Frontend:** React (Vite), TypeScript, Tailwind CSS, Recharts, React Router.
* **Hybrid AI Boundary:**
  * Extraction and explanation only.
  * All financial metrics, calculations, and rules run on deterministic, pure Python engines using `Decimal` in INR.
  * Number-guard validates all natural-language explanations against the plan JSON, with strict template fallback.
* **Test & Quality:** Pytest, Ruff, Vitest, ESLint, GitHub Actions CI.

---

## 2. Prerequisites

* **Python:** 3.11 or 3.12 (`python3 --version`)
* **Node.js:** v18+ or v20+ (`node -v`, `npm -v`)
* **PostgreSQL:** Version 15+ or 16+ (or Docker)

---

## 3. Quickstart: Local Setup Without Docker (Recommended)

If you do not have Docker installed, you can run PostgreSQL natively on macOS using Homebrew.

### Step 1: Install and Start PostgreSQL
```bash
# 1. Install PostgreSQL 16 via Homebrew
brew install postgresql@16

# 2. Start PostgreSQL background service
brew services start postgresql@16

# 3. Create the postgres superuser and the vault database
createuser -s postgres 2>/dev/null || true
createdb -U postgres vault 2>/dev/null || true

# 4. (Optional) Set the password for user 'postgres' to 'postgres'
psql -U postgres -d vault -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```
The default `.env` is configured for `postgresql://postgres:postgres@localhost:5432/vault` and `VAULT_LLM_PROVIDER=mock`.

### Step 3: Setup Backend
```bash
# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements-dev.txt

# Start backend development server
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Backend will be available at:
* API Health: [http://localhost:8000/health](http://localhost:8000/health)
* Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 4: Setup Frontend (in a separate terminal)
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at [http://localhost:5173](http://localhost:5173).

---

## 4. Alternative: Docker Compose Setup

If you have Docker installed and running:
```bash
# Start PostgreSQL container
docker compose up -d postgres

# Or start the entire stack (Postgres + Backend + Frontend)
docker compose up --build
```

---

## 5. Running Tests & Quality Verification

### Backend Linting & Tests
```bash
# From workspace root with virtual environment activated:
source .venv/bin/activate

# 1. Check code quality & formatting with Ruff
ruff check backend/
ruff format --check backend/

# 2. Run unit tests with Pytest
pytest backend/tests -v
```

### Frontend Linting, Tests & Build
```bash
cd frontend

# 1. Run ESLint
npm run lint

# 2. Run unit tests with Vitest
npm test

# 3. Build production bundle with TypeScript check
npm run build
```

---

## 6. Continuous Integration (CI)

A GitHub Actions workflow is located at [`.github/workflows/ci.yml`](./.github/workflows/ci.yml).
On every push and pull request, CI automatically executes:
1. **Backend Job:** Spins up a PostgreSQL 16 service, installs Python 3.11 dependencies, runs `ruff check`, `ruff format --check`, and executes `pytest`.
2. **Frontend Job:** Sets up Node.js 20, installs npm dependencies, runs `npm run lint`, `npm test` (Vitest), and builds the production bundle via `npm run build`.

---

## 7. Phased Build Roadmap

Per [`docs/VAULT_SPEC.md`](./docs/VAULT_SPEC.md) Section 7.4 & 7.9:
* **Phase 0 (`feature/scaffold`):** Repository structure, FastAPI health check, React shell, Docker Compose, CI pipeline.
* **Phase 1 (`feature/db-auth`):** 13 PostgreSQL tables, Alembic migrations, JWT authentication, user isolation.
* **Phase 2 (`feature/assets`):** Bill upload, extraction, service scheduler, warranty alerts, reminders.
* **Phase 3 (`feature/finance-core`):** Transactions, income sources, liabilities, holdings, goals, financial engine metrics.
* **Phase 4 (`feature/advisor`):** Investment capacity, risk questionnaire, recommendation rules, LLM explainer & number-guard.
* **Phase 5 (`feature/dashboard`):** Unified dashboard, timeline/calendar, freshness badges, data export/delete.
* **Phase 6 (`feature/qa-docs`):** Test plan, integration tests, OpenAPI docs, retrospective.
