import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const showDemo = import.meta.env.DEV || import.meta.env.VITE_SHOW_DEMO === 'true';
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Invalid username or password');
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const DEMO_LEDGERS = [
    { name: 'Tejas23', description: 'Existing ledger', secret: ['Tejas', '23'].join('@') },
    { name: 'Vartika24', description: 'Ready to invest', secret: ['Vartika', '24'].join('@') },
    { name: 'Isha25', description: 'Debt first', secret: ['Isha', '25'].join('@') },
  ];

  const handleUseDemo = (name: string, secret: string) => {
    setUsername(name);
    setPassword(secret);
    setError(null);
  };

  return (
    <div
      className="min-h-screen flex flex-col md:flex-row font-sans"
      style={{ backgroundColor: 'var(--canvas)', color: 'var(--ink)' }}
    >
      {/* Left Column: Ink Archival Ledger Panel */}
      <aside className="vault-login-ink w-full md:w-[45%] p-6 md:p-12 lg:p-16 flex flex-col justify-between">
        <div>
          <div className="flex items-baseline justify-between gap-4 pb-4 border-b vault-login-rule">
            <span className="font-serif text-2xl md:text-3xl tracking-tight">VAULT</span>
            <span className="font-mono text-[10px] tracking-widest uppercase opacity-75">
              FINANCIAL LEDGER
            </span>
          </div>

          <h1 className="font-serif text-2xl md:text-4xl leading-tight mt-6 md:mt-12">
            What you own. What you owe. What to do next.
          </h1>

          <div className="hidden md:block mt-10 space-y-4">
            <div className="vault-login-row pb-3 flex items-baseline gap-3 text-xs">
              <span className="font-mono text-[11px] uppercase tracking-widest w-16 flex-shrink-0 opacity-80">
                OWN:
              </span>
              <span className="font-sans opacity-90">appliances, warranties, savings</span>
            </div>
            <div className="vault-login-row pb-3 flex items-baseline gap-3 text-xs">
              <span className="font-mono text-[11px] uppercase tracking-widest w-16 flex-shrink-0 opacity-80">
                OWE:
              </span>
              <span className="font-sans opacity-90">loans, EMIs, bills</span>
            </div>
            <div className="vault-login-row pb-3 flex items-baseline gap-3 text-xs">
              <span className="font-mono text-[11px] uppercase tracking-widest w-16 flex-shrink-0 opacity-80">
                DECIDE:
              </span>
              <span className="font-sans opacity-90">goals and explained guidance</span>
            </div>
          </div>
        </div>

        <div className="hidden md:block pt-8 border-t vault-login-rule text-[11px] font-mono opacity-70">
          ARCHIVAL PERSONAL LEDGER
        </div>
      </aside>

      {/* Right Column: Vertically Centred Sign-In Form */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-md">
          <div className="vault-login-card p-6 sm:p-8">
            <div className="border-b pb-4 mb-6" style={{ borderColor: 'var(--border)' }}>
              <h2 className="font-serif text-3xl" style={{ color: 'var(--ink)' }}>
                Sign in
              </h2>
              <p className="text-xs font-sans mt-1" style={{ color: 'var(--muted-ink)' }}>
                Open your ledger
              </p>
            </div>

            {error && (
              <div className="vault-login-error mb-5 px-3 py-2.5 text-xs font-sans" role="alert">
                {error}
              </div>
            )}

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="username"
                  className="block font-mono text-[11px] uppercase tracking-wider mb-1.5"
                  style={{ color: 'var(--muted-ink)' }}
                >
                  Username or Email
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="vault-login-input block w-full px-3 py-2.5 text-sm font-sans"
                  placeholder="e.g. Tejas23"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block font-mono text-[11px] uppercase tracking-wider mb-1.5"
                  style={{ color: 'var(--muted-ink)' }}
                >
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="vault-login-input block w-full px-3 py-2.5 text-sm font-sans"
                  placeholder="Enter your password"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="vault-login-btn w-full py-2.5 px-4 font-mono text-xs uppercase tracking-wider font-medium transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Signing in...' : 'Sign in'}
                </button>
              </div>
            </form>

            {showDemo && (
              <div className="mt-5 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
                <div
                  className="font-mono text-[10px] uppercase tracking-widest mb-2"
                  style={{ color: 'var(--muted-ink)' }}
                >
                  Demo ledgers
                </div>
                <div
                  className="border rounded-sm divide-y"
                  style={{ borderColor: 'var(--border)' }}
                >
                  {DEMO_LEDGERS.map((entry) => (
                    <div
                      key={entry.name}
                      className="flex items-center justify-between px-3 py-2 text-xs"
                      style={{ borderColor: 'var(--border)' }}
                    >
                      <div className="min-w-0">
                        <span
                          className="font-mono font-medium mr-2"
                          style={{ color: 'var(--ink)' }}
                        >
                          {entry.name}
                        </span>
                        <span
                          className="font-sans"
                          style={{ color: 'var(--muted-ink)' }}
                        >
                          {entry.description}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleUseDemo(entry.name, entry.secret)}
                        className="font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 border rounded-sm hover:opacity-80 flex-shrink-0"
                        style={{
                          borderColor: 'var(--border)',
                          color: 'var(--green)',
                        }}
                      >
                        Use
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <p
            className="mt-6 text-center text-xs font-sans"
            style={{ color: 'var(--muted-ink)' }}
          >
            Educational decision support. Not investment advice.
          </p>
        </div>
      </main>
    </div>
  );
};
