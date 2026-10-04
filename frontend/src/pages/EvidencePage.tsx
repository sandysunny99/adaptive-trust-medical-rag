import { FileSearch } from 'lucide-react';

export function EvidencePage() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileSearch size={20} className="text-blue-600" />
        <h2 className="text-base font-semibold text-slate-900">Evidence Explorer</h2>
      </div>
      <p className="text-sm text-slate-500">
        Evidence explorer will display retrieved sources, provenance chains, and trust scores
        after a medication analysis is performed.
      </p>
    </div>
  );
}
