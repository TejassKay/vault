import { apiRequest } from './client';

export interface CategoryBreakdownItem {
  category: string;
  amount: string | number;
  share_percent: string | number;
}

export interface CategoryBreakdown {
  items: CategoryBreakdownItem[];
  total: string | number;
}

export interface MonthlySeriesItem {
  month: string;
  income: string | number;
  expenses: string | number;
  essential: string | number;
  discretionary: string | number;
  net: string | number;
  debt_payments: string | number;
}

export interface CategoryTrendMonth {
  month: string;
  totals: Record<string, string | number>;
}

export interface CategoryTrend {
  categories: string[];
  series: CategoryTrendMonth[];
}

export interface PacePoint {
  day: number;
  cumulative: string | number;
}

export interface SpendingPace {
  current_month: PacePoint[];
  previous_month: PacePoint[];
  comparison_day: number;
  delta_at_day: string | number;
}

export interface CategoryCompareItem {
  category: string;
  amount: string | number;
  previous: string | number;
  delta: string | number;
  delta_percent: string | number | null;
}

export interface HoldingCompositionItem {
  type: string;
  value: string | number;
  share_percent: string | number;
}

export interface LiabilityCompositionItem {
  type: string;
  outstanding_principal: string | number;
  share_percent: string | number;
}

export interface CompositionSummary {
  holdings: {
    items: HoldingCompositionItem[];
    total: string | number;
  };
  liabilities: {
    items: LiabilityCompositionItem[];
    total: string | number;
  };
}

export interface AnalyticsMeta {
  generated_at: string;
  months_available: number;
  has_data: boolean;
}

export interface AnalyticsSummary {
  month: string;
  months: number;
  category_breakdown: CategoryBreakdown;
  monthly_series: MonthlySeriesItem[];
  category_trend: CategoryTrend;
  spending_pace: SpendingPace;
  compare: CategoryCompareItem[];
  composition: CompositionSummary;
  meta: AnalyticsMeta;
}

export async function fetchAnalyticsSummary(
  month?: string,
  months: 3 | 6 | 12 = 6
): Promise<AnalyticsSummary> {
  const params = new URLSearchParams();
  if (month) {
    params.set('month', month);
  }
  params.set('months', String(months));
  return apiRequest<AnalyticsSummary>(`/analytics/summary?${params.toString()}`);
}
