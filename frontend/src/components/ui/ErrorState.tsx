import { AlertTriangle, RotateCw } from 'lucide-react';

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
      className="bg-white rounded-lg border border-red-200 shadow-sm p-6 flex flex-col items-center text-center gap-3"
    >
      <AlertTriangle className="text-red-600" size={24} aria-hidden="true" />
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {message && <p className="text-sm text-slate-600 max-w-prose break-words">{message}</p>}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          disabled={retrying}
          className="mt-1 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <RotateCw size={14} aria-hidden="true" className={retrying ? 'animate-spin' : ''} />
          {retrying ? 'Retrying…' : 'Retry'}
        </button>
      )}
    </div>
  );
}
