import React from 'react';
import { CapacityStep } from '../api/advisor';
import Money from './Money';
import { getLabel } from '../lib/labels.js';

interface InvestmentCapacityBlockProps {
  status: string;
  capacity: number | null;
  capacityIfClear?: number | null;
  steps?: CapacityStep[];
  missingItems?: string[];
  reasonCodes?: string[];
  className?: string;
}

export const InvestmentCapacityBlock: React.FC<InvestmentCapacityBlockProps> = ({
  status,
  capacity,
  capacityIfClear,
  steps = [],
  missingItems = [],
  reasonCodes = [],
  className = '',
}) => {
  // Compute segments for the horizontal bar from steps if available
  // Filter steps with non-null values
  const validSteps = steps.filter((s) => s.value !== null && s.value !== undefined);
  const totalValue = validSteps.reduce((acc, s) => acc + Math.abs(Number(s.value)), 0) || 1;

  return (
    <div className={`bg-ink text-canvas rounded-sm p-6 flex flex-col justify-between border border-ink ${className}`}>
      <div>
        <div className="flex items-center justify-between border-b border-muted-ink/40 pb-3">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-muted-ink block">
              Investment Capacity
            </span>
            <span className="text-xs text-canvas/70 font-sans">Monthly investable surplus after gates & buffers</span>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 rounded-sm border border-canvas/20 uppercase tracking-wide">
            Status: {getLabel(status)}
          </span>
        </div>

        <div className="my-6">
          {status === 'insufficient_data' ? (
            <div>
              <div className="text-2xl font-serif text-canvas/80">Insufficient Data</div>
              <p className="text-xs font-sans text-canvas/60 mt-1">
                Record your baseline income and expenses before capacity can be computed.
              </p>
              {missingItems.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {missingItems.map((item, i) => (
                    <span key={i} className="text-xs font-mono bg-canvas/10 px-2 py-0.5 rounded-sm border border-canvas/15 text-canvas/80">
                      {getLabel(item)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="flex items-baseline gap-3">
                <span className="text-4xl md:text-5xl font-mono tabular-nums font-semibold tracking-tight text-canvas">
                  <Money amount={capacity} className="text-canvas" />
                </span>
                <span className="text-xs font-mono text-muted-ink">/ month</span>
              </div>
              {status === 'blocked' && capacityIfClear !== null && capacityIfClear !== undefined && (
                <p className="text-xs font-sans text-liability mt-1.5 flex items-center gap-1.5">
                  <span>Capacity if gates cleared:</span>
                  <Money amount={capacityIfClear} className="font-semibold text-liability" />
                </p>
              )}
              {reasonCodes.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {reasonCodes.map((rc, i) => (
                    <span key={i} className="text-[11px] font-mono text-liability bg-liability/20 border border-liability/40 px-2 py-0.5 rounded-sm">
                      {getLabel(rc)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Stacked Horizontal Bar (Section 6.7) */}
        {validSteps.length > 0 && (
          <div className="space-y-2 mt-4 pt-4 border-t border-muted-ink/30">
            <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block">
              Capacity Composition Breakdown
            </span>
            <div className="h-3 w-full bg-canvas/10 rounded-sm overflow-hidden flex border border-canvas/20">
              {validSteps.map((step, idx) => {
                const widthPct = Math.max(8, (Math.abs(Number(step.value)) / totalValue) * 100);
                const barColors = [
                  'bg-growth',
                  'bg-gold',
                  'bg-liability',
                  'bg-canvas/50',
                  'bg-muted-ink',
                ];
                return (
                  <div
                    key={idx}
                    style={{ width: `${widthPct}%` }}
                    className={`${barColors[idx % barColors.length]} border-r border-ink/40 last:border-r-0`}
                    title={`${step.name}: ${step.value}`}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Transparent Math: Step-by-Step Equation */}
        {validSteps.length > 0 && (
          <div className="mt-4 space-y-1.5 text-xs font-mono">
            <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink block mb-1">
              Deterministic Calculation Steps (Real API Values)
            </span>
            <div className="bg-canvas/5 rounded-sm p-3 border border-canvas/10 space-y-1.5">
              {validSteps.map((s) => (
                <div key={s.step_number} className="flex items-center justify-between text-canvas/90">
                  <span className="text-canvas/70 font-sans text-xs flex items-center gap-1.5">
                    <span className="text-[10px] font-mono text-muted-ink">#{s.step_number}</span>
                    {s.name}
                  </span>
                  <div className="text-right">
                    <Money amount={s.value} className="text-canvas font-mono" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InvestmentCapacityBlock;
