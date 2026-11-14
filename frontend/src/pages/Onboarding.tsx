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
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl p-8 shadow-sm">
        <span className="text-xs font-semibold tracking-wider uppercase text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-3 py-1 rounded-full">
          Guided Onboarding
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold mt-3">Welcome to Vault</h1>
        <p className="text-slate-300 mt-2 max-w-2xl text-sm md:text-base">
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
              className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:border-indigo-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 font-bold flex items-center justify-center text-sm">
                    {s.num}
                  </span>
                  <div className="p-2 rounded-lg bg-slate-50 text-slate-700">
                    <Icon className="w-5 h-5 text-indigo-600" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-slate-900">{s.title}</h3>
                <p className="text-sm text-slate-600 mt-2 leading-relaxed">{s.desc}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                <Link
                  to={s.href}
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-600 hover:text-indigo-800 group"
                >
                  {s.actionText}
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 flex items-start gap-3">
        <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-600 leading-relaxed">
          <span className="font-semibold text-slate-800">Privacy & Decision Support Policy: </span>
          All data is strictly private and isolated to your account. Vault provides educational decision support
          based strictly on the data you enter, at category level only. No trades, no named securities, and no external bank logins.
        </div>
      </div>
    </div>
  );
};
