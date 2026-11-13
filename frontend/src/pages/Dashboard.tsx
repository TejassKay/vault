import React from 'react';
import { ShieldCheck, TrendingUp, AlertTriangle } from 'lucide-react';

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex items-start gap-4">
        <ShieldCheck className="w-6 h-6 text-emerald-600 mt-1 flex-shrink-0" />
        <div>
          <h2 className="text-base font-semibold text-emerald-900">
            Phase 0 Scaffold Active
          </h2>
          <p className="text-sm text-emerald-700 mt-1">
            Vault connected personal finance and asset-protection platform initialized.
            FastAPI backend, React routing, Tailwind CSS, and CI pipeline configured.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Net Cash Flow</span>
            <TrendingUp className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">₹0.00</div>
          <span className="text-xs text-slate-400 mt-1 block">Awaiting Phase 1-3 Data</span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Net Worth</span>
            <TrendingUp className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">₹0.00</div>
          <span className="text-xs text-slate-400 mt-1 block">Holdings minus Liabilities</span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Emergency Coverage</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">0.0 months</div>
          <span className="text-xs text-slate-400 mt-1 block">Target: 6.0 months</span>
        </div>
      </div>
    </div>
  );
};
