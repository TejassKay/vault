import React from 'react';

export type StatusVariant = 'growth' | 'liability' | 'neutral' | 'gold';

interface StatusPillProps {
  label: string;
  variant?: StatusVariant;
  className?: string;
}

export const StatusPill: React.FC<StatusPillProps> = ({
  label,
  variant = 'neutral',
  className = '',
}) => {
  const variantStyles = {
    growth: 'text-growth bg-growth/[0.08] border-growth/35',
    liability: 'text-liability bg-liability/[0.08] border-liability/35',
    gold: 'text-ink bg-gold/[0.08] border-gold/50',
    neutral: 'text-muted-ink bg-canvas border-border',
  }[variant];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-mono tracking-wide uppercase border rounded-sm font-medium ${variantStyles} ${className}`}
    >
      {label}
    </span>
  );
};

export default StatusPill;
