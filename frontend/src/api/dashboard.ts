import { apiRequest } from './client';
import { FinancialSnapshot } from './finances';

export interface DashboardObligation {
  id: string;
  title: string;
  due_date: string;
  amount: number | null;
  category: string;
  status: string;
  details?: string | null;
}

export interface DashboardAssetAlert {
  appliance_id: number;
  product_name: string;
  brand?: string | null;
  alert_type: string;
  due_date: string;
  days_remaining: number;
  message: string;
}

export interface DashboardGoalSummary {
  goal_id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  progress_percent: number;
  target_date: string;
  months_left: number;
  planning_contribution: number;
}

export interface DashboardResponse {
  snapshot: FinancialSnapshot;
  investment_capacity: number | null;
  investment_capacity_status: string;
  top_recommendation?: {
    recommendation_id?: number;
    priority_rank: number;
    rec_type: string;
    action: string;
    reason: string;
    status: string;
    explanation_text?: string | null;
    explanation_source?: string | null;
  } | null;
  upcoming_obligations: DashboardObligation[];
  asset_alerts: DashboardAssetAlert[];
  goals_progress: DashboardGoalSummary[];
  physical_assets_estimate: number;
  freshness: {
    is_stale: boolean;
    stale_reasons: string[];
    evaluated_at: string;
  };
}

export interface TimelineEvent {
  event_id: string;
  title: string;
  event_date: string;
  event_type: 'emi' | 'service' | 'warranty' | 'goal' | 'bill';
  amount: number | null;
  urgency: 'low' | 'medium' | 'high' | 'overdue';
  description: string;
  meta: Record<string, unknown>;
}

export interface TimelineResponse {
  events: TimelineEvent[];
  today: string;
}

export interface DemoSeedResponse {
  message: string;
  scenario: string;
  user_email: string;
  user_id: number;
}

export async function fetchDashboard(): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>('/dashboard');
}

export async function fetchTimeline(): Promise<TimelineResponse> {
  return apiRequest<TimelineResponse>('/timeline');
}

export async function triggerDemoSeed(scenario: 'A' | 'B'): Promise<DemoSeedResponse> {
  return apiRequest<DemoSeedResponse>('/demo/seed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  });
}

export async function exportUserData(): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>('/me/export');
}

export async function deleteUserAccount(): Promise<void> {
  await apiRequest<void>('/me', {
    method: 'DELETE',
  });
}
