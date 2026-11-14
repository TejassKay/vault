import React from 'react';
import { Link } from 'react-router-dom';
import { Receipt, WalletCards, ShieldCheck, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';

export const Onboarding: React.FC = () => {
  const steps = [
    {
      num: 1,
      title: 'Upload a Bill & Track Warranties',
      desc: 'Upload an appliance bill (PDF or image). Vault extracts the product, seller, price, and warranty, auto-generating a scheduled maintenance timeline.',
      icon: Receipt,
      href: '/assets',
      actionText: 'Go to Assets & Bills',
    },
    {
      num: 2,
      title: 'Record Financial Baseline',
      desc: 'Enter your monthly income sources, essential expenses, liabilities (loans/EMIs), and financial holdings to unlock your cash flow snapshot and net worth.',
      icon: WalletCards,
      href: '/finances',
      actionText: 'Go to Finances',
    },
    {
      num: 3,
      title: 'Complete Risk Assessment',
      desc: 'Answer 8 simple questions to assess your risk tolerance. Vault combines your tolerance with your actual financial risk capacity to derive your effective risk profile.',
      icon: ShieldCheck,
      href: '/advisor',
      actionText: 'Take Questionnaire',
    },
    {
      num: 4,
      title: 'Get Explainable Recommendations',
      desc: 'View your sustainable monthly investment capacity and prioritized recommendations with complete reasoning, assumptions, risks, and alternatives.',
      icon: Sparkles,
      href: '/advisor',
      actionText: 'Open Explainable Advisor',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      <div className="bg-ink text-canvas border border-gold/60 rounded-sm p-8">
        <span className="text-[11px] font-mono tracking-widest uppercase text-canvas bg-growth/30 border border-growth/60 px-3 py-1 rounded-sm">
          Guided Onboarding
        </span>
        <h1 className="text-2xl md:text-3xl font-serif mt-4 pb-3 border-b border-gold/50">Welcome to Vault</h1>
        <p className="text-canvas/80 mt-3 max-w-2xl text-sm md:text-base font-sans">
          Vault connects what you own, what you owe, and what you save into one unified platform.
          Follow these 4 quick steps to set up your profile in under 5 minutes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {steps.map((s) => {
          const Icon = s.icon;
          return (
            <div
              key={s.num}
              className="bg-surface border border-border rounded-sm p-6 hover:border-growth/60 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="w-8 h-8 rounded-full bg-growth/[0.08] border border-growth/35 text-growth font-mono font-semibold flex items-center justify-center text-sm">
                    {s.num}
                  </span>
                  <div className="p-2 rounded-sm bg-canvas border border-border text-growth">
                    <Icon className="w-5 h-5 text-growth" />
                  </div>
                </div>
                <h3 className="text-lg font-serif text-ink">{s.title}</h3>
                <p className="text-sm text-muted-ink mt-2 leading-relaxed font-sans">{s.desc}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
                <Link
                  to={s.href}
                  className="inline-flex items-center gap-1.5 text-sm font-mono font-medium text-growth hover:text-ink group"
                >
                  {s.actionText}
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-surface border border-border rounded-sm p-5 flex items-start gap-3">
        <CheckCircle2 className="w-5 h-5 text-growth flex-shrink-0 mt-0.5" />
        <div className="text-xs text-muted-ink leading-relaxed font-sans">
          <span className="font-semibold text-ink">Privacy & Decision Support Policy: </span>
          All data is strictly private and isolated to your account. Vault provides educational decision support
          based strictly on the data you enter, at category level only. No trades, no named securities, and no external bank logins.
        </div>
      </div>
    </div>
  );
};
