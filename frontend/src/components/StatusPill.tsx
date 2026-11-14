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
    growth: 'vault-pill--growth',
    liability: 'vault-pill--liability',
    gold: 'vault-pill--gold',
    neutral: 'vault-pill--neutral',
  }[variant];

  return (
    <span
      className={`vault-pill inline-flex items-center px-2 py-0.5 text-xs tracking-wide rounded-sm font-medium ${variantStyles} ${className}`}
    >
      {label}
    </span>
  );
};

export default StatusPill;
