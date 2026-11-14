import React, { useEffect, useState, useTransition } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileQuestion,
  HelpCircle,
  Info,
  RefreshCw,
  Shield,
  ShieldAlert,
  Sparkles,
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

function formatCurrency(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(val);
}

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

  // Expanded cards
  const [expandedRecs, setExpandedRecs] = useState<Record<number, boolean>>({});
  const [showCapacitySteps, setShowCapacitySteps] = useState<boolean>(false);

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
        setRecommendations(recsRes.recommendations || []);
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
      // Pre-populate with existing answers if present
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
      // Auto-refresh recommendations with new risk profile
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
        if (res.disclaimer) setDisclaimer(res.disclaimer);
      });
      // also refresh capacity
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

  const toggleExpand = (recId: number) => {
    setExpandedRecs((prev) => ({ ...prev, [recId]: !prev[recId] }));
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* 1. Statutory Compliance Disclaimer Banner (NFR-7) */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 shadow-xs">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 leading-relaxed">
          <span className="font-bold tracking-wide uppercase text-amber-800 mr-1">
            Decision Support Notice:
          </span>
          {disclaimer}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 2. Top Header & Action Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            Explainable Financial Advisor
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic rule engine with verifiable AI explanations and full audit trail
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-xs disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Evaluating Engine Rules...' : 'Generate Recommendations'}
          </button>
        </div>
      </div>

      {/* 3. Data Insufficient Warning (FR-29) */}
      {capacity?.status === 'insufficient_data' && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-orange-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-base font-bold text-orange-950">
                Insufficient Baseline Financial Data (FR-29)
              </h3>
              <p className="text-sm text-orange-800 mt-1">
                Vault does not estimate or guess numbers when baseline records are missing. Please enter:
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 text-xs text-orange-900 font-medium">
                {capacity.missing_items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
              <div className="mt-4">
                <Link
                  to="/finances"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-orange-950 bg-orange-100 hover:bg-orange-200 border border-orange-300 px-3 py-1.5 rounded-lg transition-colors"
                >
                  Enter Financial Baseline
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Top Metrics Cards: Capacity & Risk Profile */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Investment Capacity Card (FR-21) */}
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Monthly Investment Capacity (FR-21)
              </span>
              {capacity?.status === 'ok' && (
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Sustainable
                </span>
              )}
              {capacity?.status === 'blocked' && (
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                  Blocked by Gate
                </span>
              )}
              {capacity?.status === 'insufficient_data' && (
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-orange-50 text-orange-700 border border-orange-200">
                  Data Needed
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-3">
              <span className="text-3xl md:text-4xl font-extrabold text-slate-900">
                {capacity?.status === 'insufficient_data'
                  ? 'No Data'
                  : formatCurrency(capacity?.capacity)}
              </span>
              <span className="text-sm font-medium text-slate-500">/ month</span>
            </div>

            {/* Blocked reason badges */}
            {capacity?.status === 'blocked' && capacity.reason_codes.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {capacity.reason_codes.map((code) => (
                  <span
                    key={code}
                    className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-rose-100 text-rose-800"
                  >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Gate: {code.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}

            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              {capacity?.status === 'blocked'
                ? 'Investment capacity is restricted to ₹0.00 until safety thresholds (emergency fund or high-interest liabilities) are resolved.'
                : capacity?.status === 'ok'
                ? 'Estimated sustainable monthly allocation after covering essential burn, loan EMIs, goal contributions, emergency top-ups, and retaining a 10% cash flow buffer.'
                : 'Enter your income and expenses in the Finances tab to compute your sustainable capacity.'}
            </p>
          </div>

          {/* Breakdown Steps Toggle */}
          {capacity?.steps && capacity.steps.length > 0 && (
            <div className="mt-5 pt-4 border-t border-slate-100">
              <button
                onClick={() => setShowCapacitySteps(!showCapacitySteps)}
                className="w-full flex items-center justify-between text-xs font-semibold text-indigo-600 hover:text-indigo-800"
              >
                <span>{showCapacitySteps ? 'Hide Step-by-Step Breakdown' : 'Show Step-by-Step Breakdown (Spec 6.7)'}</span>
                {showCapacitySteps ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showCapacitySteps && (
                <div className="mt-3 space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  {capacity.steps.map((st) => (
                    <div key={st.step_number} className="flex items-center justify-between text-xs py-1 border-b border-slate-200/60 last:border-0">
                      <div>
                        <span className="font-bold text-slate-800">
                          {st.step_number}. {st.name}
                        </span>
                        <p className="text-[11px] text-slate-500">{st.description}</p>
                      </div>
                      <span className="font-mono font-semibold text-slate-900 ml-4">
                        {formatCurrency(st.value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Risk Profile Card (FR-22) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Risk Profile (FR-22)
              </span>
              <Shield className="w-5 h-5 text-indigo-500" />
            </div>

            {riskProfile ? (
              <div className="space-y-3">
                <div>
                  <span className="text-xs text-slate-500">Effective Level</span>
                  <div className="text-2xl font-extrabold text-slate-900 capitalize">
                    {riskProfile.effective_level}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Tolerance:</span>
                    <span className="font-semibold text-slate-800 capitalize">
                      {riskProfile.tolerance_level} ({riskProfile.score}/32)
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Capacity:</span>
                    <span className="font-semibold text-slate-800 capitalize">
                      {riskProfile.capacity_level}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500">
                  Effective level is the lower of your tolerance and financial capacity cap (Spec 6.8).
                </p>
              </div>
            ) : (
              <div className="py-4 text-center">
                <FileQuestion className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-xs text-slate-600 mb-3">
                  No risk profile assessed yet. Defaulting to Moderate.
                </p>
              </div>
            )}
          </div>

          <button
            onClick={handleOpenQuiz}
            className="mt-4 w-full py-2 px-3 text-xs font-semibold rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center gap-1.5"
          >
            <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
            {riskProfile ? 'Retake Questionnaire (8 Qs)' : 'Take Risk Questionnaire'}
          </button>
        </div>
      </div>

      {/* 5. Explainable Recommendations List (FR-23, FR-24, FR-25, FR-26) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            Actionable Recommendations
            <span className="text-xs font-normal text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
              {recommendations.length} Active
            </span>
          </h2>
          <span className="text-xs text-slate-500">Priority order (highest impact first)</span>
        </div>

        {loading ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-500">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
            Loading advisor engine recommendations...
          </div>
        ) : recommendations.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-500">
            <Sparkles className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-slate-700">No Recommendations Generated Yet</h3>
            <p className="text-xs text-slate-500 mt-1">
              Click &quot;Generate Recommendations&quot; above to run the deterministic rule engine.
            </p>
          </div>
        ) : (
          recommendations.map((rec) => {
            const isExpanded = !!expandedRecs[rec.recommendation_id];
            return (
              <div
                key={rec.recommendation_id}
                className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs transition-all hover:border-slate-300 space-y-4"
              >
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold flex items-center justify-center">
                      #{rec.priority_rank}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono uppercase tracking-wide">
                      {rec.rec_type.replace(/_/g, ' ')}
                    </span>
                  </div>

                  {/* Decision status badge */}
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${
                        rec.status === 'accepted'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : rec.status === 'rejected'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      }`}
                    >
                      Status: {rec.status}
                    </span>
                  </div>
                </div>

                {/* Main Action & Reason */}
                <div>
                  <h3 className="text-base md:text-lg font-bold text-slate-900 leading-snug">
                    {rec.action}
                  </h3>
                  <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                    {rec.reason}
                  </p>
                </div>

                {/* Plain-Language Explanation Callout (FR-25, Spec 6.10) */}
                {rec.explanation_text && (
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        Plain-Language Explanation (FR-25)
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                        Source: {rec.explanation_source === 'llm' ? 'AI (Number-Guard Verified)' : 'Template Fallback'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed italic">
                      &quot;{rec.explanation_text}&quot;
                    </p>
                  </div>
                )}

                {/* Collapsible Explainability Sections (FR-24) */}
                {isExpanded && (
                  <div className="pt-3 border-t border-slate-100 space-y-3 text-xs">
                    {/* Assumptions */}
                    {rec.assumptions && rec.assumptions.length > 0 && (
                      <div>
                        <span className="font-bold text-slate-700 uppercase tracking-wide text-[10px]">
                          Assumptions:
                        </span>
                        <ul className="list-disc list-inside mt-1 text-slate-600 space-y-0.5">
                          {rec.assumptions.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Risks & Limitations */}
                    {rec.risks && rec.risks.length > 0 && (
                      <div>
                        <span className="font-bold text-slate-700 uppercase tracking-wide text-[10px]">
                          Risks & Trade-Offs:
                        </span>
                        <ul className="list-disc list-inside mt-1 text-slate-600 space-y-0.5">
                          {rec.risks.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Alternatives Considered */}
                    {rec.alternatives && rec.alternatives.length > 0 && (
                      <div>
                        <span className="font-bold text-slate-700 uppercase tracking-wide text-[10px]">
                          Alternatives:
                        </span>
                        <ul className="list-disc list-inside mt-1 text-slate-600 space-y-0.5">
                          {rec.alternatives.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Review Trigger */}
                    {rec.review_trigger && (
                      <div className="flex items-baseline gap-1.5 text-slate-700">
                        <Info className="w-3.5 h-3.5 text-indigo-500 flex-shrink-0 self-center" />
                        <span>
                          <strong className="text-slate-800">Review Trigger:</strong>{' '}
                          {rec.review_trigger}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Footer Controls: Decision & Toggle Details */}
                <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
                  <button
                    onClick={() => toggleExpand(rec.recommendation_id)}
                    className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp className="w-4 h-4" /> Hide Details
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-4 h-4" /> View Assumptions & Risks (FR-24)
                      </>
                    )}
                  </button>

                  {/* FR-26: Decision Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleStatusChange(rec.recommendation_id, 'accepted')}
                      disabled={rec.status === 'accepted'}
                      className={`inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                        rec.status === 'accepted'
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-white hover:bg-emerald-50 text-slate-700 border-slate-200'
                      }`}
                    >
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      Accept
                    </button>
                    <button
                      onClick={() => handleStatusChange(rec.recommendation_id, 'rejected')}
                      disabled={rec.status === 'rejected'}
                      className={`inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                        rec.status === 'rejected'
                          ? 'bg-rose-600 text-white border-rose-600'
                          : 'bg-white hover:bg-rose-50 text-slate-700 border-slate-200'
                      }`}
                    >
                      <XCircle className="w-3.5 h-3.5 text-rose-500" />
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 6. Interactive Risk Questionnaire Modal (FR-22) */}
      {showQuestionnaire && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-xl">
            <div className="p-6 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Risk Tolerance Questionnaire (FR-22)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  8 standardized questions to evaluate your risk appetite and capacity
                </p>
              </div>
              <button
                onClick={() => setShowQuestionnaire(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleQuizSubmit} className="p-6 overflow-y-auto space-y-6 flex-1">
              {questions.map((q, qIndex) => (
                <div key={q.id} className="space-y-2">
                  <label className="block text-sm font-bold text-slate-800">
                    {qIndex + 1}. {q.text}
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    {q.options.map((opt) => {
                      const isSelected = questionAnswers[q.id] === opt.score;
                      return (
                        <button
                          type="button"
                          key={opt.score}
                          onClick={() =>
                            setQuestionAnswers((prev) => ({
                              ...prev,
                              [q.id]: opt.score,
                            }))
                          }
                          className={`text-left p-3 rounded-xl border text-xs transition-all flex items-center justify-between ${
                            isSelected
                              ? 'border-indigo-600 bg-indigo-50/50 text-indigo-950 font-semibold'
                              : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                          }`}
                        >
                          <span>{opt.text}</span>
                          <span
                            className={`w-4 h-4 rounded-full border flex items-center justify-center ml-2 flex-shrink-0 ${
                              isSelected
                                ? 'border-indigo-600 bg-indigo-600 text-white'
                                : 'border-slate-300'
                            }`}
                          >
                            {isSelected && <CheckCircle className="w-3.5 h-3.5" />}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowQuestionnaire(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingQuiz || Object.keys(questionAnswers).length < questions.length}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold disabled:opacity-50"
                >
                  {submittingQuiz ? 'Calculating Profile...' : 'Save & Assess Risk'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
