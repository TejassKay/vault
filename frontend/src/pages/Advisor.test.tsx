import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Advisor } from './Advisor';
import * as advisorApi from '../api/advisor';

vi.mock('../api/advisor', () => ({
  fetchInvestmentCapacity: vi.fn(),
  fetchRiskProfile: vi.fn(),
  fetchRecommendations: vi.fn(),
  fetchRiskQuestionnaire: vi.fn(),
  generateRecommendations: vi.fn(),
  submitRiskProfile: vi.fn(),
  updateRecommendationStatus: vi.fn(),
}));

describe('Advisor Component (FR-21 to FR-26, FR-29, NFR-7)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders statutory decision support disclaimer banner (NFR-7)', async () => {
    vi.mocked(advisorApi.fetchInvestmentCapacity).mockResolvedValue({
      status: 'ok',
      capacity: 14625,
      capacity_if_clear: 14625,
      surplus: 35000,
      goal_contribution: 18750,
      emergency_top_up: 0,
      remaining: 16250,
      steps: [],
      reason_codes: [],
      missing_items: [],
      assumptions: [],
    });
    vi.mocked(advisorApi.fetchRiskProfile).mockResolvedValue({
      risk_profile_id: 1,
      user_id: 1,
      answers: {},
      score: 20,
      tolerance_level: 'moderate',
      capacity_level: 'medium',
      effective_level: 'moderate',
      assessed_at: '2026-11-14T00:00:00Z',
    });
    vi.mocked(advisorApi.fetchRecommendations).mockResolvedValue({
      recommendations: [
        {
          recommendation_id: 10,
          user_id: 1,
          priority_rank: 1,
          rec_type: 'INVEST_BY_CATEGORY',
          action: 'Deploy sustainable investment capacity of ₹14,625.00/month',
          reason: 'Based on your moderate risk profile...',
          assumptions: ['10% buffer retained'],
          risks: ['Market volatility'],
          alternatives: ['SIP in index funds'],
          review_trigger: 'Annual review',
          inputs_snapshot: {},
          engine_version: '1.0',
          explanation_text: 'Deploy your capacity across diversified categories.',
          explanation_source: 'template',
          status: 'proposed',
          created_at: '2026-11-14T00:00:00Z',
        },
      ],
      disclaimer: 'Vault provides general educational decision support based on the information you entered.',
    });

    render(
      <BrowserRouter>
        <Advisor />
      </BrowserRouter>
    );

    // Disclaimer check (NFR-7)
    expect(screen.getByText(/Decision Support Notice:/i)).toBeInTheDocument();
    expect(screen.getByText(/Vault provides general educational decision support/i)).toBeInTheDocument();

    // Capacity check (FR-21)
    await waitFor(() => {
      expect(screen.getByText(/Monthly Investment Capacity/i)).toBeInTheDocument();
      expect(screen.getByText(/Deploy sustainable investment capacity/i)).toBeInTheDocument();
    });
  });

  it('renders insufficient data warning when baseline data is missing (FR-29)', async () => {
    vi.mocked(advisorApi.fetchInvestmentCapacity).mockResolvedValue({
      status: 'insufficient_data',
      capacity: null,
      capacity_if_clear: null,
      surplus: null,
      goal_contribution: null,
      emergency_top_up: null,
      remaining: null,
      steps: [],
      reason_codes: [],
      missing_items: ['At least one income source', 'At least one month of expenses'],
      assumptions: [],
    });
    vi.mocked(advisorApi.fetchRiskProfile).mockResolvedValue(null);
    vi.mocked(advisorApi.fetchRecommendations).mockResolvedValue({
      recommendations: [],
      disclaimer: 'Vault provides general educational decision support.',
    });

    render(
      <BrowserRouter>
        <Advisor />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Insufficient Baseline Financial Data/i)).toBeInTheDocument();
      expect(screen.getByText(/At least one income source/i)).toBeInTheDocument();
      expect(screen.getByText(/At least one month of expenses/i)).toBeInTheDocument();
    });
  });
});
