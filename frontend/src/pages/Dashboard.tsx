import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Clock,
  AlertTriangle,
  Receipt,
  Target,
  Download,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  DashboardResponse,
  TimelineEvent,
  deleteUserAccount,
  exportUserData,
  fetchDashboard,
  fetchTimeline,
} from '../api/dashboard';
import { fetchInvestmentCapacity, InvestmentCapacity } from '../api/advisor';
import Money from '../components/Money';
import Card from '../components/Card';
import StatusPill from '../components/StatusPill';
import InvestmentCapacityBlock from '../components/InvestmentCapacityBlock';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [capacityData, setCapacityData] = useState<InvestmentCapacity | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'settings'>('overview');

  const loadAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dash, time, cap] = await Promise.all([
        fetchDashboard(),
        fetchTimeline(),
        fetchInvestmentCapacity().catch(() => null),
      ]);
      setData(dash);
      setTimeline(time.events);
      setCapacityData(cap);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

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
      <div className="p-16 text-center text-muted-ink">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-3 text-ink" />
        <span className="font-mono text-xs tracking-wider uppercase">Loading ledger records...</span>
      </div>
    );
  }

  const snap = data?.snapshot;
  const isStale = data?.freshness.is_stale;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Top Ledger Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gold/60 pb-4">
        <div>
          <h1 className="text-3xl font-serif text-ink tracking-tight">Financial Ledger</h1>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Archival record of holdings, liabilities, physical assets, and verified advisory guidance
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={loadAll}
            className="p-2 border border-border rounded-sm hover:border-ink text-ink bg-surface transition-colors"
            title="Refresh"
            aria-label="Refresh data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-surface border border-liability text-liability p-4 rounded-sm text-xs font-sans">
          {error}
        </div>
      )}

      {/* Freshness Indicator Banner (FR-28) */}
      {isStale && (
        <div className="bg-surface border-l-4 border-gold border border-border p-3.5 text-xs text-ink flex items-start gap-2.5 rounded-sm">
          <AlertTriangle className="w-4 h-4 text-liability flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-ink">Stale Data Warning: </span>
            Some financial figures may be outdated ({data?.freshness.stale_reasons.join(', ')}).
            Update transactions or holding balances to keep recommendations accurate.
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-border gap-6 text-xs font-mono tracking-wide uppercase">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-2.5 transition-colors ${
            activeTab === 'overview'
              ? 'border-b-2 border-ink text-ink font-semibold'
              : 'text-muted-ink hover:text-ink'
          }`}
        >
          Ledger Overview
        </button>
        <button
          onClick={() => setActiveTab('timeline')}
          className={`pb-2.5 transition-colors flex items-center gap-1.5 ${
            activeTab === 'timeline'
              ? 'border-b-2 border-ink text-ink font-semibold'
              : 'text-muted-ink hover:text-ink'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          Timeline & Calendar ({timeline.length})
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`pb-2.5 transition-colors flex items-center gap-1.5 ${
            activeTab === 'settings'
              ? 'border-b-2 border-ink text-ink font-semibold'
              : 'text-muted-ink hover:text-ink'
          }`}
        >
          Archival Data & Privacy
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Asymmetric Bento Grid: Left 2 cols for Financials, Right 1 col for Tall Timeline */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Columns: Investment Capacity (largest block) + Smaller Snapshot Blocks */}
            <div className="lg:col-span-2 space-y-6">
              {/* Largest High-Contrast Block: Investment Capacity (ink bg, canvas text) */}
              <InvestmentCapacityBlock
                status={capacityData?.status || data?.investment_capacity_status || 'insufficient_data'}
                capacity={capacityData?.capacity ?? data?.investment_capacity ?? null}
                capacityIfClear={capacityData?.capacity_if_clear}
                steps={capacityData?.steps || []}
                missingItems={capacityData?.missing_items || []}
                reasonCodes={capacityData?.reason_codes || []}
              />

              {/* Smaller blocks for Net Worth, Cash Flow, Emergency Coverage */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card className="flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-mono tracking-wider uppercase text-muted-ink block mb-1">
                      Financial Net Worth
                    </span>
                    <div className="text-2xl font-mono tabular-nums font-semibold text-ink">
                      <Money amount={snap?.net_worth} />
                    </div>
                  </div>
                  <span className="text-[11px] font-sans text-muted-ink mt-3 pt-2 border-t border-border block">
                    Holdings minus liabilities
                  </span>
                </Card>

                <Card className="flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-mono tracking-wider uppercase text-muted-ink block mb-1">
                      Net Cash Flow
                    </span>
                    <div className="text-2xl font-mono tabular-nums font-semibold text-ink">
                      <Money amount={snap?.net_cash_flow} showSign />
                    </div>
                  </div>
                  <div className="text-[11px] font-sans text-muted-ink mt-3 pt-2 border-t border-border flex items-center justify-between">
                    <span>Savings rate</span>
                    <span className="font-mono text-ink font-semibold">{snap?.savings_rate}%</span>
                  </div>
                </Card>

                <Card className="flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-mono tracking-wider uppercase text-muted-ink block mb-1">
                      Emergency Coverage
                    </span>
                    <div className="text-2xl font-mono tabular-nums font-semibold text-ink">
                      {snap?.emergency_coverage_months ?? '—'} <span className="text-sm font-sans font-normal text-muted-ink">mo</span>
                    </div>
                  </div>
                  <div className="text-[11px] font-sans text-muted-ink mt-3 pt-2 border-t border-border flex items-center justify-between">
                    {snap?.emergency_coverage_months !== undefined && snap.emergency_coverage_months < 6 ? (
                      <>
                        <span className="text-liability font-medium">Emergency Fund Low</span>
                        <span className="font-mono text-liability font-semibold">Target 6.0 mo</span>
                      </>
                    ) : (
                      <>
                        <span>Safety target</span>
                        <span className="font-mono text-ink font-semibold">6.0 mo</span>
                      </>
                    )}
                  </div>
                </Card>
              </div>

              {/* Top Recommendation Highlight (FR-11) */}
              {data?.top_recommendation && (
                <Card className="border border-gold/70 bg-surface">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <StatusPill
                          label={`Priority #${data.top_recommendation.priority_rank}`}
                          variant="gold"
                        />
                        <span className="text-xs font-mono text-muted-ink">
                          {data.top_recommendation.rec_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <h3 className="text-lg font-serif text-ink mt-1">
                        {data.top_recommendation.action}
                      </h3>
                      <p className="text-xs font-sans text-muted-ink leading-relaxed">
                        {data.top_recommendation.reason}
                      </p>
                    </div>

                    <Link
                      to="/advisor"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-ink text-canvas hover:bg-muted-ink text-xs font-mono rounded-sm self-start transition-colors flex-shrink-0"
                    >
                      Advisor &rarr;
                    </Link>
                  </div>
                </Card>
              )}

              {/* Physical Assets Estimate Banner */}
              {data?.physical_assets_estimate && data.physical_assets_estimate > 0 && (
                <Card className="bg-canvas border border-border py-3 px-4 flex items-center justify-between text-xs font-sans">
                  <div className="flex items-center gap-2.5 text-ink">
                    <Receipt className="w-4 h-4 text-muted-ink" />
                    <span>
                      <strong className="font-medium">Estimated Physical Asset Value:</strong>{' '}
                      <Money amount={data.physical_assets_estimate} className="font-semibold text-ink" />
                      <span className="text-muted-ink ml-1.5">
                        (Separately tracked possessions; never counted as liquid wealth)
                      </span>
                    </span>
                  </div>
                  <Link to="/assets" className="text-ink font-mono hover:underline flex items-center gap-1">
                    Index &rarr;
                  </Link>
                </Card>
              )}

              {/* Goal Progress Summary (FR-9, FR-11) */}
              <Card className="space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h3 className="text-sm font-serif text-ink flex items-center gap-1.5">
                    <Target className="w-4 h-4 text-growth" />
                    Active Savings Goals
                  </h3>
                  <Link to="/goals" className="text-xs font-mono text-muted-ink hover:text-ink">
                    Manage &rarr;
                  </Link>
                </div>

                {data?.goals_progress.length === 0 ? (
                  <p className="text-xs font-sans text-muted-ink py-4 text-center">No active savings goals found.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {data?.goals_progress.map((g) => (
                      <div key={g.goal_id} className="p-3 bg-canvas rounded-sm border border-border space-y-2 text-xs">
                        <div className="flex items-center justify-between font-sans font-medium text-ink">
                          <span>{g.title}</span>
                          <span className="font-mono text-xs">{g.progress_percent}%</span>
                        </div>
                        <div className="w-full bg-surface border border-border rounded-sm h-2 overflow-hidden">
                          <div
                            className="bg-growth h-full transition-all"
                            style={{
                              width: `${Math.min(100, g.progress_percent)}%`,
                              minWidth: g.progress_percent > 0 ? '6px' : undefined,
                            }}
                          />
                        </div>
                        <div className="flex items-center justify-between text-[11px] font-mono text-muted-ink pt-1">
                          <span>Saved: <Money amount={g.saved_amount} /></span>
                          <span>Target: <Money amount={g.target_amount} /></span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            {/* Right Column: Tall Vertical Timeline Column (EMIs, warranty expiries, service dates) */}
            <div className="space-y-6">
              <Card className="h-full flex flex-col">
                <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
                  <div>
                    <h3 className="text-base font-serif text-ink flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-muted-ink" />
                      Ledger Timeline
                    </h3>
                    <span className="text-[11px] font-sans text-muted-ink">Upcoming EMIs, warranties & services</span>
                  </div>
                  <button
                    onClick={() => setActiveTab('timeline')}
                    className="text-xs font-mono text-muted-ink hover:text-ink"
                  >
                    All ({timeline.length})
                  </button>
                </div>

                {/* Timeline Events List */}
                <div className="flex-1 space-y-3 overflow-y-auto max-h-[820px] pr-1">
                  {timeline.length === 0 ? (
                    <p className="text-xs font-sans text-muted-ink py-8 text-center">
                      No upcoming obligations scheduled.
                    </p>
                  ) : (
                    timeline.slice(0, 10).map((ev) => {
                      const isOverdueOrHigh = ev.urgency === 'overdue' || ev.urgency === 'high';
                      return (
                        <div
                          key={ev.event_id}
                          className={`p-3 rounded-sm border text-xs space-y-1.5 transition-colors ${
                            isOverdueOrHigh
                              ? 'bg-liability/5 border-liability/30'
                              : 'bg-canvas border-border'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-medium text-ink font-sans line-clamp-1">
                              {ev.title}
                            </span>
                            <span className="font-mono text-[11px] text-muted-ink whitespace-nowrap">
                              {ev.event_date}
                            </span>
                          </div>

                          <p className="text-[11px] font-sans text-muted-ink line-clamp-2">
                            {ev.description}
                          </p>

                          <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[11px]">
                            <StatusPill
                              label={ev.event_type}
                              variant={isOverdueOrHigh ? 'liability' : 'neutral'}
                            />
                            {ev.amount !== null && ev.amount !== undefined && (
                              <div className="font-mono tabular-nums text-right font-medium text-ink">
                                <Money amount={ev.amount} />
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* Asset Alerts section inside timeline column */}
                {data?.asset_alerts && data.asset_alerts.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-border space-y-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                      Expiring Appliance Alerts
                    </span>
                    {data.asset_alerts.map((al, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 bg-liability/5 border border-liability/30 rounded-sm text-xs flex items-center justify-between"
                      >
                        <div className="pr-2">
                          <span className="font-medium text-ink block font-sans">
                            {al.brand} {al.product_name}
                          </span>
                          <span className="text-[11px] text-muted-ink font-sans">{al.message}</span>
                        </div>
                        <StatusPill
                          label={`${al.days_remaining}D`}
                          variant="liability"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Full Timeline & Calendar */}
      {activeTab === 'timeline' && (
        <Card className="space-y-4">
          <div className="border-b border-border pb-3">
            <h2 className="text-xl font-serif text-ink">Chronological Ledger Timeline</h2>
            <p className="text-xs font-sans text-muted-ink">
              Structured schedule of EMI obligations, appliance services, warranty expirations, and savings milestones
            </p>
          </div>

          {timeline.length === 0 ? (
            <div className="text-center py-12 text-muted-ink text-xs font-mono">
              No upcoming events scheduled.
            </div>
          ) : (
            <div className="relative border-l border-border ml-4 pl-6 space-y-6">
              {timeline.map((ev) => {
                const isUrgent = ev.urgency === 'overdue' || ev.urgency === 'high';
                return (
                  <div key={ev.event_id} className="relative">
                    <div
                      className={`absolute -left-[30px] top-1.5 w-2.5 h-2.5 rounded-full ${
                        isUrgent ? 'bg-liability' : 'bg-ink'
                      }`}
                    />
                    <div className="p-4 rounded-sm border border-border bg-surface">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium font-sans text-sm text-ink">{ev.title}</span>
                        <span className="font-mono text-xs text-muted-ink">
                          Date: {ev.event_date}
                        </span>
                      </div>
                      <p className="text-xs font-sans text-muted-ink mt-1">{ev.description}</p>
                      <div className="mt-3 flex items-center justify-between pt-2 border-t border-border">
                        <StatusPill
                          label={ev.event_type}
                          variant={isUrgent ? 'liability' : 'neutral'}
                        />
                        {ev.amount !== null && ev.amount !== undefined && (
                          <div className="text-xs font-mono font-medium text-ink">
                            Amount: <Money amount={ev.amount} />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {/* Tab: Data Export & Delete */}
      {activeTab === 'settings' && (
        <Card className="space-y-6">
          <div className="border-b border-border pb-3">
            <h2 className="text-xl font-serif text-ink">Archival Data Management & Privacy</h2>
            <p className="text-xs font-sans text-muted-ink mt-0.5">
              Export everything as structured JSON or permanently purge your user records.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="border border-border rounded-sm p-5 flex flex-col justify-between bg-canvas">
              <div>
                <Download className="w-5 h-5 text-ink mb-2" />
                <h3 className="text-sm font-medium font-sans text-ink">Export All Records (JSON)</h3>
                <p className="text-xs font-sans text-muted-ink mt-1 leading-relaxed">
                  Download a full archival export containing your appliances, bills, transactions,
                  income sources, liabilities, holdings, and recommendations.
                </p>
              </div>
              <button
                onClick={handleExport}
                className="mt-4 py-2 px-4 bg-ink hover:bg-muted-ink text-canvas text-xs font-mono rounded-sm flex items-center justify-center gap-2 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Export Ledger
              </button>
            </div>

            <div className="border border-liability/40 bg-liability/5 rounded-sm p-5 flex flex-col justify-between">
              <div>
                <Trash2 className="w-5 h-5 text-liability mb-2" />
                <h3 className="text-sm font-medium font-sans text-liability">Purge Archival Record</h3>
                <p className="text-xs font-sans text-muted-ink mt-1 leading-relaxed">
                  Permanently erase your user account and all cascaded records from the Vault ledger.
                  This action is irreversible.
                </p>
              </div>
              <button
                onClick={handleDelete}
                className="mt-4 py-2 px-4 bg-liability hover:bg-liability/90 text-surface text-xs font-mono rounded-sm flex items-center justify-center gap-2 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Purge Account
              </button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
