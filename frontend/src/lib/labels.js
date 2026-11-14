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
  blocked: 'Safety Gate Active',
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
