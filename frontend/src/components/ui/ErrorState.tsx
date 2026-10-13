import { Icons } from '../../ui/icons';

interface ErrorStateProps {
  title: string;
  message?: string | null;
  onRetry?: () => void;
  retrying?: boolean;
}

export function ErrorState({ title, message, onRetry, retrying = false }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="bg-card rounded-lg border border-destructive/30 shadow-sm p-6 flex flex-col items-center text-center gap-3"
    >
      <Icons.error className="text-destructive" size={24} aria-hidden="true" />
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      {message && <p className="text-sm text-muted-foreground max-w-prose break-words">{message}</p>}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          disabled={retrying}
          className="mt-1 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-input text-foreground hover:bg-muted disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Icons.retry size={14} aria-hidden="true" className={retrying ? 'animate-spin' : ''} />
          {retrying ? 'Retrying…' : 'Retry'}
        </button>
      )}
    </div>
  );
}
