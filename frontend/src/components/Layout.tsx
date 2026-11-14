import React from 'react';
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
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

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

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50">
      {/* Sidebar for desktop */}
      <aside className="w-full md:w-64 bg-slate-900 text-slate-100 flex-shrink-0 flex flex-col justify-between">
        <div>
          <div className="p-4 flex items-center gap-3 border-b border-slate-800">
            <Shield className="w-8 h-8 text-emerald-400" />
            <div>
              <span className="font-bold text-lg tracking-wide text-white">VAULT</span>
              <span className="block text-xs text-slate-400">Asset & Finance Core</span>
            </div>
          </div>

          <nav className="p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-500/20 text-emerald-300 font-semibold'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Logout */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">
                <User className="w-4 h-4" />
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-white truncate">
                  {user?.name || 'Tejas23'}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  {user?.email || 'tejas23@vault.local'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-800">Connected Platform</h1>
          <div className="flex items-center gap-3">
            <div className="text-xs text-slate-600 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Signed in as <strong>{user?.name || 'Tejas23'}</strong></span>
            </div>
            <div className="text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full font-medium">
              ₹ INR
            </div>
          </div>
        </header>

        <div className="p-6 flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

