import React, { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Receipt,
  WalletCards,
  Target,
  Sparkles,
  Activity,
  Compass,
  LogOut,
  User,
  Menu,
  X,
  Search,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import CommandBar from './CommandBar';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Onboarding', href: '/onboarding', icon: Compass },
  { name: 'Assets & Bills', href: '/assets', icon: Receipt },
  { name: 'Finances', href: '/finances', icon: WalletCards },
  { name: 'Goals', href: '/goals', icon: Target },
  { name: 'Advisor', href: '/advisor', icon: Sparkles },
  { name: 'System Health', href: '/health', icon: Activity },
];

export const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [commandBarOpen, setCommandBarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-canvas text-ink font-sans selection:bg-gold/20 selection:text-ink">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between p-4 bg-surface border-b border-border">
        <div className="flex items-center gap-2.5">
          <Shield className="w-5 h-5 text-growth" />
          <span className="font-serif text-lg tracking-wide font-medium text-ink">VAULT Ledger</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCommandBarOpen(true)}
            className="p-1.5 border border-border rounded-sm text-ink hover:bg-canvas"
            aria-label="Open command bar"
          >
            <Search className="w-4 h-4" />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 border border-border rounded-sm text-ink hover:bg-canvas"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Sidebar for Desktop & Collapsible for Mobile */}
      <aside
        className={`${
          mobileMenuOpen ? 'block' : 'hidden'
        } md:flex w-full md:w-64 bg-surface border-r border-border flex-shrink-0 flex-col justify-between z-30`}
      >
        <div>
          {/* Logo / Brand header */}
          <div className="p-5 flex items-center justify-between border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-sm bg-ink text-canvas flex items-center justify-center font-serif text-sm">
                V
              </div>
              <div>
                <span className="font-serif text-xl tracking-tight text-ink font-semibold">VAULT</span>
                <span className="block text-[10px] font-mono tracking-widest text-muted-ink uppercase">
                  Financial Ledger
                </span>
              </div>
            </div>
            <button
              onClick={() => setCommandBarOpen(true)}
              className="hidden md:flex items-center gap-1 text-[10px] font-mono text-muted-ink bg-canvas px-1.5 py-1 rounded-sm border border-border hover:border-ink hover:text-ink transition-colors"
              title="Command Bar (Cmd+K)"
            >
              <span>⌘K</span>
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-0.5">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-sm text-xs transition-colors ${
                    isActive
                      ? 'bg-canvas text-ink font-medium border-l-2 border-ink'
                      : 'text-muted-ink hover:text-ink hover:bg-canvas/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-ink' : 'text-muted-ink'}`} />
                  <span className="tracking-tight">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Sign Out Footer */}
        <div className="p-3 border-t border-border bg-canvas/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-6 h-6 rounded-sm bg-surface border border-border text-ink flex items-center justify-center font-mono text-xs">
                <User className="w-3.5 h-3.5" />
              </div>
              <div className="truncate">
                <p className="text-xs font-mono font-medium text-ink truncate">
                  {user?.name || 'Tejas23'}
                </p>
                <p className="text-[10px] font-mono text-muted-ink truncate">
                  {user?.email || 'tejas23@vault.local'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              aria-label="Sign out"
              className="p-1.5 text-muted-ink hover:text-liability hover:bg-surface border border-transparent hover:border-border rounded-sm transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-canvas">
        {/* Archival Top Ledger Header Bar */}
        <header className="hidden md:flex bg-surface border-b border-border px-8 py-3.5 items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono uppercase tracking-widest text-muted-ink">
              Archival Ledger & Decision Record
            </span>
            <span className="text-border">|</span>
            <button
              onClick={() => setCommandBarOpen(true)}
              className="flex items-center gap-2 text-xs font-mono text-muted-ink bg-canvas px-2.5 py-1 rounded-sm border border-border hover:border-ink hover:text-ink transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Jump to record...</span>
              <kbd className="px-1 text-[10px] bg-surface border border-border rounded-xs">⌘K</kbd>
            </button>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-xs font-mono text-growth bg-growth/5 border border-growth/30 px-2.5 py-1 rounded-sm flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-growth" />
              <span>Ledger: <strong>{user?.name || 'Tejas23'}</strong></span>
            </div>
            <div className="text-xs font-mono text-muted-ink bg-canvas px-2.5 py-1 rounded-sm border border-border">
              Standard: INR (₹)
            </div>
          </div>
        </header>

        <div className="p-6 md:p-8 flex-1">
          <Outlet />
        </div>
      </main>

      {/* Command Bar Modal */}
      <CommandBar
        isOpen={commandBarOpen}
        onClose={() => setCommandBarOpen(false)}
      />
    </div>
  );
};

export default Layout;
