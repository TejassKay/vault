import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Download, RefreshCw, Table2 } from 'lucide-react';
import { AnalyticsSummary, fetchAnalyticsSummary } from '../api/analytics';
import { fetchTransactions, Transaction } from '../api/finances';
import { Money, formatINR } from '../components/Money';
import { INSIGHTS_LABELS, getLabel } from '../lib/labels.js';

const PALETTE = {
  canvas: '#f8f7f4',
  surface: '#ffffff',
  border: '#e2e0d8',
  ink: '#1f2a26',
  muted: '#5b6760',
  green: '#1f5d3d',
  terracotta: '#b4532a',
  gold: '#b8934a',
};

// 8-step categorical scale from tints of green, ink, gold, and soft terracotta
const CATEGORY_SCALE = [
  '#1f5d3d',
  '#3e7357',
  '#67917b',
  '#1f2a26',
  '#4c5853',
  '#b8934a',
  '#cba866',
  '#c97a58',
];

const LIABILITY_SCALE = ['#b4532a', '#c66d48', '#d68968', '#e4a78b', '#8f3f1e'];

function getCurrentYYYYMM(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  return `${y}-${m}`;
}

function formatCompactINR(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (abs >= 10_000_000) {
    const cr = abs / 10_000_000;
    return `${sign}₹${Number.isInteger(cr) ? cr : cr.toFixed(1)}Cr`;
  }
  if (abs >= 100_000) {
    const l = abs / 100_000;
    return `${sign}₹${Number.isInteger(l) ? l : l.toFixed(1)}L`;
  }
  if (abs >= 1_000) {
    const k = abs / 1_000;
    return `${sign}₹${Number.isInteger(k) ? k : k.toFixed(1)}k`;
  }
  return `${sign}₹${Math.round(abs)}`;
}

function formatMonthLabel(ym: string): string {
  const parts = ym.split('-');
  if (parts.length !== 2) return ym;
  const year = Number(parts[0]);
  const monthIdx = Number(parts[1]) - 1;
  if (Number.isNaN(year) || Number.isNaN(monthIdx)) return ym;
  const d = new Date(year, monthIdx, 1);
  return d.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState<boolean>(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return false;
    }
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener?.('change', onChange);
    return () => mq.removeEventListener?.('change', onChange);
  }, []);

  return reduced;
}

const ChartCard: React.FC<{
  title: string;
  ariaLabel: string;
  subtitle?: string;
  className?: string;
  children: React.ReactNode;
}> = ({ title, ariaLabel, subtitle, className = '', children }) => (
  <section
    tabIndex={0}
    aria-label={ariaLabel}
    className={`bg-surface border border-border rounded p-5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink ${className}`}
  >
    <div className="flex items-baseline justify-between gap-2 mb-3">
      <h2 className="font-serif text-xl text-ink leading-snug">{title}</h2>
      {subtitle && <span className="text-xs text-muted-ink">{subtitle}</span>}
    </div>
    {children}
  </section>
);

export const Insights: React.FC = () => {
  const [selectedMonth, setSelectedMonth] = useState<string>(getCurrentYYYYMM);
  const [monthsWindow, setMonthsWindow] = useState<3 | 6 | 12>(6);
  const [viewAsTable, setViewAsTable] = useState<boolean>(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const prefersReducedMotion = usePrefersReducedMotion();
  const animDuration = prefersReducedMotion ? 0 : 250;

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsRes, txnsRes] = await Promise.all([
        fetchAnalyticsSummary(selectedMonth, monthsWindow),
        fetchTransactions().catch(() => [] as Transaction[]),
      ]);
      setSummary(analyticsRes);
      setTransactions(txnsRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load spending insights.');
    } finally {
      setLoading(false);
    }
  }, [selectedMonth, monthsWindow]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reset category filter when month changes
  useEffect(() => {
    setSelectedCategory(null);
  }, [selectedMonth]);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      if (t.type !== 'expense') return false;
      if (!t.txn_date.startsWith(selectedMonth)) return false;
      if (selectedCategory && t.category.toLowerCase() !== selectedCategory.toLowerCase()) {
        return false;
      }
      return true;
    });
  }, [transactions, selectedMonth, selectedCategory]);

  const handleDownloadCsv = () => {
    const header = ['Date', 'Category', 'Note', 'Amount (INR)'];
    const rows = filteredTransactions.map((t) => [
      t.txn_date,
      getLabel(t.category),
      (t.note || '').replace(/"/g, '""'),
      String(t.amount),
    ]);
    const csvContent = [
      header.join(','),
      ...rows.map((r) => r.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vault-expenses-${selectedMonth}${selectedCategory ? `-${selectedCategory.toLowerCase()}` : ''}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Pre-shaped chart arrays (only formatting / Number parsing from API values)
  const categoryData = useMemo(() => {
    if (!summary) return [];
    return summary.category_breakdown.items.map((item) => ({
      category: item.category,
      label: getLabel(item.category),
      amount: Number(item.amount),
      share_percent: Number(item.share_percent),
    }));
  }, [summary]);

  const monthlyData = useMemo(() => {
    if (!summary) return [];
    return summary.monthly_series.map((m) => ({
      month: m.month,
      label: formatMonthLabel(m.month),
      income: Number(m.income),
      expenses: Number(m.expenses),
      essential: Number(m.essential),
      discretionary: Number(m.discretionary),
      net: Number(m.net),
      debt_payments: Number(m.debt_payments),
    }));
  }, [summary]);

  const paceData = useMemo(() => {
    if (!summary) return [];
    const byDay = new Map<number, { day: number; current?: number; previous?: number }>();
    for (const pt of summary.spending_pace.previous_month) {
      byDay.set(pt.day, { day: pt.day, previous: Number(pt.cumulative) });
    }
    for (const pt of summary.spending_pace.current_month) {
      const existing = byDay.get(pt.day) || { day: pt.day };
      existing.current = Number(pt.cumulative);
      byDay.set(pt.day, existing);
    }
    return Array.from(byDay.values()).sort((a, b) => a.day - b.day);
  }, [summary]);

  const compareData = useMemo(() => {
    if (!summary) return [];
    return summary.compare.map((c) => ({
      category: c.category,
      label: getLabel(c.category),
      amount: Number(c.amount),
      previous: Number(c.previous),
      delta: Number(c.delta),
      delta_percent: c.delta_percent !== null ? Number(c.delta_percent) : null,
    }));
  }, [summary]);

  const holdingsData = useMemo(() => {
    if (!summary) return [];
    return summary.composition.holdings.items.map((h) => ({
      type: h.type,
      label: getLabel(h.type),
      value: Number(h.value),
      share_percent: Number(h.share_percent),
    }));
  }, [summary]);

  const liabilitiesData = useMemo(() => {
    if (!summary) return [];
    return summary.composition.liabilities.items.map((l) => ({
      type: l.type,
      label: getLabel(l.type),
      outstanding_principal: Number(l.outstanding_principal),
      share_percent: Number(l.share_percent),
    }));
  }, [summary]);

  const paceCaption = useMemo(() => {
    if (!summary) return '';
    const delta = Number(summary.spending_pace.delta_at_day);
    const day = summary.spending_pace.comparison_day;
    if (day <= 0) return '';
    if (delta > 0) {
      return `Ahead of last month by ${formatINR(delta)} by day ${day}`;
    }
    if (delta < 0) {
      return `Behind last month by ${formatINR(Math.abs(delta))} by day ${day}`;
    }
    return `Matching last month by day ${day}`;
  }, [summary]);

  return (
    <div className="space-y-6 bg-canvas text-ink">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="font-serif text-3xl text-ink tracking-tight">
            {INSIGHTS_LABELS.pageTitle}
          </h1>
          <p className="text-sm text-muted-ink mt-1">{INSIGHTS_LABELS.pageSubtitle}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Month picker */}
          <label className="flex items-center gap-2 text-xs text-muted-ink">
            <span>Month</span>
            <input
              type="month"
              aria-label="Select month"
              value={selectedMonth}
              onChange={(e) => {
                if (e.target.value) setSelectedMonth(e.target.value);
              }}
              className="bg-surface border border-border rounded px-2.5 py-1.5 text-sm font-mono text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink"
            />
          </label>

          {/* Period toggle: 3M / 6M / 12M */}
          <div
            role="group"
            aria-label="Period length"
            className="inline-flex bg-surface border border-border rounded p-0.5"
          >
            {([3, 6, 12] as const).map((period) => {
              const active = monthsWindow === period;
              return (
                <button
                  key={period}
                  type="button"
                  onClick={() => setMonthsWindow(period)}
                  aria-pressed={active}
                  className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${
                    prefersReducedMotion ? 'duration-0' : 'duration-200'
                  } ${
                    active
                      ? 'bg-ink text-canvas font-medium'
                      : 'text-muted-ink hover:text-ink'
                  }`}
                >
                  {period}M
                </button>
              );
            })}
          </div>

          {/* View as table switch */}
          <button
            type="button"
            role="switch"
            aria-checked={viewAsTable}
            onClick={() => setViewAsTable((v) => !v)}
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs border rounded transition-colors ${
              prefersReducedMotion ? 'duration-0' : 'duration-200'
            } ${
              viewAsTable
                ? 'bg-ink text-canvas border-ink'
                : 'bg-surface text-ink border-border hover:border-ink/40'
            }`}
          >
            <Table2 className="w-3.5 h-3.5" />
            <span>{INSIGHTS_LABELS.viewAsTable}</span>
          </button>
        </div>
      </div>

      {/* Loading Skeletons */}
      {loading && (
        <div
          aria-label="Loading spending insights"
          className="grid grid-cols-1 md:grid-cols-12 gap-4"
        >
          {[5, 7, 6, 6, 7, 5].map((span, idx) => (
            <div
              key={idx}
              className={`md:col-span-${span} bg-surface border border-border rounded p-5 h-72 ${
                prefersReducedMotion ? '' : 'animate-pulse'
              }`}
            >
              <div className="h-5 w-40 bg-border/60 rounded mb-4" />
              <div className="h-48 w-full bg-canvas rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div
          role="alert"
          className="bg-surface border border-liability rounded p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div>
            <h2 className="font-serif text-xl text-ink">{INSIGHTS_LABELS.errorTitle}</h2>
            <p className="text-sm text-muted-ink mt-1">{error}</p>
          </div>
          <button
            type="button"
            onClick={loadData}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-ink text-canvas rounded hover:bg-muted-ink"
          >
            <RefreshCw className="w-4 h-4" />
            {INSIGHTS_LABELS.retry}
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && summary && !summary.meta.has_data && (
        <div className="bg-surface border border-border rounded p-8 text-center space-y-3">
          <h2 className="font-serif text-2xl text-ink">{INSIGHTS_LABELS.emptyTitle}</h2>
          <p className="text-sm text-muted-ink max-w-md mx-auto">
            {INSIGHTS_LABELS.emptyDescription}
          </p>
          <div className="pt-2">
            <Link
              to="/finances"
              className="inline-flex items-center px-4 py-2 text-sm bg-growth text-canvas rounded hover:opacity-90"
            >
              {INSIGHTS_LABELS.emptyCta}
            </Link>
          </div>
        </div>
      )}

      {/* Bento Grid + Transaction Table */}
      {!loading && !error && summary && summary.meta.has_data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            {/* 1. Spending by category */}
            <ChartCard
              title={INSIGHTS_LABELS.charts.categoryBreakdown}
              subtitle={selectedMonth}
              ariaLabel={`${INSIGHTS_LABELS.charts.categoryBreakdown} for ${selectedMonth}, total ${formatINR(Number(summary.category_breakdown.total))}`}
              className="md:col-span-5"
            >
              {categoryData.length === 0 ? (
                <p className="text-sm text-muted-ink py-12 text-center">
                  No expenses recorded for {selectedMonth}.
                </p>
              ) : viewAsTable ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-ink">
                        <th scope="col" className="py-2 font-medium">Category</th>
                        <th scope="col" className="py-2 font-medium text-right">Amount</th>
                        <th scope="col" className="py-2 font-medium text-right">Share</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {categoryData.map((row) => (
                        <tr key={row.category}>
                          <td className="py-2 text-ink">{row.label}</td>
                          <td className="py-2 text-right">
                            <Money amount={row.amount} />
                          </td>
                          <td className="py-2 text-right font-mono tabular-nums text-muted-ink">
                            {row.share_percent.toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row items-center gap-4">
                  <div className="relative w-full sm:w-48 h-48 shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={categoryData}
                          dataKey="amount"
                          nameKey="label"
                          innerRadius={52}
                          outerRadius={76}
                          paddingAngle={1}
                          animationDuration={animDuration}
                          onClick={(entry) => {
                            if (entry && entry.category) {
                              setSelectedCategory((prev) =>
                                prev === entry.category ? null : entry.category
                              );
                            }
                          }}
                          className="cursor-pointer"
                        >
                          {categoryData.map((entry, idx) => (
                            <Cell
                              key={entry.category}
                              fill={CATEGORY_SCALE[idx % CATEGORY_SCALE.length]}
                              stroke={
                                selectedCategory === entry.category ? PALETTE.ink : PALETTE.surface
                              }
                              strokeWidth={selectedCategory === entry.category ? 2 : 1}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(val: number) => formatINR(val)}
                          contentStyle={{
                            backgroundColor: PALETTE.surface,
                            borderColor: PALETTE.border,
                            borderRadius: 3,
                            fontSize: 12,
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-[10px] uppercase tracking-wider text-muted-ink">
                        Total
                      </span>
                      <Money
                        amount={summary.category_breakdown.total}
                        className="text-sm font-medium text-ink"
                      />
                    </div>
                  </div>

                  <ul className="w-full space-y-1.5 text-xs">
                    {categoryData.map((item, idx) => {
                      const isSelected = selectedCategory === item.category;
                      return (
                        <li key={item.category}>
                          <button
                            type="button"
                            onClick={() =>
                              setSelectedCategory((prev) =>
                                prev === item.category ? null : item.category
                              )
                            }
                            className={`w-full flex items-center justify-between gap-2 px-2 py-1 rounded text-left transition-colors ${
                              isSelected ? 'bg-canvas ring-1 ring-ink' : 'hover:bg-canvas'
                            }`}
                          >
                            <span className="flex items-center gap-2 min-w-0">
                              <span
                                className="w-2.5 h-2.5 rounded-sm shrink-0"
                                style={{
                                  backgroundColor: CATEGORY_SCALE[idx % CATEGORY_SCALE.length],
                                }}
                              />
                              <span className="truncate text-ink">{item.label}</span>
                            </span>
                            <span className="flex items-center gap-2 shrink-0">
                              <Money amount={item.amount} className="text-ink" />
                              <span className="font-mono tabular-nums text-muted-ink w-12 text-right">
                                {item.share_percent.toFixed(1)}%
                              </span>
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
            </ChartCard>

            {/* 2. Income versus expenses */}
            <ChartCard
              title={INSIGHTS_LABELS.charts.incomeVsExpenses}
              subtitle={`${monthsWindow}M + selected`}
              ariaLabel={`${INSIGHTS_LABELS.charts.incomeVsExpenses} over ${monthlyData.length} months`}
              className="md:col-span-7"
            >
              {viewAsTable ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-ink">
                        <th scope="col" className="py-2 font-medium">Month</th>
                        <th scope="col" className="py-2 font-medium text-right">Income</th>
                        <th scope="col" className="py-2 font-medium text-right">Expenses</th>
                        <th scope="col" className="py-2 font-medium text-right">Net</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {monthlyData.map((row) => (
                        <tr key={row.month}>
                          <td className="py-2 font-mono text-ink">{row.month}</td>
                          <td className="py-2 text-right"><Money amount={row.income} /></td>
                          <td className="py-2 text-right"><Money amount={row.expenses} /></td>
                          <td className="py-2 text-right"><Money amount={row.net} showSign /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={monthlyData}>
                      <CartesianGrid stroke={PALETTE.border} strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tick={{ fill: PALETTE.muted, fontSize: 11 }} />
                      <YAxis
                        tickFormatter={formatCompactINR}
                        tick={{ fill: PALETTE.muted, fontSize: 11 }}
                        width={60}
                      />
                      <Tooltip
                        formatter={(val: number, name: string) => [formatINR(val), name]}
                        contentStyle={{
                          backgroundColor: PALETTE.surface,
                          borderColor: PALETTE.border,
                          borderRadius: 3,
                          fontSize: 12,
                        }}
                      />
                      <Bar
                        dataKey="income"
                        name="Income"
                        fill={PALETTE.green}
                        radius={[2, 2, 0, 0]}
                        animationDuration={animDuration}
                      />
                      <Bar
                        dataKey="expenses"
                        name="Expenses"
                        fill={PALETTE.gold}
                        radius={[2, 2, 0, 0]}
                        animationDuration={animDuration}
                      />
                      <Line
                        type="monotone"
                        dataKey="net"
                        name="Net"
                        stroke={PALETTE.ink}
                        strokeWidth={2}
                        dot={{ r: 3, fill: PALETTE.ink }}
                        animationDuration={animDuration}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              )}
            </ChartCard>

            {/* 3. Essential versus discretionary */}
            <ChartCard
              title={INSIGHTS_LABELS.charts.essentialVsDiscretionary}
              ariaLabel={`${INSIGHTS_LABELS.charts.essentialVsDiscretionary} breakdown by month`}
              className="md:col-span-6"
            >
              {viewAsTable ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-ink">
                        <th scope="col" className="py-2 font-medium">Month</th>
                        <th scope="col" className="py-2 font-medium text-right">Essential</th>
                        <th scope="col" className="py-2 font-medium text-right">Discretionary</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {monthlyData.map((row) => (
                        <tr key={row.month}>
                          <td className="py-2 font-mono text-ink">{row.month}</td>
                          <td className="py-2 text-right"><Money amount={row.essential} /></td>
                          <td className="py-2 text-right"><Money amount={row.discretionary} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={monthlyData} stackOffset="expand">
                      <CartesianGrid stroke={PALETTE.border} strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tick={{ fill: PALETTE.muted, fontSize: 11 }} />
                      <YAxis
                        tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
                        tick={{ fill: PALETTE.muted, fontSize: 11 }}
                        width={42}
                      />
                      <Tooltip
                        formatter={(val: number, name: string) => [formatINR(val), name]}
                        contentStyle={{
                          backgroundColor: PALETTE.surface,
                          borderColor: PALETTE.border,
                          borderRadius: 3,
                          fontSize: 12,
                        }}
                      />
                      <Bar
                        dataKey="essential"
                        name="Essential"
                        stackId="exp"
                        fill={PALETTE.green}
                        animationDuration={animDuration}
                      />
                      <Bar
                        dataKey="discretionary"
                        name="Discretionary"
                        stackId="exp"
                        fill={PALETTE.gold}
                        animationDuration={animDuration}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </ChartCard>

            {/* 4. Spending pace */}
            <ChartCard
              title={INSIGHTS_LABELS.charts.spendingPace}
              subtitle={paceCaption}
              ariaLabel={`${INSIGHTS_LABELS.charts.spendingPace}. ${paceCaption}`}
              className="md:col-span-6"
            >
              {viewAsTable ? (
                <div className="overflow-x-auto max-h-56">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-ink">
                        <th scope="col" className="py-2 font-medium">Day</th>
                        <th scope="col" className="py-2 font-medium text-right">Selected</th>
                        <th scope="col" className="py-2 font-medium text-right">Previous</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {paceData.map((row) => (
                        <tr key={row.day}>
                          <td className="py-1.5 font-mono text-ink">Day {row.day}</td>
                          <td className="py-1.5 text-right">
                            <Money amount={row.current ?? null} />
                          </td>
                          <td className="py-1.5 text-right">
                            <Money amount={row.previous ?? null} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={paceData}>
                      <CartesianGrid stroke={PALETTE.border} strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="day" tick={{ fill: PALETTE.muted, fontSize: 11 }} />
                      <YAxis
                        tickFormatter={formatCompactINR}
                        tick={{ fill: PALETTE.muted, fontSize: 11 }}
                        width={60}
                      />
                      <Tooltip
                        labelFormatter={(day) => `Day ${day}`}
                        formatter={(val: number, name: string) => [formatINR(val), name]}
                        contentStyle={{
                          backgroundColor: PALETTE.surface,
                          borderColor: PALETTE.border,
                          borderRadius: 3,
                          fontSize: 12,
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="previous"
                        name="Previous month"
                        stroke={PALETTE.muted}
                        strokeWidth={1.5}
                        dot={false}
                        animationDuration={animDuration}
                      />
                      <Line
                        type="monotone"
                        dataKey="current"
                        name="Selected month"
                        stroke={PALETTE.green}
                        strokeWidth={2}
                        dot={false}
                        animationDuration={animDuration}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </ChartCard>

            {/* 5. Category changes */}
            <ChartCard
              title={INSIGHTS_LABELS.charts.categoryChanges}
              subtitle="vs previous month"
              ariaLabel={`${INSIGHTS_LABELS.charts.categoryChanges} compared to previous month`}
              className="md:col-span-7"
            >
              {compareData.length === 0 ? (
                <p className="text-sm text-muted-ink py-12 text-center">
                  No category comparison available for {selectedMonth}.
                </p>
              ) : viewAsTable ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-ink">
                        <th scope="col" className="py-2 font-medium">Category</th>
                        <th scope="col" className="py-2 font-medium text-right">Current</th>
                        <th scope="col" className="py-2 font-medium text-right">Previous</th>
                        <th scope="col" className="py-2 font-medium text-right">Change</th>
                        <th scope="col" className="py-2 font-medium text-right">%</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {compareData.map((row) => (
                        <tr key={row.category}>
                          <td className="py-2 text-ink">{row.label}</td>
                          <td className="py-2 text-right"><Money amount={row.amount} /></td>
                          <td className="py-2 text-right"><Money amount={row.previous} /></td>
                          <td className="py-2 text-right"><Money amount={row.delta} showSign /></td>
                          <td className="py-2 text-right font-mono tabular-nums text-muted-ink">
                            {row.delta_percent !== null
                              ? `${row.delta_percent > 0 ? '+' : ''}${row.delta_percent.toFixed(1)}%`
                              : 'New'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={compareData} layout="vertical" margin={{ left: 16, right: 24 }}>
                      <CartesianGrid stroke={PALETTE.border} strokeDasharray="3 3" horizontal={false} />
                      <XAxis
                        type="number"
                        tickFormatter={formatCompactINR}
                        tick={{ fill: PALETTE.muted, fontSize: 11 }}
                      />
                      <YAxis
                        type="category"
                        dataKey="label"
                        tick={{ fill: PALETTE.ink, fontSize: 11 }}
                        width={96}
                      />
                      <ReferenceLine x={0} stroke={PALETTE.border} />
                      <Tooltip
                        formatter={(val: number, _name, props) => {
                          const pct = props?.payload?.delta_percent;
                          const pctText =
                            pct !== null && pct !== undefined
                              ? ` (${pct > 0 ? '+' : ''}${Number(pct).toFixed(1)}%)`
                              : ' (New)';
                          return [`${formatINR(val)}${pctText}`, 'Change'];
                        }}
                        contentStyle={{
                          backgroundColor: PALETTE.surface,
                          borderColor: PALETTE.border,
                          borderRadius: 3,
                          fontSize: 12,
                        }}
                      />
                      <Bar dataKey="delta" radius={[2, 2, 2, 2]} animationDuration={animDuration}>
                        {compareData.map((entry) => (
                          <Cell
                            key={entry.category}
                            fill={entry.delta > 0 ? PALETTE.terracotta : PALETTE.green}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </ChartCard>

            {/* 6. Net worth composition */}
            <ChartCard
              title={INSIGHTS_LABELS.charts.netWorthComposition}
              ariaLabel={`${INSIGHTS_LABELS.charts.netWorthComposition}: holdings ${formatINR(Number(summary.composition.holdings.total))}, liabilities ${formatINR(Number(summary.composition.liabilities.total))}`}
              className="md:col-span-5"
            >
              {viewAsTable ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xs font-medium text-muted-ink mb-1">
                      Holdings (<Money amount={summary.composition.holdings.total} />)
                    </h3>
                    <table className="w-full text-sm">
                      <tbody className="divide-y divide-border/60">
                        {holdingsData.map((h) => (
                          <tr key={h.type}>
                            <td className="py-1.5 text-ink">{h.label}</td>
                            <td className="py-1.5 text-right"><Money amount={h.value} /></td>
                            <td className="py-1.5 text-right font-mono tabular-nums text-muted-ink">
                              {h.share_percent.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div>
                    <h3 className="text-xs font-medium text-muted-ink mb-1">
                      Liabilities (<Money amount={summary.composition.liabilities.total} />)
                    </h3>
                    <table className="w-full text-sm">
                      <tbody className="divide-y divide-border/60">
                        {liabilitiesData.map((l) => (
                          <tr key={l.type}>
                            <td className="py-1.5 text-ink">{l.label}</td>
                            <td className="py-1.5 text-right">
                              <Money amount={l.outstanding_principal} />
                            </td>
                            <td className="py-1.5 text-right font-mono tabular-nums text-muted-ink">
                              {l.share_percent.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-muted-ink">Holdings</span>
                      <Money amount={summary.composition.holdings.total} className="text-ink font-medium" />
                    </div>
                    {holdingsData.length === 0 ? (
                      <p className="text-xs text-muted-ink py-8 text-center">No holdings</p>
                    ) : (
                      <div className="h-36 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={holdingsData}
                              dataKey="value"
                              nameKey="label"
                              innerRadius={32}
                              outerRadius={52}
                              animationDuration={animDuration}
                            >
                              {holdingsData.map((h, i) => (
                                <Cell
                                  key={h.type}
                                  fill={CATEGORY_SCALE[i % CATEGORY_SCALE.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip formatter={(val: number) => formatINR(val)} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    <ul className="space-y-1 text-xs mt-1">
                      {holdingsData.map((h, i) => (
                        <li key={h.type} className="flex items-center justify-between gap-1">
                          <span className="flex items-center gap-1.5 truncate">
                            <span
                              className="w-2 h-2 rounded-sm shrink-0"
                              style={{ backgroundColor: CATEGORY_SCALE[i % CATEGORY_SCALE.length] }}
                            />
                            <span className="truncate">{h.label}</span>
                          </span>
                          <Money amount={h.value} className="text-muted-ink" />
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-muted-ink">Liabilities</span>
                      <Money
                        amount={summary.composition.liabilities.total}
                        className="text-liability font-medium"
                      />
                    </div>
                    {liabilitiesData.length === 0 ? (
                      <p className="text-xs text-muted-ink py-8 text-center">No active debt</p>
                    ) : (
                      <div className="h-36 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={liabilitiesData}
                              dataKey="outstanding_principal"
                              nameKey="label"
                              innerRadius={32}
                              outerRadius={52}
                              animationDuration={animDuration}
                            >
                              {liabilitiesData.map((l, i) => (
                                <Cell
                                  key={l.type}
                                  fill={LIABILITY_SCALE[i % LIABILITY_SCALE.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip formatter={(val: number) => formatINR(val)} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    <ul className="space-y-1 text-xs mt-1">
                      {liabilitiesData.map((l, i) => (
                        <li key={l.type} className="flex items-center justify-between gap-1">
                          <span className="flex items-center gap-1.5 truncate">
                            <span
                              className="w-2 h-2 rounded-sm shrink-0"
                              style={{ backgroundColor: LIABILITY_SCALE[i % LIABILITY_SCALE.length] }}
                            />
                            <span className="truncate">{l.label}</span>
                          </span>
                          <Money amount={l.outstanding_principal} className="text-muted-ink" />
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </ChartCard>
          </div>

          {/* Filterable Transaction Table + CSV Export */}
          <section className="bg-surface border border-border rounded p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-serif text-xl text-ink">Transactions ({selectedMonth})</h2>
                {selectedCategory && (
                  <button
                    type="button"
                    onClick={() => setSelectedCategory(null)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-canvas border border-border rounded text-ink hover:border-ink"
                  >
                    <span>Category: {getLabel(selectedCategory)}</span>
                    <span aria-hidden="true">×</span>
                  </button>
                )}
              </div>
              <button
                type="button"
                onClick={handleDownloadCsv}
                disabled={filteredTransactions.length === 0}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs bg-surface border border-border rounded text-ink hover:border-ink disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                {INSIGHTS_LABELS.downloadCsv}
              </button>
            </div>

            {filteredTransactions.length === 0 ? (
              <p className="text-sm text-muted-ink py-6 text-center">
                No matching expense transactions for {selectedMonth}
                {selectedCategory ? ` in ${getLabel(selectedCategory)}` : ''}.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-ink">
                      <th scope="col" className="py-2 font-medium">Date</th>
                      <th scope="col" className="py-2 font-medium">Category</th>
                      <th scope="col" className="py-2 font-medium">Note</th>
                      <th scope="col" className="py-2 font-medium text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {filteredTransactions.map((t) => (
                      <tr key={t.transaction_id}>
                        <td className="py-2 font-mono text-xs text-muted-ink">{t.txn_date}</td>
                        <td className="py-2 text-ink">{getLabel(t.category)}</td>
                        <td className="py-2 text-muted-ink text-xs">{t.note || '—'}</td>
                        <td className="py-2 text-right">
                          <Money amount={t.amount} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default Insights;
