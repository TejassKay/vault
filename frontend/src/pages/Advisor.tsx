import React, { useEffect, useState, useTransition } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  RefreshCw,
  ShieldAlert,
  X,
  XCircle,
} from 'lucide-react';
import {
  InvestmentCapacity,
  Recommendation,
  RiskProfile,
  RiskQuestion,
  fetchInvestmentCapacity,
  fetchRecommendations,
  fetchRiskProfile,
  fetchRiskQuestionnaire,
  generateRecommendations,
  submitRiskProfile,
  updateRecommendationStatus,
} from '../api/advisor';
import { formatSnapshotInput, getLabel } from '../lib/labels.js';
import Money from '../components/Money';
import Card from '../components/Card';
import StatusPill from '../components/StatusPill';

export const Advisor: React.FC = () => {
  const [, startTransition] = useTransition();

  const [capacity, setCapacity] = useState<InvestmentCapacity | null>(null);
  const [riskProfile, setRiskProfile] = useState<RiskProfile | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [disclaimer, setDisclaimer] = useState<string>(
    'Vault provides general educational decision support based on the information you entered. It is not investment advice and does not recommend specific products. Projections are estimates, not guarantees. Consider consulting a SEBI-registered investment adviser.'
  );

  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Questionnaire modal state
  const [showQuestionnaire, setShowQuestionnaire] = useState<boolean>(false);
  const [questions, setQuestions] = useState<RiskQuestion[]>([]);
  const [questionAnswers, setQuestionAnswers] = useState<Record<string, number>>({});
  const [submittingQuiz, setSubmittingQuiz] = useState<boolean>(false);

  // Selected recommendation for the docked right side panel
  const [selectedRecId, setSelectedRecId] = useState<number | null>(null);
  const [expandedRecs, setExpandedRecs] = useState<Record<number, boolean>>({});

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [capRes, profileRes, recsRes] = await Promise.all([
        fetchInvestmentCapacity().catch(() => null),
        fetchRiskProfile().catch(() => null),
        fetchRecommendations().catch(() => null),
      ]);

      if (capRes) setCapacity(capRes);
      if (profileRes) setRiskProfile(profileRes);
      if (recsRes) {
        const recList = recsRes.recommendations || [];
        setRecommendations(recList);
        if (recList.length > 0) {
          setSelectedRecId(recList[0].recommendation_id);
        }
        if (recsRes.disclaimer) setDisclaimer(recsRes.disclaimer);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load advisor data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenQuiz = async () => {
    try {
      if (questions.length === 0) {
        const res = await fetchRiskQuestionnaire();
        setQuestions(res.questions);
      }
      if (riskProfile?.answers) {
        setQuestionAnswers(riskProfile.answers);
      } else {
        setQuestionAnswers({});
      }
      setShowQuestionnaire(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load questionnaire');
    }
  };

  const handleQuizSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (Object.keys(questionAnswers).length < questions.length) {
      alert('Please answer all 8 questions before submitting.');
      return;
    }
    try {
      setSubmittingQuiz(true);
      const updated = await submitRiskProfile(questionAnswers);
      setRiskProfile(updated);
      setShowQuestionnaire(false);
      handleGenerate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save risk profile');
    } finally {
      setSubmittingQuiz(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      const res = await generateRecommendations();
      startTransition(() => {
        setRecommendations(res.recommendations);
        if (res.recommendations.length > 0) {
          setSelectedRecId(res.recommendations[0].recommendation_id);
        }
        if (res.disclaimer) setDisclaimer(res.disclaimer);
      });
      const updatedCap = await fetchInvestmentCapacity().catch(() => null);
      if (updatedCap) setCapacity(updatedCap);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusChange = async (
    recId: number,
    newStatus: 'accepted' | 'rejected' | 'edited'
  ) => {
    try {
      const updated = await updateRecommendationStatus(recId, newStatus);
      setRecommendations((prev) =>
        prev.map((r) => (r.recommendation_id === recId ? { ...r, status: updated.status } : r))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    }
  };

  const selectedRec =
    recommendations.find((r) => r.recommendation_id === selectedRecId) ||
    recommendations[0] ||
    null;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* 1. Statutory Compliance Disclaimer Banner (NFR-7) */}
      <div className="bg-surface border-l-4 border-gold border border-border p-4 flex items-start gap-3 rounded-sm">
        <AlertCircle className="w-5 h-5 text-liability flex-shrink-0 mt-0.5" />
        <div className="text-xs text-ink leading-relaxed font-sans">
          <span className="font-mono text-ink font-semibold uppercase tracking-wider mr-2">
            Decision Support Notice:
          </span>
          {disclaimer}
        </div>
      </div>

      {error && (
        <div className="bg-surface border border-liability text-liability p-4 rounded-sm text-xs flex items-center justify-between font-sans">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-liability hover:text-ink">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 2. Top Header & Action Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-serif text-ink tracking-tight">Advisory Decision Record</h1>
          <p className="text-xs font-sans text-muted-ink mt-0.5">
            Deterministic rule engine with verified explanations, audit trails, and grounded inputs
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-ink hover:bg-muted-ink text-canvas rounded-sm text-xs font-mono disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Evaluating Engine...' : 'Run Advisory Engine'}
          </button>
        </div>
      </div>

      {/* 3. Data Insufficient Warning (FR-29) */}
      {capacity?.status === 'insufficient_data' && (
        <Card className="border border-liability/60 bg-liability/5 space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-liability flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-xs">
              <h3 className="font-serif text-base text-ink">
                Insufficient Baseline Financial Data
              </h3>
              <p className="font-sans text-muted-ink mt-1">
                Vault does not estimate or guess numbers when baseline records are missing. Please enter:
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 font-mono text-ink">
                {capacity.missing_items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
              <div className="mt-3">
                <Link
                  to="/finances"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-canvas bg-ink px-3 py-1.5 rounded-sm hover:bg-muted-ink transition-colors"
                >
                  Enter Baseline Records &rarr;
                </Link>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 4. Top Metric Cards: Capacity & Risk Profile */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Investment Capacity Metric */}
        <Card className="md:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2 border-b border-border pb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink">
                Monthly Investment Capacity
              </span>
              {capacity?.status === 'ok' && (
                <StatusPill label="SUSTAINABLE" variant="growth" />
              )}
              {capacity?.status === 'blocked' && (
                <StatusPill label="PAUSED: PRIORITY FIRST" variant="liability" />
              )}
              {capacity?.status === 'insufficient_data' && (
                <StatusPill label="DATA NEEDED" variant="neutral" />
              )}
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-mono tabular-nums font-semibold text-ink">
                {capacity?.status === 'insufficient_data' ? (
                  'No Data'
                ) : (
                  <Money amount={capacity?.capacity} />
                )}
              </span>
              <span className="text-xs font-mono text-muted-ink">/ month</span>
            </div>

            {capacity?.status === 'blocked' && capacity.reason_codes.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {capacity.reason_codes.map((code) => (
                  <span
                    key={code}
                    className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-sm bg-liability/10 border border-liability/30 text-liability"
                  >
                    <ShieldAlert className="w-3 h-3" />
                    {getLabel(code)}
                  </span>
                ))}
              </div>
            )}

            <p className="text-xs font-sans text-muted-ink mt-2 leading-relaxed">
              {capacity?.status === 'blocked'
                ? 'New investing is paused at ₹0.00 until your emergency fund reaches 3 months and high-interest debt (≥12%) is cleared.'
                : 'Sustainable surplus after goal contributions, safety reserves, and a 10% risk buffer.'}
            </p>
          </div>
        </Card>

        {/* Risk Profile Card */}
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2 border-b border-border pb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink">
                Risk Engine Profile
              </span>
              {riskProfile && (
                <StatusPill
                  label={`${riskProfile.score}/32`}
                  variant="gold"
                />
              )}
            </div>

            {riskProfile ? (
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between font-mono">
                  <span className="text-muted-ink">Tolerance:</span>
                  <span className="text-ink font-medium capitalize">{riskProfile.tolerance_level}</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-muted-ink">Capacity Cap:</span>
                  <span className="text-ink font-medium capitalize">{riskProfile.capacity_level}</span>
                </div>
                <div className="flex justify-between font-mono pt-1 border-t border-border">
                  <span className="text-ink font-medium">Effective Level:</span>
                  <span className="text-growth font-semibold capitalize">{riskProfile.effective_level}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs font-sans text-muted-ink py-2">
                No risk profile assessed yet. Defaulting to Moderate.
              </p>
            )}
          </div>

          <button
            onClick={handleOpenQuiz}
            className="mt-3 w-full py-1.5 px-3 text-xs font-mono rounded-sm border border-border text-ink hover:bg-canvas transition-colors flex items-center justify-center gap-1.5"
          >
            <HelpCircle className="w-3.5 h-3.5 text-muted-ink" />
            {riskProfile ? 'Retake Risk Questionnaire' : 'Assess Risk (8 Qs)'}
          </button>
        </Card>
      </div>

      {/* 5. Main Layout with Docked Right Side Panel (No floating chat bubble) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Recommendations Ledger List (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="text-xl font-serif text-ink">Actionable Recommendations ({recommendations.length})</h2>
            <span className="text-xs font-mono text-muted-ink">Priority Order</span>
          </div>

          {loading ? (
            <Card className="text-center py-12 text-xs font-mono text-muted-ink">
              <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-2 text-ink" />
              Evaluating advisor engine rules...
            </Card>
          ) : recommendations.length === 0 ? (
            <Card className="text-center py-12 text-xs font-sans text-muted-ink">
              No recommendations generated yet. Run the advisory engine above to evaluate rules.
            </Card>
          ) : (
            recommendations.map((rec) => {
              const isSelected = selectedRec?.recommendation_id === rec.recommendation_id;
              const isExpanded = !!expandedRecs[rec.recommendation_id];

              return (
                <Card
                  key={rec.recommendation_id}
                  onClick={() => setSelectedRecId(rec.recommendation_id)}
                  className={`cursor-pointer transition-all space-y-3 ${
                    isSelected
                      ? 'border-l-4 border-ink bg-surface shadow-none'
                      : 'border-border bg-surface hover:border-ink/50'
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-border pb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-medium text-ink">
                        #{rec.priority_rank}
                      </span>
                      <StatusPill
                        label={getLabel(rec.rec_type)}
                        variant="neutral"
                      />
                    </div>
                    <StatusPill
                      label={rec.status}
                      variant={
                        rec.status === 'accepted'
                          ? 'growth'
                          : rec.status === 'rejected'
                          ? 'liability'
                          : 'neutral'
                      }
                    />
                  </div>

                  <div>
                    <h3 className="text-base font-serif text-ink leading-snug">
                      {rec.action}
                    </h3>
                    <p className="text-xs font-sans text-muted-ink mt-1.5 leading-relaxed">
                      {rec.reason}
                    </p>
                  </div>

                  {/* Decision Buttons */}
                  <div className="pt-2 border-t border-border flex items-center justify-between">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setExpandedRecs((prev) => ({
                          ...prev,
                          [rec.recommendation_id]: !prev[rec.recommendation_id],
                        }));
                      }}
                      className="text-xs font-mono text-muted-ink hover:text-ink flex items-center gap-1"
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      <span>{isExpanded ? 'Less' : 'Details'}</span>
                    </button>

                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleStatusChange(rec.recommendation_id, 'accepted')}
                        disabled={rec.status === 'accepted'}
                        className={`inline-flex items-center gap-1 text-xs font-mono px-2.5 py-1 rounded-sm border transition-colors ${
                          rec.status === 'accepted'
                            ? 'bg-growth text-surface border-growth'
                            : 'bg-surface hover:bg-canvas text-ink border-border'
                        }`}
                      >
                        <Check className={`w-3 h-3 ${rec.status === 'accepted' ? 'text-surface' : 'text-growth'}`} />
                        Accept
                      </button>
                      <button
                        onClick={() => handleStatusChange(rec.recommendation_id, 'rejected')}
                        disabled={rec.status === 'rejected'}
                        className={`inline-flex items-center gap-1 text-xs font-mono px-2.5 py-1 rounded-sm border transition-colors ${
                          rec.status === 'rejected'
                            ? 'bg-liability text-surface border-liability'
                            : 'bg-surface hover:bg-canvas text-ink border-border'
                        }`}
                      >
                        <XCircle className={`w-3 h-3 ${rec.status === 'rejected' ? 'text-surface' : 'text-liability'}`} />
                        Dismiss
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>

        {/* Right Column: Docked Advisory Side Panel (5 cols) */}
        <div className="lg:col-span-5 sticky top-6 space-y-4">
          <Card className="border border-ink bg-surface space-y-4">
            <div className="border-b border-border pb-3">
              <span className="text-[10px] font-mono tracking-widest uppercase text-muted-ink block">
                Docked Advisory Inspector
              </span>
              <h3 className="text-xl font-serif text-ink mt-0.5">
                {selectedRec ? `Inspection: Recommendation #${selectedRec.priority_rank}` : 'Inspection'}
              </h3>
            </div>

            {selectedRec ? (
              <div className="space-y-4 text-xs">
                {/* Action & Reason */}
                <div>
                  <span className="text-[10px] font-mono uppercase text-muted-ink block">Selected Item Reason</span>
                  <p className="font-sans text-xs text-muted-ink mt-1.5 leading-relaxed">{selectedRec.reason}</p>
                </div>

                {/* Explanation */}
                {selectedRec.explanation_text && (
                  <div className="bg-canvas border border-border rounded-sm p-3 space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-mono text-muted-ink">
                      <span>VERIFIED PLAIN EXPLANATION</span>
                      <span>Source: {selectedRec.explanation_source || 'template'}</span>
                    </div>
                    <p className="font-sans text-ink leading-relaxed">
                      &quot;{selectedRec.explanation_text}&quot;
                    </p>
                  </div>
                )}

                {/* Grounded 'Based on' User Records List */}
                <div className="border-t border-border pt-3 space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                    Based on Your Actual Records (Audit Inputs)
                  </span>
                  {selectedRec.inputs_snapshot && Object.keys(selectedRec.inputs_snapshot).length > 0 ? (
                    <div className="bg-canvas border border-border rounded-sm p-2.5 space-y-1.5 font-mono text-[11px]">
                      {Object.entries(selectedRec.inputs_snapshot).map(([key, val]) => {
                        const formatted = formatSnapshotInput(key, val);
                        return (
                          <div key={key} className="flex justify-between text-ink border-b border-border/40 pb-1 last:border-b-0 last:pb-0">
                            <span className="text-muted-ink">{formatted.label}:</span>
                            <span className="font-medium">{formatted.value}</span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="bg-canvas border border-border rounded-sm p-2 text-muted-ink font-mono text-[11px]">
                      Inputs evaluated from live financial snapshot and risk engine.
                    </div>
                  )}
                </div>

                {/* Assumptions */}
                {selectedRec.assumptions && selectedRec.assumptions.length > 0 && (
                  <div className="border-t border-border pt-3">
                    <span className="text-[10px] font-mono uppercase tracking-wide text-muted-ink block mb-1">
                      Underlying Assumptions
                    </span>
                    <ul className="list-disc list-inside space-y-1 font-sans text-muted-ink">
                      {selectedRec.assumptions.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Risks & Limitations */}
                {selectedRec.risks && selectedRec.risks.length > 0 && (
                  <div className="border-t border-border pt-3">
                    <span className="text-[10px] font-mono uppercase tracking-wide text-liability block mb-1">
                      Identified Risks & Trade-Offs
                    </span>
                    <ul className="list-disc list-inside space-y-1 font-sans text-muted-ink">
                      {selectedRec.risks.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Alternatives Considered */}
                {selectedRec.alternatives && selectedRec.alternatives.length > 0 && (
                  <div className="border-t border-border pt-3">
                    <span className="text-[10px] font-mono uppercase tracking-wide text-muted-ink block mb-1">
                      Alternatives Considered
                    </span>
                    <ul className="list-disc list-inside space-y-1 font-sans text-muted-ink">
                      {selectedRec.alternatives.map((alt, i) => (
                        <li key={i}>{alt}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Review Trigger */}
                {selectedRec.review_trigger && (
                  <div className="border-t border-border pt-3 text-[11px] font-mono text-muted-ink">
                    <strong className="text-ink">Review Trigger:</strong> {selectedRec.review_trigger}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs font-sans text-muted-ink py-8 text-center">
                Select a recommendation from the ledger to inspect grounded inputs, assumptions, and risks.
              </p>
            )}
          </Card>
        </div>
      </div>

      {/* 6. Interactive Risk Questionnaire Modal (FR-22) */}
      {showQuestionnaire && (
        <div className="fixed inset-0 z-50 bg-ink/40 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-surface border border-ink rounded-sm max-w-2xl w-full max-h-[90vh] flex flex-col">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
                  Deterministic Risk Profiler
                </span>
                <h3 className="text-xl font-serif text-ink mt-0.5">
                  Risk Tolerance & Capacity Assessment
                </h3>
              </div>
              <button
                onClick={() => setShowQuestionnaire(false)}
                className="text-xs font-mono text-muted-ink hover:text-ink"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleQuizSubmit} className="p-6 space-y-6 overflow-y-auto flex-1 text-xs">
              {questions.map((q, idx) => (
                <div key={q.id} className="space-y-2 border-b border-border pb-4 last:border-b-0">
                  <div className="font-sans font-medium text-ink">
                    <span className="font-mono text-muted-ink mr-1.5">Q{idx + 1}.</span>
                    {q.text}
                  </div>
                  <div className="space-y-1.5 pl-4">
                    {q.options.map((opt) => (
                      <label
                        key={opt.score}
                        className={`flex items-center gap-2 p-2 rounded-sm border cursor-pointer transition-colors ${
                          questionAnswers[q.id] === opt.score
                            ? 'bg-canvas border-ink text-ink font-medium'
                            : 'border-border text-muted-ink hover:text-ink'
                        }`}
                      >
                        <input
                          type="radio"
                          name={q.id}
                          checked={questionAnswers[q.id] === opt.score}
                          onChange={() =>
                            setQuestionAnswers((prev) => ({ ...prev, [q.id]: opt.score }))
                          }
                          className="accent-ink"
                        />
                        <span className="font-sans">{opt.text}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}

              <div className="flex justify-end gap-3 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowQuestionnaire(false)}
                  className="px-4 py-2 border border-border text-muted-ink rounded-sm font-mono text-xs hover:text-ink"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingQuiz}
                  className="px-4 py-2 bg-ink text-canvas rounded-sm font-mono text-xs hover:bg-muted-ink disabled:opacity-50"
                >
                  {submittingQuiz ? 'Scoring...' : 'Save Assessment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Advisor;
