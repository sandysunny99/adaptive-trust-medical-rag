import { Icons } from '../../ui/icons';
import { useTheme } from '../../theme/useTheme';

export function ThemeToggle() {
  const { resolved, toggle } = useTheme();
  const isDark = resolved === 'dark';

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-pressed={isDark}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {isDark ? <Icons.themeLight size={16} aria-hidden="true" /> : <Icons.themeDark size={16} aria-hidden="true" />}
    </button>
  );
}
