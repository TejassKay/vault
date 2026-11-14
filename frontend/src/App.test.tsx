import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import App from './App';
import { setAuthToken, removeAuthToken } from './api/client';

describe('App Component (NFR-5, NFR-6)', () => {
  beforeEach(() => {
    localStorage.clear();
    removeAuthToken();
    window.history.pushState({}, '', '/');
  });

  it('renders login screen when unauthenticated', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByText('ARCHIVAL PERSONAL LEDGER')).toBeInTheDocument();
  });

  it('renders navigation bar and dashboard when authenticated', async () => {
    setAuthToken('mock-test-jwt-token');
    await act(async () => {
      render(<App />);
    });
    expect(screen.getByText('VAULT')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Onboarding')).toBeInTheDocument();
    expect(screen.getByText('Advisor')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });
});
