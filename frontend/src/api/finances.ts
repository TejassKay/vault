import { apiRequest } from './client';

export interface Transaction {
  transaction_id: number;
  user_id: number;
  type: string;
  amount: number;
  category: string;
  txn_date: string;
  note?: string | null;
  is_recurring: boolean;
}

export interface IncomeSource {
  income_source_id: number;
  user_id: number;
  name: string;
  amount: number;
  frequency: string;
  income_type: string;
  expected_day?: number | null;
  is_active: boolean;
  updated_at?: string | null;
}

export interface Liability {
  liability_id: number;
  user_id: number;
  type: string;
  lender_name?: string | null;
  outstanding_principal: number;
  interest_rate: number;
  emi_amount: number;
  due_day: number;
  remaining_months?: number | null;
  prepayment_note?: string | null;
  status: string;
}

export interface Holding {
  holding_id: number;
  user_id: number;
  type: string;
  name: string;
  current_value: number;
  as_of_date: string;
  liquidity: string;
  is_emergency_reserve: boolean;
  source: string;
}

export interface FinancialSnapshot {
  is_sufficient: boolean;
  missing_items: string[];
  monthly_income: number;
  essential_expenses: number;
  discretionary_expenses: number;
  total_expenses: number;
  debt_payments: number;
  net_cash_flow: number;
  savings_rate: number;
  dti: number;
  dti_level: string;
  net_worth: number;
  emergency_coverage_months: number;
  is_stale: boolean;
  stale_reasons: string[];
}

export interface Goal {
  goal_id: number;
  user_id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  target_date: string;
  priority: string;
  liquidity_need: string;
  status: string;
}

export interface GoalProjection {
  goal_id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  target_date: string;
  months_left: number;
  progress_percent: number;
  planning_contribution: number;
  scenarios: { rate_percent: number; required_contribution: number }[];
  disclaimer: string;
}

// APIs
export async function fetchSnapshot(): Promise<FinancialSnapshot> {
  return apiRequest<FinancialSnapshot>('/snapshot');
}

export async function fetchTransactions(): Promise<Transaction[]> {
  return apiRequest<Transaction[]>('/transactions');
}

export async function createTransaction(data: Omit<Transaction, 'transaction_id' | 'user_id'>): Promise<{ transaction: Transaction; nudge?: { message: string } | null }> {
  return apiRequest('/transactions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function updateTransaction(txnId: number, data: Partial<Omit<Transaction, 'transaction_id' | 'user_id'>>): Promise<Transaction> {
  return apiRequest(`/transactions/${txnId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function fetchIncomeSources(): Promise<IncomeSource[]> {
  return apiRequest<IncomeSource[]>('/income-sources');
}

export async function createIncomeSource(data: Omit<IncomeSource, 'income_source_id' | 'user_id'>): Promise<IncomeSource> {
  return apiRequest('/income-sources', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function updateIncomeSource(sourceId: number, data: Partial<Omit<IncomeSource, 'income_source_id' | 'user_id'>>): Promise<IncomeSource> {
  return apiRequest(`/income-sources/${sourceId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function deleteIncomeSource(sourceId: number): Promise<void> {
  return apiRequest(`/income-sources/${sourceId}`, {
    method: 'DELETE',
  });
}

export async function fetchLiabilities(): Promise<Liability[]> {
  return apiRequest<Liability[]>('/liabilities');
}

export async function createLiability(data: Omit<Liability, 'liability_id' | 'user_id'>): Promise<Liability> {
  return apiRequest('/liabilities', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function updateLiability(liabilityId: number, data: Partial<Omit<Liability, 'liability_id' | 'user_id'>>): Promise<Liability> {
  return apiRequest(`/liabilities/${liabilityId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function fetchHoldings(): Promise<Holding[]> {
  return apiRequest<Holding[]>('/holdings');
}

export async function createHolding(data: Omit<Holding, 'holding_id' | 'user_id'>): Promise<Holding> {
  return apiRequest('/holdings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function updateHolding(holdingId: number, data: Partial<Omit<Holding, 'holding_id' | 'user_id'>>): Promise<Holding> {
  return apiRequest(`/holdings/${holdingId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function fetchGoals(): Promise<Goal[]> {
  return apiRequest<Goal[]>('/goals');
}

export async function createGoal(data: Omit<Goal, 'goal_id' | 'user_id'>): Promise<Goal> {
  return apiRequest('/goals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function addGoalSaving(goalId: number, amount: number): Promise<Goal> {
  return apiRequest(`/goals/${goalId}/add-saving`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount }),
  });
}

export async function fetchGoalProjection(goalId: number): Promise<GoalProjection> {
  return apiRequest(`/goals/${goalId}/projection`);
}
