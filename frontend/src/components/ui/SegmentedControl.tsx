import { useRef, type KeyboardEvent, type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: ReactNode;
}

interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
  className?: string;
}

/**
 * Tab-style segmented control. Arrow keys, Home and End move the selection
 * (automatic activation); only the selected segment is in the tab order.
 */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
  className,
}: SegmentedControlProps<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const select = (index: number) => {
    const next = options[(index + options.length) % options.length];
    onChange(next.value);
    refs.current[(index + options.length) % options.length]?.focus();
  };

  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        select(index + 1);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        select(index - 1);
        break;
      case 'Home':
        e.preventDefault();
        select(0);
        break;
      case 'End':
        e.preventDefault();
        select(options.length - 1);
        break;
    }
  };

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cn('inline-flex w-full rounded-lg bg-muted p-1 sm:w-auto', className)}
    >
      {options.map((option, i) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            ref={el => { refs.current[i] = el; }}
            type="button"
            role="tab"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(option.value)}
            onKeyDown={e => onKeyDown(e, i)}
            className={cn(
              'flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors sm:flex-none',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              selected
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {option.icon && <span aria-hidden="true">{option.icon}</span>}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
