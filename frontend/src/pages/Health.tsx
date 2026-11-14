import React, { useEffect, useState } from 'react';
import { fetchHealth, HealthResponse } from '../api/client';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

export const Health: React.FC = () => {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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

  return (
    <div className="max-w-xl mx-auto bg-white rounded-xl border border-slate-200 p-6 space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Backend System Status</h2>
          <p className="text-xs text-slate-500">System Health Verification</p>
        </div>
        <button
          onClick={checkStatus}
          disabled={loading}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading && (
        <div className="py-8 text-center text-slate-400 text-sm">
          Checking backend connection...
        </div>
      )}

      {!loading && data && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 bg-emerald-50 text-emerald-800 p-4 rounded-lg">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
            <div>
              <div className="font-semibold text-sm">Backend Connected</div>
              <div className="text-xs text-emerald-600">FastAPI status: {data.status}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm bg-slate-50 p-4 rounded-lg">
            <div>
              <span className="text-xs text-slate-400 block">App Name</span>
              <span className="font-medium text-slate-700">{data.app}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">API Version</span>
              <span className="font-medium text-slate-700">{data.version}</span>
            </div>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 bg-red-50 text-red-800 p-4 rounded-lg">
          <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-sm">Connection Failed</div>
            <div className="text-xs text-red-600 mt-1">{error}</div>
            <div className="text-xs text-slate-500 mt-2">
              Ensure FastAPI backend is running on <code>http://localhost:8000</code>.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
