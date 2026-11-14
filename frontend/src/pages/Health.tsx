import React, { useEffect, useState } from 'react';
import { fetchHealth, HealthResponse } from '../api/client';
import { triggerDemoSeed } from '../api/dashboard';
import { CheckCircle2, XCircle, RefreshCw, Sliders } from 'lucide-react';

export const Health: React.FC = () => {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [seeding, setSeeding] = useState<boolean>(false);
  const [seedSuccess, setSeedSuccess] = useState<string | null>(null);
  const [seedError, setSeedError] = useState<string | null>(null);

  const checkStatus = () => {
    setLoading(true);
    setError(null);
    fetchHealth()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const handleSeed = async (scenario: 'A' | 'B') => {
    try {
      setSeeding(true);
      setSeedSuccess(null);
      setSeedError(null);
      const res = await triggerDemoSeed(scenario);
      setSeedSuccess(res.message);
    } catch (err) {
      setSeedError(err instanceof Error ? err.message : 'Demo seed failed');
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-surface rounded-sm border border-border p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h2 className="text-xl font-serif text-ink">Backend System Status</h2>
            <p className="text-xs font-sans text-muted-ink">System Health Verification</p>
          </div>
          <button
            onClick={checkStatus}
            disabled={loading}
            className="p-2 text-muted-ink hover:text-ink hover:bg-canvas border border-border rounded-sm transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loading && (
          <div className="py-8 text-center text-muted-ink text-xs font-mono">
            Checking backend connection...
          </div>
        )}

        {!loading && data && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 bg-growth/[0.08] border border-growth/35 text-growth p-4 rounded-sm">
              <CheckCircle2 className="w-6 h-6 text-growth flex-shrink-0" />
              <div>
                <div className="font-semibold text-sm">Backend Connected</div>
                <div className="text-xs font-mono text-growth">FastAPI status: {data.status}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm bg-canvas border border-border p-4 rounded-sm">
              <div>
                <span className="text-[10px] font-mono uppercase text-muted-ink block">App Name</span>
                <span className="font-medium text-ink">{data.app}</span>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase text-muted-ink block">API Version</span>
                <span className="font-mono font-medium text-ink">{data.version}</span>
              </div>
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="flex items-start gap-3 bg-liability/[0.08] border border-liability/35 text-liability p-4 rounded-sm">
            <XCircle className="w-5 h-5 text-liability flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-sm">Connection Failed</div>
              <div className="text-xs mt-1">{error}</div>
              <div className="text-xs text-muted-ink mt-2">
                Ensure FastAPI backend is running on <code>http://localhost:8000</code>.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Demo Scenario Switcher */}
      <div className="bg-surface rounded-sm border border-border p-6 space-y-4">
        <div className="border-b border-border pb-3">
          <h3 className="text-lg font-serif text-ink flex items-center gap-2">
            <Sliders className="w-4 h-4 text-muted-ink" />
            Demo Scenario Switcher
          </h3>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Load pre-configured financial ledger scenarios for testing and verification.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => handleSeed('A')}
            disabled={seeding}
            className="px-3.5 py-2 text-xs font-mono rounded-sm bg-canvas text-ink border border-border hover:border-ink transition-colors disabled:opacity-50"
          >
            Seed A (₹45k)
          </button>
          <button
            onClick={() => handleSeed('B')}
            disabled={seeding}
            className="px-3.5 py-2 text-xs font-mono rounded-sm bg-canvas text-ink border border-border hover:border-ink transition-colors disabled:opacity-50"
          >
            Seed B (₹2.6L)
          </button>
        </div>

        {seedSuccess && (
          <div className="bg-growth/[0.08] border border-growth/35 text-growth px-4 py-2.5 rounded-sm text-xs flex items-center gap-2 font-sans">
            <CheckCircle2 className="w-4 h-4 text-growth flex-shrink-0" />
            {seedSuccess}
          </div>
        )}

        {seedError && (
          <div className="bg-liability/[0.08] border border-liability/35 text-liability px-4 py-2.5 rounded-sm text-xs font-sans">
            {seedError}
          </div>
        )}
      </div>
    </div>
  );
};
