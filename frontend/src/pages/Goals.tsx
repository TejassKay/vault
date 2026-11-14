import React, { useEffect, useState } from 'react';
import {
  Goal,
  GoalProjection,
  addGoalSaving,
  createGoal,
  fetchGoalProjection,
  fetchGoals,
} from '../api/finances';
import Money from '../components/Money';
import Card from '../components/Card';
import StatusPill from '../components/StatusPill';

export const Goals: React.FC = () => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [error, setError] = useState<string | null>(null);

  // New Goal form
  const [title, setTitle] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [priority, setPriority] = useState('medium');

  // Projection Modal
  const [activeProjection, setActiveProjection] = useState<GoalProjection | null>(null);
  const [savingGoalId, setSavingGoalId] = useState<number | null>(null);
  const [savingAmount, setSavingAmount] = useState('');

  const loadGoals = async () => {
    try {
      setError(null);
      const data = await fetchGoals();
      setGoals(data);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  useEffect(() => {
    loadGoals();
  }, []);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !targetAmount || !targetDate) return;
    try {
      await createGoal({
        title,
        target_amount: parseFloat(targetAmount),
        saved_amount: 0,
        target_date: targetDate,
        priority,
        liquidity_need: 'medium',
        status: 'active',
      });
      setTitle('');
      setTargetAmount('');
      setTargetDate('');
      await loadGoals();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddSaving = async (goalId: number) => {
    if (!savingAmount) return;
    try {
      await addGoalSaving(goalId, parseFloat(savingAmount));
      setSavingGoalId(null);
      setSavingAmount('');
      await loadGoals();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleViewProjection = async (goalId: number) => {
    try {
      const proj = await fetchGoalProjection(goalId);
      setActiveProjection(proj);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-serif text-ink tracking-tight">Savings Goals & Targets</h1>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Archival savings ledger, horizon schedules, and projected contribution scenarios
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-surface border border-liability text-liability rounded-sm text-xs font-sans">
          {error}
        </div>
      )}

      {/* Create Goal Card */}
      <Card className="space-y-4">
        <div className="border-b border-border pb-3">
          <h2 className="text-xl font-serif text-ink">Establish New Savings Goal</h2>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Deterministic goal engines compute monthly contribution requirements across low, baseline, and growth scenarios.
          </p>
        </div>

        <form onSubmit={handleCreateGoal} className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-sans text-muted-ink mb-1">Goal Purpose</label>
            <input
              type="text"
              placeholder="e.g. Emergency Fund, Child Education"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-sans text-muted-ink mb-1">Target Amount (INR)</label>
            <input
              type="number"
              placeholder="e.g. 500000"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
              className="w-full text-xs font-mono p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-sans text-muted-ink mb-1">Target Date</label>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full text-xs font-mono p-2 border border-border rounded-sm bg-surface focus:border-ink"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-sans text-muted-ink mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full text-xs font-sans p-2 border border-border rounded-sm bg-surface focus:border-ink"
            >
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
            </select>
          </div>

          <div className="md:col-span-4 flex justify-end pt-2">
            <button
              type="submit"
              className="px-4 py-2 bg-ink hover:bg-muted-ink text-canvas rounded-sm text-xs font-mono transition-colors"
            >
              Establish Goal
            </button>
          </div>
        </form>
      </Card>

      {/* Goals Index */}
      <div className="space-y-4">
        <div className="flex justify-between items-center border-b border-border pb-3">
          <h2 className="text-xl font-serif text-ink">Active Goals ({goals.length})</h2>
          <button
            onClick={loadGoals}
            className="text-xs font-mono text-muted-ink hover:text-ink"
          >
            Refresh
          </button>
        </div>

        {goals.length === 0 ? (
          <Card className="text-center py-12 text-xs font-sans text-muted-ink">
            No active savings goals found. Establish your first goal above.
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {goals.map((goal) => {
              const progressPct = goal.target_amount > 0
                ? Math.min(100, Math.round((goal.saved_amount / goal.target_amount) * 100))
                : 0;

              return (
                <Card
                  key={goal.goal_id}
                  className="border border-border bg-surface flex flex-col justify-between space-y-4 hover:border-ink transition-colors"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3 border-b border-border pb-3">
                      <div>
                        <span className="text-[10px] font-mono tracking-wider uppercase text-muted-ink block">
                          Goal #{goal.goal_id}
                        </span>
                        <h3 className="text-lg font-serif text-ink mt-0.5">{goal.title}</h3>
                      </div>
                      <StatusPill
                        label={goal.priority}
                        variant={goal.priority === 'high' ? 'liability' : 'neutral'}
                      />
                    </div>

                    {/* Progress Bar & Amount Numbers */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-muted-ink">Progress</span>
                        <span className="font-semibold text-ink">{progressPct}%</span>
                      </div>
                      <div className="w-full bg-canvas border border-border rounded-sm h-2 overflow-hidden">
                        <div
                          className="bg-growth h-full transition-all"
                          style={{ width: `${progressPct}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs font-mono pt-1">
                        <span className="text-muted-ink">
                          Saved: <Money amount={goal.saved_amount} />
                        </span>
                        <span className="text-ink font-medium">
                          Target: <Money amount={goal.target_amount} />
                        </span>
                      </div>
                    </div>

                    <div className="text-[11px] font-mono text-muted-ink pt-1 flex items-center justify-between">
                      <span>Target Date: {goal.target_date}</span>
                      <span>Status: {goal.status}</span>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="pt-3 border-t border-border flex flex-wrap items-center justify-between gap-2">
                    <button
                      onClick={() => handleViewProjection(goal.goal_id)}
                      className="text-xs font-mono text-ink underline hover:text-muted-ink"
                    >
                      View Projections (FR-27) &rarr;
                    </button>

                    {savingGoalId === goal.goal_id ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="number"
                          placeholder="Amount"
                          value={savingAmount}
                          onChange={(e) => setSavingAmount(e.target.value)}
                          className="w-24 text-xs font-mono p-1 border border-border rounded-sm bg-surface"
                        />
                        <button
                          onClick={() => handleAddSaving(goal.goal_id)}
                          className="px-2 py-1 bg-growth text-surface text-xs font-mono rounded-sm"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setSavingGoalId(null)}
                          className="px-2 py-1 text-xs font-mono text-muted-ink"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setSavingGoalId(goal.goal_id)}
                        className="px-2.5 py-1 bg-canvas hover:bg-surface border border-border rounded-sm text-xs font-mono text-ink transition-colors"
                      >
                        + Log Contribution
                      </button>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* FR-27: Scenario Projection Modal */}
      {activeProjection && (
        <div
          className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50"
          onClick={() => setActiveProjection(null)}
        >
          <div
            className="w-full max-w-lg bg-surface border border-ink rounded-sm p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Deterministic Planning Projections (FR-27)
                </span>
                <h3 className="text-xl font-serif text-ink mt-0.5">
                  Monthly Contribution Scenarios
                </h3>
              </div>
              <button
                onClick={() => setActiveProjection(null)}
                className="text-xs font-mono text-muted-ink hover:text-ink"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              {activeProjection.scenarios.map((sc, i) => {
                const labels = ['Conservative Scenario', 'Baseline Planning Scenario', 'Optimistic Growth Scenario'];
                const descs = ['Low-volatility safe yield', 'Standard expected growth yield', 'Higher return expectation'];
                return (
                  <div
                    key={i}
                    className={`p-3 bg-canvas border rounded-sm flex items-center justify-between text-xs ${
                      i === 1 ? 'border-ink' : 'border-border'
                    }`}
                  >
                    <div>
                      <span className="font-sans font-medium text-ink block">
                        {labels[i] || `Scenario (${sc.rate_percent}%)`}
                      </span>
                      <span className="text-[11px] font-sans text-muted-ink">
                        {descs[i] || `Assumed annual return: ${sc.rate_percent}%`}
                      </span>
                    </div>
                    <div className="font-mono text-right font-medium text-ink">
                      <Money
                        amount={sc.required_contribution}
                        className={i === 1 ? 'font-semibold text-growth' : 'text-ink'}
                      />
                      <span className="text-muted-ink text-[10px] block">/ month</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Mandatory FR-27 Disclaimer */}
            <div className="p-3 bg-canvas border border-border rounded-sm text-[11px] font-sans text-muted-ink leading-relaxed">
              <strong className="font-mono text-ink block mb-0.5">DISCLAIMER:</strong>
              {activeProjection.disclaimer}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setActiveProjection(null)}
                className="px-4 py-1.5 bg-ink text-canvas rounded-sm text-xs font-mono"
              >
                Close Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Goals;
