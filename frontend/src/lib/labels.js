/**
 * Plain-language mappings for internal codes, rule codes, statuses, and error messages.
 */

export const CODE_LABELS = {
  // Gate & reason codes
  EMERGENCY_FUND_LOW: 'Emergency Fund Low',
  HIGH_INTEREST_DEBT: 'High-Interest Debt Active',
  CASH_FLOW_NEGATIVE: 'Negative Cash Flow',
  NEGATIVE_CASH_FLOW: 'Negative Cash Flow',
  DATA_INSUFFICIENT: 'Insufficient Data',
  INCOME_IRREGULAR: 'Irregular Income',
  GOALS_UNDERFUNDED: 'Goals Underfunded',

  // Recommendation types
  EMERGENCY_FUND_BUILD: 'Top Up Emergency Fund',
  INVEST_BY_CATEGORY: 'Invest by Category',
  REVIEW_SCHEDULE: 'Review Financial Plan',

  // Risk profiles
  low: 'Conservative',
  moderate: 'Moderate',
  high: 'Aggressive Growth',

  // Statuses
  ok: 'Healthy',
  blocked: 'Paused (Safety First)',
  insufficient_data: 'More Data Needed',
  needs_review: 'Review Needed',
  parsed: 'Verified',
  pending: 'Processing',
  corrected: 'Updated',
  active: 'Active',
  closed: 'Closed',
  paid_off: 'Paid Off',
  done: 'Completed',
  dismissed: 'Dismissed',
  accepted: 'Accepted',
  rejected: 'Declined',
  edited: 'Customized',

  // Liquidity
  liquid: 'Emergency Reserve',
  semi_liquid: 'Investment',
  illiquid: 'Locked Asset',
};

/**
 * Convert any UPPER_SNAKE or internal code to a plain-language human label.
 * @param {string | null | undefined} code
 * @returns {string}
 */
export function getLabel(code) {
  if (!code) return '';
  const str = String(code).trim();
  if (CODE_LABELS[str]) return CODE_LABELS[str];
  if (CODE_LABELS[str.toLowerCase()]) return CODE_LABELS[str.toLowerCase()];

  // Convert UPPER_SNAKE or snake_case to Title Case
  return str
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Format API error messages into user-friendly text without internal IDs or stack traces.
 * @param {any} err
 * @returns {string}
 */
export function getFriendlyErrorMessage(err) {
  if (!err) return 'An unexpected error occurred. Please try again.';
  let msg = '';
  if (typeof err === 'string') {
    msg = err;
  } else if (err.detail) {
    msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
  } else if (err.message) {
    msg = err.message;
  } else {
    msg = String(err);
  }

  // Remove internal identifiers, tracebacks, or raw JSON
  msg = msg.replace(/\b(FR-\d+|NFR-\d+|UC-\d+)\b[:\s-]*/gi, '');
  if (msg.includes('Traceback') || msg.includes('Internal Server Error')) {
    return 'A system error occurred. Please try again later.';
  }
  return msg.trim() || 'An unexpected error occurred. Please try again.';
}

export const SNAPSHOT_INPUT_META = {
  dti: { label: 'DTI', format: 'percent' },
  savings_rate: { label: 'Savings rate', format: 'percent' },
  emergency_coverage_months: { label: 'Emergency coverage', format: 'months' },
  net_worth: { label: 'Net worth', format: 'currency' },
  monthly_income: { label: 'Monthly income', format: 'currency' },
  monthly_expenses: { label: 'Monthly expenses', format: 'currency' },
  net_cash_flow: { label: 'Net cash flow', format: 'currency' },
  total_assets: { label: 'Total holdings', format: 'currency' },
  total_holdings: { label: 'Total holdings', format: 'currency' },
  total_liabilities: { label: 'Total liabilities', format: 'currency' },
  monthly_emi: { label: 'Monthly EMI', format: 'currency' },
  total_emi: { label: 'Monthly EMI', format: 'currency' },
  liquid_reserves: { label: 'Emergency reserve', format: 'currency' },
  emergency_fund: { label: 'Emergency reserve', format: 'currency' },
  investment_capacity: { label: 'Investment capacity', format: 'currency' },
  capacity: { label: 'Investment capacity', format: 'currency' },
  surplus: { label: 'Monthly surplus', format: 'currency' },
  goal_contribution: { label: 'Goal contribution', format: 'currency' },
  dti_level: { label: 'DTI level', format: 'label' },
  effective_level: { label: 'Risk profile', format: 'label' },
  risk_level: { label: 'Risk profile', format: 'label' },
  risk_profile: { label: 'Risk profile', format: 'label' },
  status: { label: 'Status', format: 'label' },
};

const formatINRCurrency = (num) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(num);

/**
 * Format an advisor inputs_snapshot entry into a human-readable label and unit-aware value.
 * @param {string} key
 * @param {unknown} val
 * @returns {{ label: string, value: string }}
 */
export function formatSnapshotInput(key, val) {
  const normalizedKey = String(key).trim().toLowerCase();
  const meta = SNAPSHOT_INPUT_META[normalizedKey];
  const label = meta?.label || getLabel(key);

  if (val === null || val === undefined || val === '') {
    return { label, value: '—' };
  }

  let format = meta?.format;
  if (!format && typeof val === 'number') {
    if (normalizedKey === 'dti' || normalizedKey.endsWith('_rate') || normalizedKey.endsWith('_pct') || normalizedKey.endsWith('_percent')) {
      format = 'percent';
    } else if (normalizedKey.endsWith('_months')) {
      format = 'months';
    } else {
      format = 'currency';
    }
  }

  if (typeof val === 'number' && !Number.isNaN(val)) {
    if (format === 'percent') {
      return { label, value: `${val.toFixed(2)}%` };
    }
    if (format === 'months') {
      return { label, value: `${val.toFixed(2)} months` };
    }
    if (format === 'currency') {
      return { label, value: formatINRCurrency(val) };
    }
  }

  if (format === 'label') {
    return { label, value: getLabel(String(val)) };
  }

  return { label, value: String(val) };
}
