import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Clock,
  AlertTriangle,
  Receipt,
  Target,
  ArrowRight,
  Download,
  Trash2,
  RefreshCw,
  Sliders,
  CheckCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  DashboardResponse,
  TimelineEvent,
  deleteUserAccount,
  exportUserData,
  fetchDashboard,
  fetchTimeline,
  triggerDemoSeed,
} from '../api/dashboard';

function formatCurrency(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(val);
}

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'settings'>('overview');
  const [seeding, setSeeding] = useState<boolean>(false);
  const [seedSuccess, setSeedSuccess] = useState<string | null>(null);

  const loadAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dash, time] = await Promise.all([fetchDashboard(), fetchTimeline()]);
      setData(dash);
      setTimeline(time.events);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleSeed = async (scenario: 'A' | 'B') => {
    try {
      setSeeding(true);
      setSeedSuccess(null);
      const res = await triggerDemoSeed(scenario);
      setSeedSuccess(res.message);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo seed failed');
    } finally {
      setSeeding(false);
    }
  };

  const handleExport = async () => {
    try {
      const exportJson = await exportUserData();
      const blob = new Blob([JSON.stringify(exportJson, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vault_user_export_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const handleDelete = async () => {
    if (
      window.confirm(
        'Are you sure you want to delete your entire Vault account? All bills, appliances, transactions, liabilities, and goals will be permanently deleted.'
      )
    ) {
      try {
        await deleteUserAccount();
        alert('Your account and all associated data have been deleted.');
        window.location.reload();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Account deletion failed');
      }
    }
  };

  if (loading && !data) {
    return (
      <div className="p-12 text-center text-slate-500">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
        Loading unified dashboard...
      </div>
    );
  }

  const snap = data?.snapshot;
  const isStale = data?.freshness.is_stale;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Top Bar with Demo Scenario Switcher & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            Connected Overview
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            What you own, what you owe, and what you should do next
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Demo Scenario Switcher (Spec 6.6 & 7.4) */}
          <div className="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200">
            <span className="text-[11px] font-bold uppercase text-slate-500 px-2 flex items-center gap-1">
              <Sliders className="w-3.5 h-3.5" /> Scenario:
            </span>
            <button
              onClick={() => handleSeed('A')}
              disabled={seeding}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-white text-slate-700 shadow-xs hover:text-indigo-600 transition-colors disabled:opacity-50"
            >
              Seed A (₹45k)
            </button>
            <button
              onClick={() => handleSeed('B')}
              disabled={seeding}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-white text-slate-700 shadow-xs hover:text-indigo-600 transition-colors disabled:opacity-50 ml-1"
            >
              Seed B (₹2.6L)
            </button>
          </div>

          <button
            onClick={loadAll}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {seedSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2.5 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          {seedSuccess}
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Freshness Indicator Banner (FR-28) */}
      {isStale && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 text-xs text-amber-900 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Data Freshness Alert (FR-28): </span>
            Some financial figures may be outdated ({data?.freshness.stale_reasons.join(', ')}).
            Update transactions or holding balances to keep recommendations accurate.
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 transition-colors ${
            activeTab === 'overview'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Snapshot & Priorities
        </button>
        <button
          onClick={() => setActiveTab('timeline')}
          className={`pb-3 transition-colors flex items-center gap-1.5 ${
            activeTab === 'timeline'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          Timeline & Calendar ({timeline.length})
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`pb-3 transition-colors flex items-center gap-1.5 ${
            activeTab === 'settings'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Data & Privacy (FR-30)
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metric Tiles (FR-10, FR-18, FR-19, FR-20) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Net Cash Flow
              </span>
              <div className="text-2xl font-extrabold text-slate-900">
                {formatCurrency(snap?.net_cash_flow)}
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                Savings rate: <strong>{snap?.savings_rate}%</strong>
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Financial Net Worth
              </span>
              <div className="text-2xl font-extrabold text-slate-900">
                {formatCurrency(snap?.net_worth)}
              </div>
              <span className="text-xs text-slate-500 mt-1 block">Holdings minus liabilities</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Emergency Coverage
              </span>
              <div className="text-2xl font-extrabold text-slate-900">
                {snap?.emergency_coverage_months} mo
              </div>
              <span className="text-xs text-slate-500 mt-1 block">Safety target: 6.0 mo</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Investment Capacity
              </span>
              <div className="text-2xl font-extrabold text-indigo-600">
                {data?.investment_capacity_status === 'insufficient_data'
                  ? 'No Data'
                  : formatCurrency(data?.investment_capacity)}
              </div>
              <span className="text-xs text-slate-500 mt-1 block capitalize">
                Status: {data?.investment_capacity_status}
              </span>
            </div>
          </div>

          {/* Physical Assets Estimate Banner (FR-18: shown separately, never added to liquid net worth) */}
          {data?.physical_assets_estimate && data.physical_assets_estimate > 0 && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-slate-700">
                <Receipt className="w-4 h-4 text-indigo-500" />
                <span>
                  <strong>Estimated Physical Asset Value (FR-18):</strong>{' '}
                  {formatCurrency(data.physical_assets_estimate)}
                  <span className="text-slate-400 ml-1.5">
                    (Separately tracked possessions; never counted as liquid wealth)
                  </span>
                </span>
              </div>
              <Link to="/assets" className="text-indigo-600 font-semibold hover:underline">
                View Assets &rarr;
              </Link>
            </div>
          )}

          {/* Top Recommendation Highlight (FR-11) */}
          {data?.top_recommendation && (
            <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 text-[10px] uppercase font-extrabold px-2 py-0.5 rounded-full">
                    Top Priority Action #{data.top_recommendation.priority_rank}
                  </span>
                  <span className="text-xs text-slate-300">
                    {data.top_recommendation.rec_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mt-1">
                  {data.top_recommendation.action}
                </h3>
                <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                  {data.top_recommendation.reason}
                </p>
              </div>

              <Link
                to="/advisor"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg self-start md:self-center transition-colors flex-shrink-0"
              >
                Review in Advisor
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Upcoming Obligations (FR-11) */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-slate-500" />
                  Upcoming Obligations
                </h3>
                <button
                  onClick={() => setActiveTab('timeline')}
                  className="text-xs text-indigo-600 font-semibold hover:underline"
                >
                  View All &rarr;
                </button>
              </div>

              {data?.upcoming_obligations.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  No pending obligations in the near future.
                </p>
              ) : (
                <div className="space-y-2">
                  {data?.upcoming_obligations.map((ob) => (
                    <div
                      key={ob.id}
                      className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-bold text-slate-800 block">{ob.title}</span>
                        <span className="text-[11px] text-slate-500">
                          Due: {ob.due_date} • {ob.details}
                        </span>
                      </div>
                      {ob.amount && (
                        <span className="font-mono font-bold text-slate-900">
                          {formatCurrency(ob.amount)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Asset Alerts (FR-11) */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Asset & Warranty Alerts
                </h3>
                <Link to="/assets" className="text-xs text-indigo-600 font-semibold hover:underline">
                  Assets &rarr;
                </Link>
              </div>

              {data?.asset_alerts.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  All appliance warranties and services are up to date.
                </p>
              ) : (
                <div className="space-y-2">
                  {data?.asset_alerts.map((al, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-amber-50/60 border border-amber-200 rounded-xl text-xs flex items-center justify-between"
                    >
                      <div>
                        <span className="font-bold text-amber-950 block">
                          {al.brand} {al.product_name}
                        </span>
                        <span className="text-[11px] text-amber-800">{al.message}</span>
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-200 text-amber-900">
                        {al.days_remaining}d left
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Goal Progress Summary (FR-9, FR-11) */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Target className="w-4 h-4 text-emerald-600" />
                Active Savings Goals Progress
              </h3>
              <Link to="/goals" className="text-xs text-indigo-600 font-semibold hover:underline">
                Manage Goals &rarr;
              </Link>
            </div>

            {data?.goals_progress.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No active savings goals found.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data?.goals_progress.map((g) => (
                  <div key={g.goal_id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
                    <div className="flex items-center justify-between font-bold text-slate-800">
                      <span>{g.title}</span>
                      <span>{g.progress_percent}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{ width: `${Math.min(100, g.progress_percent)}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                      <span>Saved: {formatCurrency(g.saved_amount)}</span>
                      <span>Target: {formatCurrency(g.target_amount)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Timeline & Calendar (FR-12) */}
      {activeTab === 'timeline' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Unified Obligations Timeline (FR-12)</h2>
            <p className="text-xs text-slate-500">
              Chronological schedule of EMI payments, maintenance services, warranty expiries, and goal milestones
            </p>
          </div>

          {timeline.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No upcoming events scheduled.
            </div>
          ) : (
            <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-6">
              {timeline.map((ev) => {
                const urgencyColors = {
                  overdue: 'bg-rose-50 border-rose-300 text-rose-900',
                  high: 'bg-amber-50 border-amber-300 text-amber-900',
                  medium: 'bg-indigo-50 border-indigo-200 text-indigo-900',
                  low: 'bg-slate-50 border-slate-200 text-slate-800',
                };
                return (
                  <div key={ev.event_id} className="relative">
                    <div className="absolute -left-[31px] top-1.5 w-3 h-3 rounded-full bg-white border-2 border-indigo-600" />
                    <div className={`p-4 rounded-xl border ${urgencyColors[ev.urgency]} shadow-xs`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-bold text-sm">{ev.title}</span>
                        <span className="font-mono text-xs font-semibold">
                          Date: {ev.event_date}
                        </span>
                      </div>
                      <p className="text-xs mt-1 opacity-90">{ev.description}</p>
                      {ev.amount && (
                        <div className="mt-2 text-xs font-mono font-bold">
                          Obligation Amount: {formatCurrency(ev.amount)}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab: Data Export & Delete (FR-30) */}
      {activeTab === 'settings' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Data Management & Privacy (FR-30)</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              You own your data. Export everything as structured JSON or purge your account.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="border border-slate-200 rounded-xl p-5 flex flex-col justify-between">
              <div>
                <Download className="w-6 h-6 text-indigo-600 mb-2" />
                <h3 className="text-sm font-bold text-slate-800">Export All Records (JSON)</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                  Download a full export containing your user profile, appliances, services, bills,
                  transactions, income sources, liabilities, holdings, goals, and recommendations.
                </p>
              </div>
              <button
                onClick={handleExport}
                className="mt-4 py-2 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-lg flex items-center justify-center gap-2"
              >
                <Download className="w-3.5 h-3.5" />
                Export My Data (FR-30)
              </button>
            </div>

            <div className="border border-rose-200 bg-rose-50/40 rounded-xl p-5 flex flex-col justify-between">
              <div>
                <Trash2 className="w-6 h-6 text-rose-600 mb-2" />
                <h3 className="text-sm font-bold text-rose-950">Delete Account & Purge Data</h3>
                <p className="text-xs text-rose-800 mt-1 leading-relaxed">
                  Permanently erase your user account and all cascaded records from the Vault database.
                  This action is irreversible.
                </p>
              </div>
              <button
                onClick={handleDelete}
                className="mt-4 py-2 px-4 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center justify-center gap-2"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete My Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
