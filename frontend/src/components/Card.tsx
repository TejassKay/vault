import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'surface' | 'canvas' | 'ink';
  bordered?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'surface',
  bordered = true,
  ...props
}) => {
  const bg = {
    surface: 'bg-surface text-ink',
    canvas: 'bg-canvas text-ink',
    ink: 'bg-ink text-canvas',
  }[variant];

  const borderClass = bordered
    ? variant === 'ink'
      ? 'border border-ink'
      : 'border border-border'
    : '';

  return (
    <div
      className={`rounded-sm p-5 ${bg} ${borderClass} transition-colors ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
