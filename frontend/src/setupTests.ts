import '@testing-library/jest-dom';

// Provide global mock fetch for auth endpoint so unit tests resolve successfully
const originalFetch = globalThis.fetch;
globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
  if (url.includes('/auth/me')) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        user_id: 1,
        name: 'Tejas23',
        email: 'tejas23@vault.local',
        notification_pref: 'in_app',
        consent_given_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      }),
    } as unknown as Response;
  }
  if (url.includes('/dashboard/summary') || url.includes('/dashboard/timeline')) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        snapshot: {
          monthly_income: 85000,
          essential_expenses: 32000,
          discretionary_expenses: 8000,
          debt_payments: 10000,
          net_cash_flow: 35000,
          savings_rate: 41.18,
          dti: 11.76,
          net_worth: 270000,
          emergency_coverage_months: 6.19,
        },
        investment_capacity: 14625,
        investment_capacity_status: 'ok',
        top_recommendation: null,
        upcoming_obligations: [],
        asset_alerts: [],
        goals_progress: [],
        events: [],
      }),
    } as unknown as Response;
  }
  if (originalFetch) {
    return originalFetch(input, init);
  }
  return {
    ok: true,
    status: 200,
    json: async () => ({}),
  } as unknown as Response;
};
