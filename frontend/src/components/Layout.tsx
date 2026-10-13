import type { MouseEvent, ReactNode } from 'react';
import type { Page } from '../routing/routes';
import { ThemeToggle } from './ui/ThemeToggle';
import { IconChip } from './ui/IconChip';
import { Icons } from '../ui/icons';
import { cn } from '../utils/cn';
import { RESEARCH_DISCLAIMER } from '../constants/disclaimer';

interface NavItem {
  page: Page;
  label: string;
  icon: ReactNode;
}

const APP_NAME = 'Adaptive Trust-Aware Medical RAG';

const PUBLIC_NAV: NavItem[] = [
  { page: 'analyze', label: 'Analyze', icon: <Icons.analyze size={16} /> },
  { page: 'history', label: 'History', icon: <Icons.history size={16} /> },
  { page: 'about', label: 'About', icon: <Icons.about size={16} /> },
];

const RESEARCH_NAV: NavItem[] = [
  { page: 'evaluation', label: 'Evaluation', icon: <Icons.evaluation size={16} /> },
  { page: 'audit', label: 'Research Audit', icon: <Icons.audit size={16} /> },
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
        <div className="max-w-[1600px] mx-auto px-3 sm:px-6 py-3 flex items-center justify-between gap-2 sm:gap-3">
          <a
            href="#analyze"
            onClick={e => onNavClick(e, 'analyze')}
            className="flex min-w-0 items-center gap-2 sm:gap-3 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <IconChip icon={Icons.brand} tone="primary" size="md" className="h-8 w-8 sm:h-9 sm:w-9" />
            <div className="min-w-0">
              <h1 title={APP_NAME} className="truncate text-base sm:text-lg font-semibold text-foreground">
                {/* Under 640px the visible title is short; screen readers always get the full name. */}
                <span aria-hidden="true" className="sm:hidden">Medical RAG</span>
                <span className="sr-only sm:not-sr-only">{APP_NAME}</span>
              </h1>
              <p className="hidden sm:block text-xs text-muted-foreground">
                Medication Safety &amp; Evidence Analysis — Research Prototype
              </p>
            </div>
          </a>
          <div className="flex shrink-0 items-center gap-2">
            <span
              title={RESEARCH_DISCLAIMER}
              className="cursor-help inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 text-[11px] sm:text-xs font-semibold bg-warning-soft text-warning rounded"
            >
              <Icons.caution size={14} />
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
