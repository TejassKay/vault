import React, { useEffect, useState } from 'react';
import {
  Goal,
  GoalProjection,
  addGoalSaving,
  createGoal,
  fetchGoalProjection,
  fetchGoals,
} from '../api/finances';

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
    } finally {
      // loaded
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Savings Goals & Projections</h1>
        <p className="text-sm text-slate-500">
          Create priority-based goals and view required contributions across multiple growth scenarios.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Create Goal Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Create a New Goal</h2>
        <form onSubmit={handleCreateGoal} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Goal Title</label>
            <input
              type="text"
              placeholder="e.g. Car Down Payment"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs p-2 border border-slate-300 rounded"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Target Amount (₹)</label>
            <input
              type="number"
              placeholder="e.g. 500000"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
              className="w-full text-xs p-2 border border-slate-300 rounded"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Target Deadline</label>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full text-xs p-2 border border-slate-300 rounded"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full text-xs p-2 border border-slate-300 rounded"
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="sm:col-span-2 md:col-span-4 flex justify-end">
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-medium"
            >
              Set Goal
            </button>
          </div>
        </form>
      </div>

      {/* Goal Projections Modal */}
      {activeProjection && (
        <div className="bg-indigo-50 border border-indigo-200 p-6 rounded-xl shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-bold text-indigo-950">
                Contribution Scenarios: {activeProjection.title}
              </h2>
              <p className="text-xs text-indigo-700">
                {activeProjection.months_left} months remaining • Progress: {activeProjection.progress_percent}%
              </p>
            </div>
            <button
              onClick={() => setActiveProjection(null)}
              className="text-xs text-slate-500 hover:text-slate-800"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {activeProjection.scenarios.map((sc) => (
              <div key={sc.rate_percent} className="bg-white p-4 rounded-lg border border-indigo-100">
                <div className="text-xs font-semibold text-indigo-600">
                  {sc.rate_percent === 0 ? 'Conservative (0% return)' : `${sc.rate_percent}% Expected Return`}
                </div>
                <div className="text-xl font-bold text-slate-900 mt-2">
                  ₹{Number(sc.required_contribution).toLocaleString('en-IN')}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">per month required</div>
              </div>
            ))}
          </div>

          <div className="text-xs text-slate-500 italic bg-white p-2 rounded border border-indigo-100">
            ⚠️ {activeProjection.disclaimer}
          </div>
        </div>
      )}

      {/* Goals List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map((g) => {
          const progress = Math.min(100, Math.round((Number(g.saved_amount) / Number(g.target_amount)) * 100));
          return (
            <div key={g.goal_id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-slate-900">{g.title}</h3>
                  <div className="text-xs text-slate-500">Deadline: {g.target_date}</div>
                </div>
                <span className={`px-2 py-0.5 text-[11px] rounded font-medium ${g.priority === 'high' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-100 text-slate-700'}`}>
                  {g.priority.toUpperCase()}
                </span>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-600 mb-1">
                  <span>₹{Number(g.saved_amount).toLocaleString('en-IN')} saved</span>
                  <span>Target: ₹{Number(g.target_amount).toLocaleString('en-IN')} ({progress}%)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center pt-2">
                <button
                  onClick={() => handleViewProjection(g.goal_id)}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
                >
                  View Scenarios ➔
                </button>

                {savingGoalId === g.goal_id ? (
                  <div className="flex gap-1 items-center">
                    <input
                      type="number"
                      placeholder="₹ Amount"
                      value={savingAmount}
                      onChange={(e) => setSavingAmount(e.target.value)}
                      className="text-xs p-1 border rounded w-20"
                    />
                    <button
                      onClick={() => handleAddSaving(g.goal_id)}
                      className="px-2 py-1 bg-emerald-600 text-white rounded text-xs"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setSavingGoalId(null)}
                      className="text-xs text-slate-400"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setSavingGoalId(g.goal_id)}
                    className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-medium"
                  >
                    + Add Saving
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
