import type { ReactNode } from 'react';
import type { Page } from '../App';
import {
  FlaskConical, Shield, BarChart3, FileSearch,
  Activity, LayoutDashboard
} from 'lucide-react';

const NAV_ITEMS: { page: Page; label: string; icon: ReactNode }[] = [
  { page: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
  { page: 'workspace', label: 'Medical RAG', icon: <FlaskConical size={18} /> },
  { page: 'evidence', label: 'Evidence', icon: <FileSearch size={18} /> },
  { page: 'security', label: 'Security', icon: <Shield size={18} /> },
  { page: 'evaluation', label: 'Evaluation', icon: <BarChart3 size={18} /> },
  { page: 'audit', label: 'Research Audit', icon: <Activity size={18} /> },
];

interface LayoutProps {
  children: ReactNode;
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

export function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FlaskConical className="text-blue-700" size={24} />
            <div>
              <h1 className="text-lg font-semibold text-slate-900">
                Adaptive Trust-Aware Medical RAG
              </h1>
              <p className="text-xs text-slate-500">
                Medication Safety &amp; Evidence Analysis — Research Prototype
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-800 rounded">
              RESEARCH USE ONLY
            </span>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-[1600px] mx-auto px-6 flex gap-1">
          {NAV_ITEMS.map(({ page, label, icon }) => (
            <button
              key={page}
              onClick={() => onNavigate(page)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                currentPage === page
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
              }`}
            >
              {icon}
              {label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6">
        {children}
      </main>

      {/* Footer disclaimer */}
      <footer className="border-t border-slate-200 bg-white mt-8">
        <div className="max-w-[1600px] mx-auto px-6 py-3">
          <p className="text-xs text-slate-500 text-center">
            ⚠️ This is an evidence-grounded research prototype. It is NOT an autonomous clinical
            decision-maker and does NOT replace a doctor, pharmacist, or other healthcare professional.
            All outputs are research-grade and require clinical verification.
          </p>
        </div>
      </footer>
    </div>
  );
}
