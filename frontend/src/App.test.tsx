import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App Component (NFR-5, NFR-6)', () => {
  it('renders navigation bar with brand name and links', () => {
    render(<App />);
    expect(screen.getByText('VAULT')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });

  it('renders default dashboard placeholder content', () => {
    render(<App />);
    expect(screen.getByText('Phase 0 Scaffold Active')).toBeInTheDocument();
    expect(screen.getByText('Emergency Coverage')).toBeInTheDocument();
  });
});
