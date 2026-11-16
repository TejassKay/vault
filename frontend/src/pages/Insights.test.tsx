import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Insights } from './Insights';
import * as analyticsApi from '../api/analytics';
import * as financesApi from '../api/finances';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

vi.mock('../api/analytics', () => ({
  fetchAnalyticsSummary: vi.fn(),
}));

vi.mock('../api/finances', () => ({
  fetchTransactions: vi.fn(),
}));

describe('Insights Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders key figures and swaps charts for accessible tables when View as table is toggled', async () => {
    vi.mocked(analyticsApi.fetchAnalyticsSummary).mockResolvedValue({
      month: '2026-11',
      months: 6,
      category_breakdown: {
        items: [
          { category: 'Rent', amount: '25000.00', share_percent: '50.00' },
          { category: 'Groceries', amount: '15000.00', share_percent: '30.00' },
          { category: 'Shopping', amount: '10000.00', share_percent: '20.00' },
        ],
        total: '50000.00',
      },
      monthly_series: [
        {
          month: '2026-10',
          income: '120000.00',
          expenses: '68000.00',
          essential: '48000.00',
          discretionary: '20000.00',
          net: '52000.00',
          debt_payments: '12000.00',
        },
        {
          month: '2026-11',
          income: '120000.00',
          expenses: '50000.00',
          essential: '40000.00',
          discretionary: '10000.00',
          net: '70000.00',
          debt_payments: '12000.00',
        },
      ],
      category_trend: {
        categories: ['Rent', 'Groceries', 'Shopping'],
        series: [
          { month: '2026-10', totals: { Rent: '25000.00', Groceries: '15000.00', Shopping: '8000.00' } },
          { month: '2026-11', totals: { Rent: '25000.00', Groceries: '15000.00', Shopping: '10000.00' } },
        ],
      },
      spending_pace: {
        current_month: [
          { day: 1, cumulative: '25000.00' },
          { day: 2, cumulative: '30000.00' },
        ],
        previous_month: [
          { day: 1, cumulative: '25000.00' },
          { day: 2, cumulative: '25000.00' },
        ],
        comparison_day: 2,
        delta_at_day: '5000.00',
      },
      compare: [
        {
          category: 'Shopping',
          amount: '10000.00',
          previous: '8000.00',
          delta: '2000.00',
          delta_percent: '25.00',
        },
      ],
      composition: {
        holdings: {
          items: [{ type: 'bank_savings', value: '450000.00', share_percent: '100.00' }],
          total: '450000.00',
        },
        liabilities: {
          items: [{ type: 'personal', outstanding_principal: '120000.00', share_percent: '100.00' }],
          total: '120000.00',
        },
      },
      meta: {
        generated_at: '2026-11-14T10:00:00Z',
        months_available: 4,
        has_data: true,
      },
    });

    vi.mocked(financesApi.fetchTransactions).mockResolvedValue([
      {
        transaction_id: 1,
        user_id: 1,
        type: 'expense',
        amount: 25000,
        category: 'Rent',
        txn_date: '2026-11-01',
        note: 'Monthly rent',
        is_recurring: true,
      },
    ]);

    render(
      <BrowserRouter>
        <Insights />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Spending Insights')).toBeInTheDocument();
      expect(screen.getByText('Spending by category')).toBeInTheDocument();
    });

    expect(screen.getByText(/Ahead of last month by ₹5,000 by day 2/i)).toBeInTheDocument();
    expect(screen.getByText('Bank Savings')).toBeInTheDocument();
    expect(screen.getByText('Personal Loan')).toBeInTheDocument();
    expect(screen.getAllByText('₹4,50,000').length).toBeGreaterThanOrEqual(1);

    // Toggle "View as table"
    const tableSwitch = screen.getByRole('switch', { name: /View as table/i });
    fireEvent.click(tableSwitch);
    expect(tableSwitch).toHaveAttribute('aria-checked', 'true');

    // Accessible tables should render with exact figures
    const tables = screen.getAllByRole('table');
    expect(tables.length).toBeGreaterThanOrEqual(6);
    expect(screen.getByText('₹68,000')).toBeInTheDocument();
    expect(screen.getByText('+25.0%')).toBeInTheDocument();
  });

  it('renders empty state with link to Finances when has_data is false', async () => {
    vi.mocked(analyticsApi.fetchAnalyticsSummary).mockResolvedValue({
      month: '2026-11',
      months: 6,
      category_breakdown: { items: [], total: '0.00' },
      monthly_series: [],
      category_trend: { categories: [], series: [] },
      spending_pace: {
        current_month: [],
        previous_month: [],
        comparison_day: 0,
        delta_at_day: '0.00',
      },
      compare: [],
      composition: {
        holdings: { items: [], total: '0.00' },
        liabilities: { items: [], total: '0.00' },
      },
      meta: {
        generated_at: '2026-11-14T10:00:00Z',
        months_available: 0,
        has_data: false,
      },
    });
    vi.mocked(financesApi.fetchTransactions).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Insights />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No financial activity yet')).toBeInTheDocument();
    });

    const financesLink = screen.getByRole('link', { name: /Go to Finances/i });
    expect(financesLink).toHaveAttribute('href', '/finances');
  });
});
