import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutDashboard,
  Compass,
  Receipt,
  WalletCards,
  Target,
  Sparkles,
  Activity,
  ArrowRight,
  FileText,
} from 'lucide-react';

interface CommandItem {
  id: string;
  title: string;
  category: 'Pages' | 'Financial Records' | 'Actions';
  icon: React.ComponentType<{ className?: string }>;
  action: () => void;
  hint?: string;
}

interface CommandBarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandBar: React.FC<CommandBarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Global keyboard shortcut listener: Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open handled by parent or state
          // Triggering close / open toggle
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const items: CommandItem[] = [
    {
      id: 'page-dashboard',
      title: 'Ledger Overview & Snapshot',
      category: 'Pages',
      icon: LayoutDashboard,
      hint: 'Net worth, capacity & timeline',
      action: () => {
        navigate('/');
        onClose();
      },
    },
    {
      id: 'page-assets',
      title: 'Physical Asset Index & Bills',
      category: 'Pages',
      icon: Receipt,
      hint: 'Appliances, invoices & warranties',
      action: () => {
        navigate('/assets');
        onClose();
      },
    },
    {
      id: 'page-finances',
      title: 'Financial Core Records',
      category: 'Pages',
      icon: WalletCards,
      hint: 'Income, transactions, liabilities & holdings',
      action: () => {
        navigate('/finances');
        onClose();
      },
    },
    {
      id: 'page-goals',
      title: 'Savings Goals & Projections',
      category: 'Pages',
      icon: Target,
      hint: 'Targets, progress & contribution scenarios',
      action: () => {
        navigate('/goals');
        onClose();
      },
    },
    {
      id: 'page-advisor',
      title: 'Advisory Recommendations Panel',
      category: 'Pages',
      icon: Sparkles,
      hint: 'Decision support, investment capacity & allocation',
      action: () => {
        navigate('/advisor');
        onClose();
      },
    },
    {
      id: 'page-onboarding',
      title: 'Risk Profile Questionnaire',
      category: 'Pages',
      icon: Compass,
      hint: 'Risk tolerance and capacity quiz',
      action: () => {
        navigate('/onboarding');
        onClose();
      },
    },
    {
      id: 'page-health',
      title: 'System Health & Engine Status',
      category: 'Pages',
      icon: Activity,
      hint: 'API & database status',
      action: () => {
        navigate('/health');
        onClose();
      },
    },
    {
      id: 'action-upload-bill',
      title: 'Upload Appliance Bill / Invoice',
      category: 'Actions',
      icon: FileText,
      hint: 'Add an archival bill to index',
      action: () => {
        navigate('/assets');
        onClose();
      },
    },
    {
      id: 'action-record-txn',
      title: 'Record New Transaction',
      category: 'Actions',
      icon: WalletCards,
      hint: 'Log expense or income in ledger',
      action: () => {
        navigate('/finances');
        onClose();
      },
    },
  ];

  const filtered = items.filter((item) =>
    `${item.title} ${item.category} ${item.hint || ''}`
      .toLowerCase()
      .includes(query.toLowerCase().trim())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDownInInput = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-ink/40 flex items-start justify-center pt-20 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-surface border border-ink rounded-sm overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-surface">
          <Search className="w-4 h-4 text-muted-ink flex-shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDownInInput}
            placeholder="Type a command or jump to page/record..."
            className="w-full bg-transparent text-sm font-sans text-ink placeholder:text-muted-ink outline-none"
          />
          <kbd className="text-[10px] font-mono px-1.5 py-0.5 bg-canvas border border-border text-muted-ink rounded-xs">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto divide-y divide-border/50 p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-muted-ink">
              No matching pages or records found.
            </div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-sm text-left transition-colors ${
                    isSelected
                      ? 'bg-canvas text-ink border border-border'
                      : 'text-muted-ink border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon className={`w-4 h-4 flex-shrink-0 ${isSelected ? 'text-ink' : 'text-muted-ink'}`} />
                    <div className="truncate">
                      <span className="font-sans text-xs font-medium text-ink block truncate">
                        {item.title}
                      </span>
                      {item.hint && (
                        <span className="text-[11px] font-sans text-muted-ink block truncate">
                          {item.hint}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 pl-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-muted-ink border border-border px-1.5 py-0.5 rounded-xs">
                      {item.category}
                    </span>
                    <ArrowRight className={`w-3.5 h-3.5 ${isSelected ? 'text-ink opacity-100' : 'opacity-0'}`} />
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Command Bar Footer */}
        <div className="px-4 py-2 border-t border-border bg-canvas/60 text-[10px] font-mono text-muted-ink flex items-center justify-between">
          <span>Navigate with ↑ / ↓, select with ↵</span>
          <span>No free-text AI prompt</span>
        </div>
      </div>
    </div>
  );
};

export default CommandBar;
