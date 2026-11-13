import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Receipt,
  WalletCards,
  Target,
  Sparkles,
  Activity,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Assets & Bills', href: '/assets', icon: Receipt },
  { name: 'Finances', href: '/finances', icon: WalletCards },
  { name: 'Goals', href: '/goals', icon: Target },
  { name: 'Advisor', href: '/advisor', icon: Sparkles },
  { name: 'System Health', href: '/health', icon: Activity },
];

export const Layout: React.FC = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50">
      {/* Sidebar for desktop */}
      <aside className="w-full md:w-64 bg-slate-900 text-slate-100 flex-shrink-0">
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
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-800">Connected Platform</h1>
          <div className="text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full font-medium">
            Demo Mode • ₹ INR
          </div>
        </header>

        <div className="p-6 flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
