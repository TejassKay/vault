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
    growth: 'text-growth bg-growth/10 border-growth/30',
    liability: 'text-liability bg-liability/10 border-liability/30',
    gold: 'text-ink bg-gold/15 border-gold/40',
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
