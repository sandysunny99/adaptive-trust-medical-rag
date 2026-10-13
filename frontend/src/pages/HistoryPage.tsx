import { useEffect, useState } from 'react';
import { Clock, Trash2, FolderOpen } from 'lucide-react';
import type { AnalysisResult } from '../types';
import {
  clearHistory, deleteHistoryRecord, listHistoryRecords, type HistoryRecord,
} from '../services/historyDb';

interface Props {
  onOpen: (result: AnalysisResult) => void;
}

export function HistoryPage({ onOpen }: Props) {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => listHistoryRecords().then(setRecords).catch(err => setError(err.message));
  useEffect(() => { void refresh(); }, []);

  const remove = async (id: string) => {
    try {
      await deleteHistoryRecord(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete the saved analysis.');
    }
  };

  const clear = async () => {
    if (!window.confirm('Clear all saved analyses from this browser? This cannot be undone.')) return;
    try {
      await clearHistory();
      setRecords([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to clear local history.');
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Analysis History</h2>
          <p className="text-sm text-slate-500 mt-1">Saved locally in this browser. Opening a record does not rerun analysis.</p>
        </div>
        <button onClick={() => void clear()} disabled={!records.length} className="px-3 py-2 text-sm text-red-600 border border-red-200 rounded disabled:opacity-40">
          Clear all
        </button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}
      {!records.length && !error && <div className="bg-white border border-slate-200 rounded p-6 text-sm text-slate-500">No saved analyses yet.</div>}
      {records.map(record => (
        <div key={record.id} className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <Clock size={15} /> {new Date(record.createdAt).toLocaleString()}
            </div>
            <p className="text-xs text-slate-500 mt-1">{record.inputMode.replace(/_/g, ' ')} · {record.status}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => onOpen(record.result)} className="p-2 text-blue-600 hover:bg-blue-50 rounded" title="Open saved analysis">
              <FolderOpen size={17} />
            </button>
            <button onClick={() => void remove(record.id)} className="p-2 text-red-600 hover:bg-red-50 rounded" title="Delete saved analysis">
              <Trash2 size={17} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
