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
import Money from '../components/Money';
import Card from '../components/Card';
import StatusPill from '../components/StatusPill';

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
  const [incType, setIncType] = useState('fixed');

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
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleAddTxn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!txnAmount || !txnCategory) return;
    try {
      const res = await createTransaction({
        type: txnType,
        amount: parseFloat(txnAmount),
        category: txnCategory,
        txn_date: txnDate,
        is_recurring: false,
      });
      setTxnAmount('');
      if (res.nudge?.message) {
        setNudgeMessage(res.nudge.message);
      }
      await loadAll();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddIncome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incName || !incAmount) return;
    setError(null);
    try {
      await createIncomeSource({
        name: incName,
        amount: parseFloat(incAmount),
        frequency: incFrequency,
        income_type: incType,
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
        interest_rate: liabRate ? parseFloat(liabRate) : 10.0,
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
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-serif text-ink tracking-tight">Financial Ledger Core</h1>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Archival records of income flows, expenditures, obligations, and capital reserves
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-surface border border-liability text-liability rounded-sm text-xs font-sans">
          {error}
        </div>
      )}

      {nudgeMessage && (
        <div className="p-3.5 bg-surface border-l-4 border-gold border border-border text-ink rounded-sm text-xs flex justify-between items-center">
          <span>
            <strong className="font-mono text-ink uppercase tracking-wide mr-2">Budgeting Nudge:</strong>
            {nudgeMessage}
          </span>
          <button
            onClick={() => setNudgeMessage(null)}
            className="text-xs font-mono text-muted-ink hover:text-ink ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Snapshot Ledger Header Cards */}
      {snapshot && (
        <Card className="space-y-4">
          <div className="flex justify-between items-center border-b border-border pb-3">
            <h2 className="text-xl font-serif text-ink">Ledger Snapshot & Computed Core</h2>
            {snapshot.is_stale && (
              <StatusPill label="STALE DATA RECORD" variant="liability" />
            )}
          </div>

          {!snapshot.is_sufficient ? (
            <div className="p-4 bg-canvas border border-border rounded-sm text-xs text-muted-ink">
              <span className="font-medium text-ink">Insufficient Data:</span> Please record{' '}
              {snapshot.missing_items.join(' and ')} to compute accurate metrics.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 bg-canvas rounded-sm border border-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Monthly Income
                </span>
                <div className="text-lg font-mono font-medium text-ink mt-1">
                  <Money amount={snapshot.monthly_income} />
                </div>
              </div>

              <div className="p-3 bg-canvas rounded-sm border border-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Net Cash Flow
                </span>
                <div className="text-lg font-mono font-medium mt-1">
                  <Money amount={snapshot.net_cash_flow} showSign />
                </div>
              </div>

              <div className="p-3 bg-canvas rounded-sm border border-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Savings Rate
                </span>
                <div className="text-lg font-mono font-medium text-ink mt-1">
                  {snapshot.savings_rate}%
                </div>
              </div>

              <div className="p-3 bg-canvas rounded-sm border border-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  DTI Ratio
                </span>
                <div className="text-lg font-mono font-medium text-ink mt-1">
                  {snapshot.dti}%
                </div>
                <span className="text-[10px] font-mono text-muted-ink block uppercase">
                  {snapshot.dti_level}
                </span>
              </div>

              <div className="p-3 bg-canvas rounded-sm border border-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Net Worth
                </span>
                <div className="text-lg font-mono font-medium text-ink mt-1">
                  <Money amount={snapshot.net_worth} />
                </div>
              </div>

              <div className="p-3 bg-canvas rounded-sm border border-border">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Emergency Fund
                </span>
                <div className="text-lg font-mono font-medium text-ink mt-1">
                  {snapshot.emergency_coverage_months}{' '}
                  <span className="text-xs font-sans text-muted-ink">mo</span>
                </div>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Grid of Forms & Records: Archival tables with tabular-nums and right-aligned numbers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income Sources (FR-15) */}
        <Card className="space-y-4">
          <div className="border-b border-border pb-3 flex justify-between items-center">
            <h3 className="text-lg font-serif text-ink">Income Sources ({incomeSources.length})</h3>
          </div>

          <form onSubmit={handleAddIncome} className="flex gap-2">
            <input
              type="text"
              placeholder="Source Name"
              value={incName}
              onChange={(e) => setIncName(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface flex-1 focus:border-ink"
              required
            />
            <input
              type="number"
              placeholder="Amount (₹)"
              value={incAmount}
              onChange={(e) => setIncAmount(e.target.value)}
              className="text-xs font-mono p-2 border border-border rounded-sm bg-surface w-28 focus:border-ink"
              required
            />
            <select
              value={incFrequency}
              onChange={(e) => setIncFrequency(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
            >
              <option value="monthly">Monthly</option>
              <option value="weekly">Weekly</option>
              <option value="yearly">Yearly</option>
            </select>
            <select
              value={incType}
              onChange={(e) => setIncType(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
            >
              <option value="fixed">Fixed</option>
              <option value="variable">Variable</option>
            </select>
            <button
              type="submit"
              className="px-3 py-1 bg-ink hover:bg-muted-ink text-canvas rounded-sm text-xs font-mono transition-colors"
            >
              Add
            </button>
          </form>

          {/* Table */}
          <div className="max-h-56 overflow-y-auto border border-border rounded-sm bg-canvas">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface text-[10px] font-mono text-muted-ink uppercase">
                  <th className="p-2.5 font-normal">Source</th>
                  <th className="p-2.5 font-normal">Frequency</th>
                  <th className="p-2.5 font-normal text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {incomeSources.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="p-4 text-center text-muted-ink font-sans">
                      No income sources logged.
                    </td>
                  </tr>
                ) : (
                  incomeSources.map((s) => (
                    <tr key={s.income_source_id} className="hover:bg-surface/50">
                      <td className="p-2.5 font-sans font-medium text-ink">{s.name}</td>
                      <td className="p-2.5 font-mono text-[11px] text-muted-ink capitalize">{s.frequency}</td>
                      <td className="p-2.5 font-mono text-right text-ink">
                        <Money amount={s.amount} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Transactions (FR-7) */}
        <Card className="space-y-4">
          <div className="border-b border-border pb-3 flex justify-between items-center">
            <h3 className="text-lg font-serif text-ink">Record Transaction ({transactions.length})</h3>
          </div>

          <form onSubmit={handleAddTxn} className="flex gap-2">
            <select
              value={txnType}
              onChange={(e) => setTxnType(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
            <input
              type="number"
              placeholder="Amount"
              value={txnAmount}
              onChange={(e) => setTxnAmount(e.target.value)}
              className="text-xs font-mono p-2 border border-border rounded-sm bg-surface w-24 focus:border-ink"
              required
            />
            <input
              type="text"
              placeholder="Category"
              value={txnCategory}
              onChange={(e) => setTxnCategory(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface flex-1 focus:border-ink"
              required
            />
            <button
              type="submit"
              className="px-3 py-1 bg-ink hover:bg-muted-ink text-canvas rounded-sm text-xs font-mono transition-colors"
            >
              Record
            </button>
          </form>

          {/* Table */}
          <div className="max-h-56 overflow-y-auto border border-border rounded-sm bg-canvas">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface text-[10px] font-mono text-muted-ink uppercase">
                  <th className="p-2.5 font-normal">Date</th>
                  <th className="p-2.5 font-normal">Category</th>
                  <th className="p-2.5 font-normal">Type</th>
                  <th className="p-2.5 font-normal text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-muted-ink font-sans">
                      No transactions recorded.
                    </td>
                  </tr>
                ) : (
                  transactions.slice(0, 10).map((t) => (
                    <tr key={t.transaction_id} className="hover:bg-surface/50">
                      <td className="p-2.5 font-mono text-[11px] text-muted-ink">{t.txn_date}</td>
                      <td className="p-2.5 font-sans font-medium text-ink">{t.category}</td>
                      <td className="p-2.5">
                        <StatusPill
                          label={t.type}
                          variant={t.type === 'income' ? 'growth' : 'liability'}
                        />
                      </td>
                      <td className="p-2.5 font-mono text-right">
                        <Money
                          amount={t.type === 'expense' ? -Math.abs(Number(t.amount)) : Number(t.amount)}
                          showSign
                        />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Liabilities / Loans (FR-16) */}
        <Card className="space-y-4">
          <div className="border-b border-border pb-3 flex justify-between items-center">
            <h3 className="text-lg font-serif text-ink">Liabilities & EMIs ({liabilities.length})</h3>
          </div>

          <form onSubmit={handleAddLiability} className="grid grid-cols-3 gap-2">
            <input
              type="text"
              placeholder="Lender / Note"
              value={liabLender}
              onChange={(e) => setLiabLender(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
            />
            <input
              type="number"
              placeholder="Principal (₹)"
              value={liabPrincipal}
              onChange={(e) => setLiabPrincipal(e.target.value)}
              className="text-xs font-mono p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
            <input
              type="number"
              placeholder="EMI (₹)"
              value={liabEmi}
              onChange={(e) => setLiabEmi(e.target.value)}
              className="text-xs font-mono p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
            <button
              type="submit"
              className="col-span-3 py-1.5 bg-ink hover:bg-muted-ink text-canvas rounded-sm text-xs font-mono transition-colors"
            >
              Log Liability
            </button>
          </form>

          {/* Table */}
          <div className="max-h-56 overflow-y-auto border border-border rounded-sm bg-canvas">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface text-[10px] font-mono text-muted-ink uppercase">
                  <th className="p-2.5 font-normal">Lender / Type</th>
                  <th className="p-2.5 font-normal">Due Day</th>
                  <th className="p-2.5 font-normal text-right">Principal</th>
                  <th className="p-2.5 font-normal text-right">EMI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {liabilities.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-muted-ink font-sans">
                      No liabilities logged.
                    </td>
                  </tr>
                ) : (
                  liabilities.map((l) => (
                    <tr key={l.liability_id} className="hover:bg-surface/50">
                      <td className="p-2.5 font-sans font-medium text-ink">
                        {l.lender_name || l.type}
                      </td>
                      <td className="p-2.5 font-mono text-[11px] text-muted-ink">Day {l.due_day}</td>
                      <td className="p-2.5 font-mono text-right text-liability">
                        <Money amount={l.outstanding_principal} />
                      </td>
                      <td className="p-2.5 font-mono text-right font-medium text-liability">
                        <span className="inline-flex items-center gap-1.5">
                          <StatusPill label="EMI" variant="liability" />
                          <Money amount={l.emi_amount} />
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Financial Holdings (FR-17) */}
        <Card className="space-y-4">
          <div className="border-b border-border pb-3 flex justify-between items-center">
            <h3 className="text-lg font-serif text-ink">Financial Holdings ({holdings.length})</h3>
          </div>

          <form onSubmit={handleAddHolding} className="grid grid-cols-2 gap-2">
            <input
              type="text"
              placeholder="Asset Name (FD, Savings, etc.)"
              value={holdName}
              onChange={(e) => setHoldName(e.target.value)}
              className="text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
            <input
              type="number"
              placeholder="Current Value (₹)"
              value={holdValue}
              onChange={(e) => setHoldValue(e.target.value)}
              className="text-xs font-mono p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
            <label className="text-xs font-sans flex items-center gap-1.5 col-span-2 text-muted-ink">
              <input
                type="checkbox"
                checked={holdReserve}
                onChange={(e) => setHoldReserve(e.target.checked)}
                className="rounded-xs border-border"
              />
              Designate as Emergency Reserve Fund
            </label>
            <button
              type="submit"
              className="col-span-2 py-1.5 bg-ink hover:bg-muted-ink text-canvas rounded-sm text-xs font-mono transition-colors"
            >
              Add Holding
            </button>
          </form>

          {/* Table */}
          <div className="max-h-56 overflow-y-auto border border-border rounded-sm bg-canvas">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface text-[10px] font-mono text-muted-ink uppercase">
                  <th className="p-2.5 font-normal">Holding</th>
                  <th className="p-2.5 font-normal">Role</th>
                  <th className="p-2.5 font-normal text-right">Current Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {holdings.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="p-4 text-center text-muted-ink font-sans">
                      No holdings logged.
                    </td>
                  </tr>
                ) : (
                  holdings.map((h) => (
                    <tr key={h.holding_id} className="hover:bg-surface/50">
                      <td className="p-2.5 font-sans font-medium text-ink">{h.name}</td>
                      <td className="p-2.5">
                        {h.is_emergency_reserve ? (
                          <StatusPill label="RESERVE" variant="growth" />
                        ) : (
                          <span className="text-[11px] font-mono text-muted-ink">General</span>
                        )}
                      </td>
                      <td className="p-2.5 font-mono text-right text-ink font-medium">
                        <Money amount={h.current_value} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Finances;
