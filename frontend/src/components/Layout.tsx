import type { MouseEvent, ReactNode } from 'react';
import type { Page } from '../routing/routes';
import { ThemeToggle } from './ui/ThemeToggle';
import { FlaskConical, Info, BarChart3, Activity, Clock } from 'lucide-react';
import { cn } from '../utils/cn';
import { RESEARCH_DISCLAIMER } from '../constants/disclaimer';

interface NavItem {
  page: Page;
  label: string;
  icon: ReactNode;
}

const PUBLIC_NAV: NavItem[] = [
  { page: 'analyze', label: 'Analyze', icon: <FlaskConical size={18} /> },
  { page: 'history', label: 'History', icon: <Clock size={18} /> },
  { page: 'about', label: 'About', icon: <Info size={18} /> },
];

const RESEARCH_NAV: NavItem[] = [
  { page: 'evaluation', label: 'Evaluation', icon: <BarChart3 size={18} /> },
  { page: 'audit', label: 'Research Audit', icon: <Activity size={18} /> },
];

interface LayoutProps {
  children: ReactNode;
  currentPage: Page;
  onNavigate: (page: Page) => void;
  showResearchTabs?: boolean;
}

export function Layout({ children, currentPage, onNavigate, showResearchTabs = false }: LayoutProps) {
  const navItems = showResearchTabs ? [...PUBLIC_NAV, ...RESEARCH_NAV] : PUBLIC_NAV;

  const onNavClick = (e: MouseEvent<HTMLAnchorElement>, page: Page) => {
    // Let modified clicks (new tab, etc.) behave like normal links.
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    onNavigate(page);
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-glass backdrop-blur-md">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <a
            href="#analyze"
            onClick={e => onNavClick(e, 'analyze')}
            className="flex min-w-0 items-center gap-3 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <FlaskConical className="shrink-0 text-primary" size={24} aria-hidden="true" />
            <div className="min-w-0">
              <h1 className="truncate text-base sm:text-lg font-semibold text-foreground">
                Adaptive Trust-Aware Medical RAG
              </h1>
              <p className="hidden sm:block text-xs text-muted-foreground">
                Medication Safety &amp; Evidence Analysis — Research Prototype
              </p>
            </div>
          </a>
          <div className="flex shrink-0 items-center gap-2">
            <span
              title={RESEARCH_DISCLAIMER}
              className="cursor-help px-2 py-0.5 text-xs font-semibold bg-warning-soft text-warning rounded"
            >
              RESEARCH USE ONLY
              <span className="sr-only">. {RESEARCH_DISCLAIMER}</span>
            </span>
            <ThemeToggle />
          </div>
        </div>

        <nav aria-label="Main" className="border-t border-border">
          <div className="max-w-[1600px] mx-auto px-2 sm:px-6 flex gap-1 overflow-x-auto">
            {navItems.map(({ page, label, icon }) => {
              const active = currentPage === page;
              return (
                <a
                  key={page}
                  href={`#${page}`}
                  aria-current={active ? 'page' : undefined}
                  onClick={e => onNavClick(e, page)}
                  className={cn(
                    'flex shrink-0 items-center gap-2 px-3 sm:px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                    active
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:border-input'
                  )}
                >
                  <span aria-hidden="true">{icon}</span>
                  {label}
                </a>
              );
            })}
          </div>
        </nav>
      </header>

      <main className="w-full flex-1 max-w-[1600px] mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>

      <footer className="border-t border-border">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-3 text-xs text-muted-foreground">
          Research prototype.{' '}
          <a
            href="#about"
            onClick={e => onNavClick(e, 'about')}
            className="rounded underline underline-offset-2 hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Methodology and full disclaimer
          </a>
        </div>
      </footer>
    </div>
  );
}
