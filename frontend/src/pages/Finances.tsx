import React, { useEffect, useState } from 'react';
import {
  FinancialSnapshot,
  Holding,
  IncomeSource,
  Liability,
  Transaction,
  createHolding,
  createIncomeSource,
  createLiability,
  createTransaction,
  fetchHoldings,
  fetchIncomeSources,
  fetchLiabilities,
  fetchSnapshot,
  fetchTransactions,
} from '../api/finances';

export const Finances: React.FC = () => {
  const [snapshot, setSnapshot] = useState<FinancialSnapshot | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [incomeSources, setIncomeSources] = useState<IncomeSource[]>([]);
  const [liabilities, setLiabilities] = useState<Liability[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [nudgeMessage, setNudgeMessage] = useState<string | null>(null);

  // New Transaction Form state
  const [txnType, setTxnType] = useState('expense');
  const [txnAmount, setTxnAmount] = useState('');
  const [txnCategory, setTxnCategory] = useState('Groceries');
  const [txnDate] = useState(new Date().toISOString().split('T')[0]);

  // New Income Source Form state
  const [incName, setIncName] = useState('');
  const [incAmount, setIncAmount] = useState('');
  const [incFrequency, setIncFrequency] = useState('monthly');

  // New Liability Form state
  const [liabType] = useState('personal');
  const [liabLender, setLiabLender] = useState('');
  const [liabPrincipal, setLiabPrincipal] = useState('');
  const [liabRate] = useState('');
  const [liabEmi, setLiabEmi] = useState('');
  const [liabDueDay] = useState('5');

  // New Holding Form state
  const [holdType] = useState('bank_savings');
  const [holdName, setHoldName] = useState('');
  const [holdValue, setHoldValue] = useState('');
  const [holdReserve, setHoldReserve] = useState(false);

  const loadAll = async () => {
    try {
      setError(null);
      const [snapData, txnsData, incData, liabData, holdData] = await Promise.all([
        fetchSnapshot(),
        fetchTransactions(),
        fetchIncomeSources(),
        fetchLiabilities(),
        fetchHoldings(),
      ]);
      setSnapshot(snapData);
      setTransactions(txnsData);
      setIncomeSources(incData);
      setLiabilities(liabData);
      setHoldings(holdData);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load financial records');
      }
    } finally {
      // loaded
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleAddTxn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!txnAmount) return;
    try {
      const res = await createTransaction({
        type: txnType,
        amount: parseFloat(txnAmount),
        category: txnCategory,
        txn_date: txnDate,
        is_recurring: false,
      });
      if (res.nudge?.message) {
        setNudgeMessage(res.nudge.message);
      }
      setTxnAmount('');
      await loadAll();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddIncome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incName || !incAmount) return;
    try {
      await createIncomeSource({
        name: incName,
        amount: parseFloat(incAmount),
        frequency: incFrequency,
        income_type: 'fixed',
        is_active: true,
      });
      setIncName('');
      setIncAmount('');
      await loadAll();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddLiability = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!liabPrincipal || !liabEmi) return;
    try {
      await createLiability({
        type: liabType,
        lender_name: liabLender || null,
        outstanding_principal: parseFloat(liabPrincipal),
        interest_rate: parseFloat(liabRate || '10.0'),
        emi_amount: parseFloat(liabEmi),
        due_day: parseInt(liabDueDay, 10),
        status: 'active',
      });
      setLiabLender('');
      setLiabPrincipal('');
      setLiabEmi('');
      await loadAll();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!holdName || !holdValue) return;
    try {
      await createHolding({
        type: holdType,
        name: holdName,
        current_value: parseFloat(holdValue),
        as_of_date: new Date().toISOString().split('T')[0],
        liquidity: 'liquid',
        is_emergency_reserve: holdReserve,
        source: 'manual',
      });
      setHoldName('');
      setHoldValue('');
      setHoldReserve(false);
      await loadAll();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Financial Core</h1>
        <p className="text-sm text-slate-500">
          Track income, expenses, debts, holdings, and view deterministic financial metrics.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {nudgeMessage && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-sm flex justify-between items-center">
          <span>💡 <strong>Budgeting Nudge (FR-8):</strong> {nudgeMessage}</span>
          <button onClick={() => setNudgeMessage(null)} className="text-xs text-amber-700 hover:text-amber-900">
            Dismiss
          </button>
        </div>
      )}

      {/* Snapshot Cards (FR-10, FR-18 - FR-20) */}
      {snapshot && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-900">Financial Health Snapshot (FR-10)</h2>
            {snapshot.is_stale && (
              <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                Stale Data Indicator
              </span>
            )}
          </div>

          {!snapshot.is_sufficient ? (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600">
              <span className="font-semibold text-slate-800">Insufficient Data:</span> Please provide{' '}
              {snapshot.missing_items.join(' and ')} to compute accurate metrics.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="text-xs text-slate-500 font-medium">Monthly Income</div>
                <div className="text-lg font-bold text-slate-900 mt-1">
                  ₹{Number(snapshot.monthly_income).toLocaleString('en-IN')}
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="text-xs text-slate-500 font-medium">Net Cash Flow</div>
                <div className={`text-lg font-bold mt-1 ${snapshot.net_cash_flow >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  ₹{Number(snapshot.net_cash_flow).toLocaleString('en-IN')}
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="text-xs text-slate-500 font-medium">Savings Rate</div>
                <div className="text-lg font-bold text-indigo-600 mt-1">
                  {snapshot.savings_rate}%
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="text-xs text-slate-500 font-medium">DTI Ratio</div>
                <div className="text-lg font-bold text-slate-900 mt-1">
                  {snapshot.dti}% <span className="text-xs font-normal text-slate-400">({snapshot.dti_level})</span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="text-xs text-slate-500 font-medium">Net Worth (FR-18)</div>
                <div className="text-lg font-bold text-slate-900 mt-1">
                  ₹{Number(snapshot.net_worth).toLocaleString('en-IN')}
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="text-xs text-slate-500 font-medium">Emergency Fund (FR-19)</div>
                <div className="text-lg font-bold text-slate-900 mt-1">
                  {snapshot.emergency_coverage_months} <span className="text-xs font-normal text-slate-400">mo</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Grid of Forms & Records */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income Sources (FR-15) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 space-y-4">
          <h3 className="font-semibold text-slate-900">Income Sources ({incomeSources.length})</h3>
          <form onSubmit={handleAddIncome} className="flex gap-2">
            <input
              type="text"
              placeholder="Source Name"
              value={incName}
              onChange={(e) => setIncName(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded flex-1"
              required
            />
            <input
              type="number"
              placeholder="Amount (₹)"
              value={incAmount}
              onChange={(e) => setIncAmount(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded w-28"
              required
            />
            <select
              value={incFrequency}
              onChange={(e) => setIncFrequency(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
            >
              <option value="monthly">Monthly</option>
              <option value="weekly">Weekly</option>
              <option value="yearly">Yearly</option>
            </select>
            <button type="submit" className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs">
              Add
            </button>
          </form>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
            {incomeSources.map((s) => (
              <div key={s.income_source_id} className="py-2 flex justify-between">
                <span className="font-medium text-slate-800">{s.name} ({s.frequency})</span>
                <span className="font-semibold text-slate-900">₹{Number(s.amount).toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Transactions (FR-7) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 space-y-4">
          <h3 className="font-semibold text-slate-900">Record Transaction (FR-7)</h3>
          <form onSubmit={handleAddTxn} className="flex gap-2">
            <select
              value={txnType}
              onChange={(e) => setTxnType(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
            <input
              type="number"
              placeholder="Amount"
              value={txnAmount}
              onChange={(e) => setTxnAmount(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded w-24"
              required
            />
            <input
              type="text"
              placeholder="Category"
              value={txnCategory}
              onChange={(e) => setTxnCategory(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded flex-1"
              required
            />
            <button type="submit" className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs">
              Record
            </button>
          </form>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
            {transactions.slice(0, 5).map((t) => (
              <div key={t.transaction_id} className="py-2 flex justify-between">
                <span>{t.category} ({t.txn_date})</span>
                <span className={t.type === 'income' ? 'text-emerald-600 font-semibold' : 'text-slate-800'}>
                  ₹{Number(t.amount).toLocaleString('en-IN')}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Liabilities / Loans (FR-16) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 space-y-4">
          <h3 className="font-semibold text-slate-900">Liabilities & EMIs ({liabilities.length})</h3>
          <form onSubmit={handleAddLiability} className="grid grid-cols-3 gap-2">
            <input
              type="text"
              placeholder="Lender"
              value={liabLender}
              onChange={(e) => setLiabLender(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
            />
            <input
              type="number"
              placeholder="Principal (₹)"
              value={liabPrincipal}
              onChange={(e) => setLiabPrincipal(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
              required
            />
            <input
              type="number"
              placeholder="EMI (₹)"
              value={liabEmi}
              onChange={(e) => setLiabEmi(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
              required
            />
            <button type="submit" className="col-span-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs">
              Add Liability
            </button>
          </form>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
            {liabilities.map((l) => (
              <div key={l.liability_id} className="py-2 flex justify-between">
                <span>{l.lender_name || l.type} (EMI Due day: {l.due_day})</span>
                <span className="font-semibold text-red-600">EMI: ₹{Number(l.emi_amount).toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Financial Holdings (FR-17) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 space-y-4">
          <h3 className="font-semibold text-slate-900">Financial Holdings ({holdings.length})</h3>
          <form onSubmit={handleAddHolding} className="grid grid-cols-2 gap-2">
            <input
              type="text"
              placeholder="Asset Name (e.g. FD, Savings)"
              value={holdName}
              onChange={(e) => setHoldName(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
              required
            />
            <input
              type="number"
              placeholder="Current Value (₹)"
              value={holdValue}
              onChange={(e) => setHoldValue(e.target.value)}
              className="text-xs p-2 border border-slate-300 rounded"
              required
            />
            <label className="text-xs flex items-center gap-1 col-span-2">
              <input
                type="checkbox"
                checked={holdReserve}
                onChange={(e) => setHoldReserve(e.target.checked)}
              />
              Mark as Emergency Reserve Fund
            </label>
            <button type="submit" className="col-span-2 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs">
              Add Holding
            </button>
          </form>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
            {holdings.map((h) => (
              <div key={h.holding_id} className="py-2 flex justify-between">
                <span>{h.name} {h.is_emergency_reserve && <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">Reserve</span>}</span>
                <span className="font-semibold text-slate-900">₹{Number(h.current_value).toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
