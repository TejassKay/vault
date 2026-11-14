import React from 'react';

interface MoneyProps {
  amount: number | string | null | undefined;
  className?: string;
  showSign?: boolean;
}

export const formatINR = (value: number): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

export const Money: React.FC<MoneyProps> = ({ amount, className = '', showSign = false }) => {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return <span className={`font-mono text-muted-ink ${className}`}>—</span>;
  }

  const num = Number(amount);
  const isNegative = num < 0;
  const absFormatted = formatINR(Math.abs(num));

  // If negative or explicitly requested positive sign
  const displayValue = isNegative
    ? `-${absFormatted}`
    : showSign && num > 0
    ? `+${absFormatted}`
    : absFormatted;

  return (
    <span
      className={`font-mono tabular-nums ${
        isNegative ? 'text-liability' : ''
      } ${className}`}
      style={{ fontVariantNumeric: 'tabular-nums' }}
    >
      {displayValue}
    </span>
  );
};

export default Money;
