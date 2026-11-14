# Vault API Reference (OpenAPI 3.1)

Generated automatically from the FastAPI application schema.

**Title:** Vault
**Version:** 0.1.0
**Description:** Vault - Connected Personal Finance and Asset-Protection Platform

---

## `/`

### GET `/`
- **Summary:** Root

**Responses:**
- `200`: Successful Response

---

## `/api/v1/appliances`

### GET `/api/v1/appliances`
- **Tags:** appliances
- **Summary:** List Appliances
- **Description:** FR-4, NFR-3: List user's appliances.

**Responses:**
- `200`: Successful Response

### POST `/api/v1/appliances`
- **Tags:** appliances
- **Summary:** Confirm Appliance
- **Description:** FR-4, FR-5, FR-6: Confirm appliance; create service schedule and reminders.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/ApplianceCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/appliances/{appliance_id}`

### GET `/api/v1/appliances/{appliance_id}`
- **Tags:** appliances
- **Summary:** Get Appliance
- **Description:** FR-4, NFR-3: Get appliance by ID — owner only.

**Parameters:**
- `appliance_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

### PATCH `/api/v1/appliances/{appliance_id}`
- **Tags:** appliances
- **Summary:** Update Appliance
- **Description:** FR-4: Partially update an appliance.

**Parameters:**
- `appliance_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/ApplianceUpdate`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

### DELETE `/api/v1/appliances/{appliance_id}`
- **Tags:** appliances
- **Summary:** Delete Appliance
- **Description:** FR-4: Delete an appliance and its services/reminders (cascade).

**Parameters:**
- `appliance_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/api/v1/auth/login`

### POST `/api/v1/auth/login`
- **Tags:** auth
- **Summary:** Login
- **Description:** FR-1 & NFR-3: Authenticate user credentials and return a signed JWT access token.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/UserLogin`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/auth/me`

### GET `/api/v1/auth/me`
- **Tags:** auth
- **Summary:** Get Me
- **Description:** NFR-3: Get current authenticated user profile.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/auth/signup`

### POST `/api/v1/auth/signup`
- **Tags:** auth
- **Summary:** Signup
- **Description:** FR-1: Register a new user with email, password, and mandatory data processing consent.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/UserSignup`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/bills`

### POST `/api/v1/bills`
- **Tags:** bills
- **Summary:** Upload Bill
- **Description:** FR-2, FR-3: Upload a bill file, extract fields, return structured result.

**Request Body:**
- Content-Type: `multipart/form-data` (Schema: `#/components/schemas/Body_upload_bill_api_v1_bills_post`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/bills/{bill_id}`

### GET `/api/v1/bills/{bill_id}`
- **Tags:** bills
- **Summary:** Get Bill
- **Description:** FR-2, NFR-3: Get bill by ID — owner only.

**Parameters:**
- `bill_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/bills/{bill_id}/correct`

### PATCH `/api/v1/bills/{bill_id}/correct`
- **Tags:** bills
- **Summary:** Correct Bill
- **Description:** FR-4: User submits corrections; mark parse_status='corrected', record corrected fields.

**Parameters:**
- `bill_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/BillCorrectRequest`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/dashboard`

### GET `/api/v1/dashboard`
- **Tags:** overview
- **Summary:** Get Dashboard
- **Description:** FR-11, FR-18, FR-28: Complete unified financial & asset dashboard.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/demo/seed`

### POST `/api/v1/demo/seed`
- **Tags:** overview
- **Summary:** Trigger Demo Seed
- **Description:** Part 7.4 & 6.6: Seed golden demo user (Scenario A or B).

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/DemoSeedRequest`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/goals`

### GET `/api/v1/goals`
- **Tags:** goals
- **Summary:** List Goals

**Responses:**
- `200`: Successful Response

### POST `/api/v1/goals`
- **Tags:** goals
- **Summary:** Create Goal

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/GoalCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/goals/{goal_id}`

### GET `/api/v1/goals/{goal_id}`
- **Tags:** goals
- **Summary:** Get Goal

**Parameters:**
- `goal_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/goals/{goal_id}/add-saving`

### POST `/api/v1/goals/{goal_id}/add-saving`
- **Tags:** goals
- **Summary:** Add Saving

**Parameters:**
- `goal_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/GoalAddSavingRequest`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/goals/{goal_id}/projection`

### GET `/api/v1/goals/{goal_id}/projection`
- **Tags:** goals
- **Summary:** Get Goal Projection

**Parameters:**
- `goal_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/health`

### GET `/api/v1/health`
- **Tags:** health
- **Summary:** Get Health
- **Description:** NFR-6: Health check endpoint verifying the service is running.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/holdings`

### GET `/api/v1/holdings`
- **Tags:** finance
- **Summary:** List Holdings

**Responses:**
- `200`: Successful Response

### POST `/api/v1/holdings`
- **Tags:** finance
- **Summary:** Create Holding

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/HoldingCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/holdings/{holding_id}`

### DELETE `/api/v1/holdings/{holding_id}`
- **Tags:** finance
- **Summary:** Delete Holding

**Parameters:**
- `holding_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/api/v1/income-sources`

### GET `/api/v1/income-sources`
- **Tags:** finance
- **Summary:** List Income Sources

**Responses:**
- `200`: Successful Response

### POST `/api/v1/income-sources`
- **Tags:** finance
- **Summary:** Create Income Source

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/IncomeSourceCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/income-sources/{source_id}`

### DELETE `/api/v1/income-sources/{source_id}`
- **Tags:** finance
- **Summary:** Delete Income Source

**Parameters:**
- `source_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/api/v1/investment-capacity`

### GET `/api/v1/investment-capacity`
- **Tags:** advisor
- **Summary:** Get Investment Capacity
- **Description:** FR-21, FR-29: Step-by-step breakdown of monthly investment capacity.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/jobs/daily-reminders`

### POST `/api/v1/jobs/daily-reminders`
- **Tags:** reminders
- **Summary:** Trigger Daily Reminders
- **Description:** FR-6, NFR-4: Dev/admin endpoint to trigger the daily reminder job manually.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/liabilities`

### GET `/api/v1/liabilities`
- **Tags:** finance
- **Summary:** List Liabilities

**Responses:**
- `200`: Successful Response

### POST `/api/v1/liabilities`
- **Tags:** finance
- **Summary:** Create Liability

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/LiabilityCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/liabilities/{liability_id}`

### DELETE `/api/v1/liabilities/{liability_id}`
- **Tags:** finance
- **Summary:** Delete Liability

**Parameters:**
- `liability_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/api/v1/me`

### GET `/api/v1/me`
- **Tags:** auth
- **Summary:** Get Me
- **Description:** NFR-3: Get current authenticated user profile.

**Responses:**
- `200`: Successful Response

### DELETE `/api/v1/me`
- **Tags:** auth
- **Summary:** Delete User Account
- **Description:** FR-30: Permanently delete current user account and all cascaded data.

**Responses:**
- `204`: Successful Response

---

## `/api/v1/me/export`

### GET `/api/v1/me/export`
- **Tags:** auth
- **Summary:** Export User Data
- **Description:** FR-30: Export all user-owned records as structured JSON.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/recommendations`

### GET `/api/v1/recommendations`
- **Tags:** advisor
- **Summary:** Get Recommendations
- **Description:** Return latest recommendations for current user with statutory disclaimer.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/recommendations/generate`

### POST `/api/v1/recommendations/generate`
- **Tags:** advisor
- **Summary:** Generate Recommendations
- **Description:** FR-23, 24, 25: Build prioritized recommendations, explain them via LLM/template, save to DB.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/recommendations/{recommendation_id}`

### PATCH `/api/v1/recommendations/{recommendation_id}`
- **Tags:** advisor
- **Summary:** Update Recommendation Status
- **Description:** FR-26: User can accept, edit or reject a recommendation; stores the decision.

**Parameters:**
- `recommendation_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/RecommendationUpdate`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/reminders`

### GET `/api/v1/reminders`
- **Tags:** reminders
- **Summary:** List Reminders
- **Description:** FR-6, NFR-3: Get user's upcoming reminders (not sent, remind_on >= today).

**Responses:**
- `200`: Successful Response

---

## `/api/v1/risk-profile`

### GET `/api/v1/risk-profile`
- **Tags:** advisor
- **Summary:** Get Risk Profile
- **Description:** Get the user's latest assessed risk profile.

**Responses:**
- `200`: Successful Response

### POST `/api/v1/risk-profile`
- **Tags:** advisor
- **Summary:** Submit Risk Profile
- **Description:** Submit 8 answers, calculate score, tolerance, capacity, and effective risk level.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/RiskProfileCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/risk-questionnaire`

### GET `/api/v1/risk-questionnaire`
- **Tags:** advisor
- **Summary:** Get Risk Questionnaire
- **Description:** Return the 8 standardized risk questionnaire questions and options.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/services/{service_id}`

### PATCH `/api/v1/services/{service_id}`
- **Tags:** appliances
- **Summary:** Update Service
- **Description:** FR-5: Mark a service as done or update its details.

**Parameters:**
- `service_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/ServiceUpdate`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/api/v1/snapshot`

### GET `/api/v1/snapshot`
- **Tags:** finance
- **Summary:** Get Snapshot

**Responses:**
- `200`: Successful Response

---

## `/api/v1/timeline`

### GET `/api/v1/timeline`
- **Tags:** overview
- **Summary:** Get Timeline
- **Description:** FR-12: Unified chronological calendar and timeline of upcoming events.

**Responses:**
- `200`: Successful Response

---

## `/api/v1/transactions`

### GET `/api/v1/transactions`
- **Tags:** finance
- **Summary:** List Transactions

**Responses:**
- `200`: Successful Response

### POST `/api/v1/transactions`
- **Tags:** finance
- **Summary:** Create Transaction

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/TransactionCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/api/v1/transactions/{txn_id}`

### DELETE `/api/v1/transactions/{txn_id}`
- **Tags:** finance
- **Summary:** Delete Transaction

**Parameters:**
- `txn_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/appliances`

### GET `/appliances`
- **Tags:** appliances
- **Summary:** List Appliances
- **Description:** FR-4, NFR-3: List user's appliances.

**Responses:**
- `200`: Successful Response

### POST `/appliances`
- **Tags:** appliances
- **Summary:** Confirm Appliance
- **Description:** FR-4, FR-5, FR-6: Confirm appliance; create service schedule and reminders.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/ApplianceCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/appliances/{appliance_id}`

### GET `/appliances/{appliance_id}`
- **Tags:** appliances
- **Summary:** Get Appliance
- **Description:** FR-4, NFR-3: Get appliance by ID — owner only.

**Parameters:**
- `appliance_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

### PATCH `/appliances/{appliance_id}`
- **Tags:** appliances
- **Summary:** Update Appliance
- **Description:** FR-4: Partially update an appliance.

**Parameters:**
- `appliance_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/ApplianceUpdate`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

### DELETE `/appliances/{appliance_id}`
- **Tags:** appliances
- **Summary:** Delete Appliance
- **Description:** FR-4: Delete an appliance and its services/reminders (cascade).

**Parameters:**
- `appliance_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/auth/login`

### POST `/auth/login`
- **Tags:** auth
- **Summary:** Login
- **Description:** FR-1 & NFR-3: Authenticate user credentials and return a signed JWT access token.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/UserLogin`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/auth/me`

### GET `/auth/me`
- **Tags:** auth
- **Summary:** Get Me
- **Description:** NFR-3: Get current authenticated user profile.

**Responses:**
- `200`: Successful Response

---

## `/auth/signup`

### POST `/auth/signup`
- **Tags:** auth
- **Summary:** Signup
- **Description:** FR-1: Register a new user with email, password, and mandatory data processing consent.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/UserSignup`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/bills`

### POST `/bills`
- **Tags:** bills
- **Summary:** Upload Bill
- **Description:** FR-2, FR-3: Upload a bill file, extract fields, return structured result.

**Request Body:**
- Content-Type: `multipart/form-data` (Schema: `#/components/schemas/Body_upload_bill_bills_post`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/bills/{bill_id}`

### GET `/bills/{bill_id}`
- **Tags:** bills
- **Summary:** Get Bill
- **Description:** FR-2, NFR-3: Get bill by ID — owner only.

**Parameters:**
- `bill_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/bills/{bill_id}/correct`

### PATCH `/bills/{bill_id}/correct`
- **Tags:** bills
- **Summary:** Correct Bill
- **Description:** FR-4: User submits corrections; mark parse_status='corrected', record corrected fields.

**Parameters:**
- `bill_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/BillCorrectRequest`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/dashboard`

### GET `/dashboard`
- **Tags:** overview
- **Summary:** Get Dashboard
- **Description:** FR-11, FR-18, FR-28: Complete unified financial & asset dashboard.

**Responses:**
- `200`: Successful Response

---

## `/demo/seed`

### POST `/demo/seed`
- **Tags:** overview
- **Summary:** Trigger Demo Seed
- **Description:** Part 7.4 & 6.6: Seed golden demo user (Scenario A or B).

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/DemoSeedRequest`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/goals`

### GET `/goals`
- **Tags:** goals
- **Summary:** List Goals

**Responses:**
- `200`: Successful Response

### POST `/goals`
- **Tags:** goals
- **Summary:** Create Goal

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/GoalCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/goals/{goal_id}`

### GET `/goals/{goal_id}`
- **Tags:** goals
- **Summary:** Get Goal

**Parameters:**
- `goal_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/goals/{goal_id}/add-saving`

### POST `/goals/{goal_id}/add-saving`
- **Tags:** goals
- **Summary:** Add Saving

**Parameters:**
- `goal_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/GoalAddSavingRequest`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/goals/{goal_id}/projection`

### GET `/goals/{goal_id}/projection`
- **Tags:** goals
- **Summary:** Get Goal Projection

**Parameters:**
- `goal_id` (path, required): 

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/health`

### GET `/health`
- **Tags:** health
- **Summary:** Get Health
- **Description:** NFR-6: Health check endpoint verifying the service is running.

**Responses:**
- `200`: Successful Response

---

## `/holdings`

### GET `/holdings`
- **Tags:** finance
- **Summary:** List Holdings

**Responses:**
- `200`: Successful Response

### POST `/holdings`
- **Tags:** finance
- **Summary:** Create Holding

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/HoldingCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/holdings/{holding_id}`

### DELETE `/holdings/{holding_id}`
- **Tags:** finance
- **Summary:** Delete Holding

**Parameters:**
- `holding_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/income-sources`

### GET `/income-sources`
- **Tags:** finance
- **Summary:** List Income Sources

**Responses:**
- `200`: Successful Response

### POST `/income-sources`
- **Tags:** finance
- **Summary:** Create Income Source

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/IncomeSourceCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/income-sources/{source_id}`

### DELETE `/income-sources/{source_id}`
- **Tags:** finance
- **Summary:** Delete Income Source

**Parameters:**
- `source_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/investment-capacity`

### GET `/investment-capacity`
- **Tags:** advisor
- **Summary:** Get Investment Capacity
- **Description:** FR-21, FR-29: Step-by-step breakdown of monthly investment capacity.

**Responses:**
- `200`: Successful Response

---

## `/jobs/daily-reminders`

### POST `/jobs/daily-reminders`
- **Tags:** reminders
- **Summary:** Trigger Daily Reminders
- **Description:** FR-6, NFR-4: Dev/admin endpoint to trigger the daily reminder job manually.

**Responses:**
- `200`: Successful Response

---

## `/liabilities`

### GET `/liabilities`
- **Tags:** finance
- **Summary:** List Liabilities

**Responses:**
- `200`: Successful Response

### POST `/liabilities`
- **Tags:** finance
- **Summary:** Create Liability

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/LiabilityCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/liabilities/{liability_id}`

### DELETE `/liabilities/{liability_id}`
- **Tags:** finance
- **Summary:** Delete Liability

**Parameters:**
- `liability_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---

## `/me`

### GET `/me`
- **Tags:** auth
- **Summary:** Get Me
- **Description:** NFR-3: Get current authenticated user profile.

**Responses:**
- `200`: Successful Response

### DELETE `/me`
- **Tags:** auth
- **Summary:** Delete User Account
- **Description:** FR-30: Permanently delete current user account and all cascaded data.

**Responses:**
- `204`: Successful Response

---

## `/me/export`

### GET `/me/export`
- **Tags:** auth
- **Summary:** Export User Data
- **Description:** FR-30: Export all user-owned records as structured JSON.

**Responses:**
- `200`: Successful Response

---

## `/recommendations`

### GET `/recommendations`
- **Tags:** advisor
- **Summary:** Get Recommendations
- **Description:** Return latest recommendations for current user with statutory disclaimer.

**Responses:**
- `200`: Successful Response

---

## `/recommendations/generate`

### POST `/recommendations/generate`
- **Tags:** advisor
- **Summary:** Generate Recommendations
- **Description:** FR-23, 24, 25: Build prioritized recommendations, explain them via LLM/template, save to DB.

**Responses:**
- `200`: Successful Response

---

## `/recommendations/{recommendation_id}`

### PATCH `/recommendations/{recommendation_id}`
- **Tags:** advisor
- **Summary:** Update Recommendation Status
- **Description:** FR-26: User can accept, edit or reject a recommendation; stores the decision.

**Parameters:**
- `recommendation_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/RecommendationUpdate`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/reminders`

### GET `/reminders`
- **Tags:** reminders
- **Summary:** List Reminders
- **Description:** FR-6, NFR-3: Get user's upcoming reminders (not sent, remind_on >= today).

**Responses:**
- `200`: Successful Response

---

## `/risk-profile`

### GET `/risk-profile`
- **Tags:** advisor
- **Summary:** Get Risk Profile
- **Description:** Get the user's latest assessed risk profile.

**Responses:**
- `200`: Successful Response

### POST `/risk-profile`
- **Tags:** advisor
- **Summary:** Submit Risk Profile
- **Description:** Submit 8 answers, calculate score, tolerance, capacity, and effective risk level.

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/RiskProfileCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/risk-questionnaire`

### GET `/risk-questionnaire`
- **Tags:** advisor
- **Summary:** Get Risk Questionnaire
- **Description:** Return the 8 standardized risk questionnaire questions and options.

**Responses:**
- `200`: Successful Response

---

## `/services/{service_id}`

### PATCH `/services/{service_id}`
- **Tags:** appliances
- **Summary:** Update Service
- **Description:** FR-5: Mark a service as done or update its details.

**Parameters:**
- `service_id` (path, required): 

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/ServiceUpdate`)

**Responses:**
- `200`: Successful Response
- `422`: Validation Error

---

## `/snapshot`

### GET `/snapshot`
- **Tags:** finance
- **Summary:** Get Snapshot

**Responses:**
- `200`: Successful Response

---

## `/timeline`

### GET `/timeline`
- **Tags:** overview
- **Summary:** Get Timeline
- **Description:** FR-12: Unified chronological calendar and timeline of upcoming events.

**Responses:**
- `200`: Successful Response

---

## `/transactions`

### GET `/transactions`
- **Tags:** finance
- **Summary:** List Transactions

**Responses:**
- `200`: Successful Response

### POST `/transactions`
- **Tags:** finance
- **Summary:** Create Transaction

**Request Body:**
- Content-Type: `application/json` (Schema: `#/components/schemas/TransactionCreate`)

**Responses:**
- `201`: Successful Response
- `422`: Validation Error

---

## `/transactions/{txn_id}`

### DELETE `/transactions/{txn_id}`
- **Tags:** finance
- **Summary:** Delete Transaction

**Parameters:**
- `txn_id` (path, required): 

**Responses:**
- `204`: Successful Response
- `422`: Validation Error

---
