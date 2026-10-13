import { useId, useState, type ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

interface DisclosureProps {
  title: ReactNode;
  icon?: ReactNode;
  /** Short text shown next to the title, e.g. "Optional". */
  hint?: ReactNode;
  defaultOpen?: boolean;
  className?: string;
  children: ReactNode;
}

/** Accessible show/hide section: a button with aria-expanded controlling a region. */
export function Disclosure({ title, icon, hint, defaultOpen = false, className, children }: DisclosureProps) {
  const [open, setOpen] = useState(defaultOpen);
  const panelId = useId();

  return (
    <div className={cn('rounded-lg border border-border', className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center gap-2 rounded-lg px-4 py-3 text-left text-sm font-medium text-foreground hover:bg-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {icon && <span className="text-muted-foreground" aria-hidden="true">{icon}</span>}
        <span className="flex-1">
          {title}
          {hint && <span className="ml-2 text-xs font-normal text-muted-foreground">{hint}</span>}
        </span>
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={cn(
            'text-muted-foreground transition-transform duration-150',
            open && 'rotate-180'
          )}
        />
      </button>
      <div id={panelId} hidden={!open} className="px-4 pb-4">
        {children}
      </div>
    </div>
  );
}
