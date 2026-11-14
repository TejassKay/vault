import React, { useEffect, useState } from 'react';
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
  PanelLeftClose,
  PanelLeftOpen,
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
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('vault_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('vault_sidebar_collapsed', String(next));
      } catch {
        // Ignore storage errors
      }
      return next;
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleCollapsed();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-canvas text-ink font-sans selection:bg-gold/20 selection:text-ink">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between p-4 bg-ink text-canvas border-b border-canvas/15">
        <div className="flex items-center gap-2.5">
          <Shield className="w-5 h-5 text-gold" />
          <span className="font-serif text-lg tracking-wide font-medium text-canvas">VAULT Ledger</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCommandBarOpen(true)}
            className="p-1.5 border border-canvas/20 rounded-sm text-canvas hover:bg-canvas/10"
            aria-label="Open command bar"
          >
            <Search className="w-4 h-4" />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 border border-canvas/20 rounded-sm text-canvas hover:bg-canvas/10"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-ink/50 z-30 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Dark Forest-Slate Sidebar: Off-canvas drawer on <768px, collapsible rail on >=768px */}
      <aside
        className={`vault-sidebar fixed inset-y-0 left-0 z-40 w-[260px] transform transition-all duration-200 ease-in-out flex flex-col justify-between flex-shrink-0 md:static md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        } ${collapsed ? 'md:w-[64px]' : 'md:w-[260px]'}`}
      >
        <div>
          {/* Logo / Brand header + Collapse Toggle */}
          <div className={`vault-sidebar-header p-4 flex items-center ${collapsed ? 'md:justify-center md:px-2' : 'justify-between'}`}>
            <div className={`flex items-center gap-3 min-w-0 ${collapsed ? 'md:hidden' : ''}`}>
              <div className="w-7 h-7 rounded-sm bg-canvas/10 border border-gold/50 text-canvas flex items-center justify-center font-serif text-sm flex-shrink-0">
                V
              </div>
              <div className="truncate">
                <span className="font-serif text-xl tracking-tight text-canvas font-semibold">VAULT</span>
                <span className="vault-sidebar-muted block text-[10px] font-mono tracking-widest uppercase">
                  Financial Ledger
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={toggleCollapsed}
                className="vault-sidebar-muted hidden md:flex items-center justify-center p-1.5 rounded-sm hover:text-canvas hover:bg-canvas/10 transition-colors"
                title={collapsed ? 'Expand sidebar (⌘B)' : 'Collapse sidebar (⌘B)'}
                aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="vault-sidebar-muted md:hidden p-1.5 rounded-sm hover:text-canvas hover:bg-canvas/10"
                aria-label="Close navigation menu"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-2.5 space-y-0.5">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  title={collapsed ? item.name : undefined}
                  className={`flex items-center gap-2.5 py-2 rounded-sm text-xs transition-colors ${
                    collapsed ? 'md:justify-center md:px-0 px-3' : 'px-3'
                  } ${
                    isActive
                      ? 'vault-nav-item--active'
                      : 'vault-nav-item'
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'vault-nav-icon--active' : ''}`} />
                  <span className={`tracking-tight truncate ${collapsed ? 'md:hidden' : ''}`}>
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Sign Out Footer */}
        <div className="vault-sidebar-footer p-3">
          <div className={`flex items-center ${collapsed ? 'md:flex-col md:gap-2 justify-between' : 'justify-between'}`}>
            <div className={`flex items-center gap-2 min-w-0 ${collapsed ? 'md:justify-center' : ''}`}>
              <div
                className="w-7 h-7 rounded-sm bg-canvas/10 border border-canvas/20 text-canvas flex items-center justify-center font-mono text-xs flex-shrink-0"
                title={collapsed ? `${user?.name || 'Tejas23'} (${user?.email || 'tejas23@vault.local'})` : undefined}
              >
                <User className="w-3.5 h-3.5" />
              </div>
              <div className={`truncate ${collapsed ? 'md:hidden' : ''}`}>
                <p className="text-xs font-mono font-medium text-canvas truncate">
                  {user?.name || 'Tejas23'}
                </p>
                <p className="vault-sidebar-muted text-[10px] font-mono truncate">
                  {user?.email || 'tejas23@vault.local'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              aria-label="Sign out"
              className="vault-sidebar-muted p-1.5 hover:text-canvas hover:bg-canvas/10 border border-transparent hover:border-canvas/20 rounded-sm transition-colors flex-shrink-0"
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
