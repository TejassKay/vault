import { apiRequest } from './client';

export interface QuestionOption {
  text: string;
  score: number;
}

export interface RiskQuestion {
  id: string;
  text: string;
  options: QuestionOption[];
}

export interface RiskQuestionnaireResponse {
  questions: RiskQuestion[];
}

export interface RiskProfile {
  risk_profile_id: number;
  user_id: number;
  answers: Record<string, number>;
  score: number;
  tolerance_level: 'conservative' | 'moderate' | 'aggressive';
  capacity_level: 'low' | 'medium' | 'high';
  effective_level: 'conservative' | 'moderate' | 'aggressive';
  assessed_at: string;
}

export interface CapacityStep {
  step_number: number;
  name: string;
  value: number | null;
  description: string;
}

export interface InvestmentCapacity {
  status: 'ok' | 'blocked' | 'insufficient_data';
  capacity: number | null;
  capacity_if_clear: number | null;
  surplus: number | null;
  goal_contribution: number | null;
  emergency_top_up: number | null;
  remaining: number | null;
  steps: CapacityStep[];
  reason_codes: string[];
  missing_items: string[];
  assumptions: string[];
}

export interface Recommendation {
  recommendation_id: number;
  user_id: number;
  priority_rank: number;
  rec_type: string;
  action: string;
  reason: string;
  assumptions: string[] | null;
  risks: string[] | null;
  alternatives: string[] | null;
  review_trigger: string | null;
  inputs_snapshot: Record<string, unknown>;
  engine_version: string;
  explanation_text: string | null;
  explanation_source: 'llm' | 'template' | null;
  status: 'proposed' | 'accepted' | 'edited' | 'rejected';
  created_at: string;
  decided_at?: string | null;
}

export interface RecommendationListResponse {
  recommendations: Recommendation[];
  disclaimer: string;
}

export async function fetchRiskQuestionnaire(): Promise<RiskQuestionnaireResponse> {
  return apiRequest<RiskQuestionnaireResponse>('/risk-questionnaire');
}

export async function fetchRiskProfile(): Promise<RiskProfile | null> {
  return apiRequest<RiskProfile | null>('/risk-profile');
}

export async function submitRiskProfile(answers: Record<string, number>): Promise<RiskProfile> {
  return apiRequest<RiskProfile>('/risk-profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  });
}

export async function fetchInvestmentCapacity(): Promise<InvestmentCapacity> {
  return apiRequest<InvestmentCapacity>('/investment-capacity');
}

export async function generateRecommendations(): Promise<RecommendationListResponse> {
  return apiRequest<RecommendationListResponse>('/recommendations/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function fetchRecommendations(): Promise<RecommendationListResponse> {
  return apiRequest<RecommendationListResponse>('/recommendations');
}

export async function updateRecommendationStatus(
  id: number,
  status: 'proposed' | 'accepted' | 'edited' | 'rejected'
): Promise<Recommendation> {
  return apiRequest<Recommendation>(`/recommendations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
}
