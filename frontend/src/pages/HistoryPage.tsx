import { useState, useEffect } from 'react';
import { Clock, Trash2, FileText, FileJson, Eye } from 'lucide-react';
import type { HistoryEntry } from '../services/historyDb';
import { getAllAnalyses, deleteAnalysis, clearAllAnalyses } from '../services/historyDb';
import { exportAsJson, exportAsMarkdown, downloadFile } from '../services/exportService';
import { ResultPanel } from '../components/ResultPanel';

export function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await getAllAnalyses();
      setEntries(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: string) => {
    await deleteAnalysis(id);
    setEntries(prev => prev.filter(e => e.id !== id));
    if (selectedEntry?.id === id) setSelectedEntry(null);
  };

  const handleClearAll = async () => {
    if (!window.confirm('Delete all saved analyses? This cannot be undone.')) return;
    await clearAllAnalyses();
    setEntries([]);
    setSelectedEntry(null);
  };

  const handleDownloadMd = (entry: HistoryEntry) => {
    const md = exportAsMarkdown(entry);
    downloadFile(md, `analysis-${entry.id.slice(0, 8)}.md`, 'text/markdown');
  };

  const handleDownloadJson = (entry: HistoryEntry) => {
    const json = exportAsJson(entry);
    downloadFile(json, `analysis-${entry.id.slice(0, 8)}.json`, 'application/json');
  };

  if (selectedEntry) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSelectedEntry(null)}
            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
          >
            ← Back to History
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => handleDownloadMd(selectedEntry)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 cursor-pointer"
            >
              <FileText size={14} /> Markdown
            </button>
            <button
              onClick={() => handleDownloadJson(selectedEntry)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 cursor-pointer"
            >
              <FileJson size={14} /> JSON
            </button>
          </div>
        </div>
        <div className="text-xs text-slate-500">
          Saved: {new Date(selectedEntry.timestamp).toLocaleString()} · Drugs: {selectedEntry.drugNames.join(', ')}
        </div>
        <ResultPanel result={selectedEntry.result} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock size={20} className="text-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">Analysis History</h2>
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">{entries.length} saved</span>
          </div>
          {entries.length > 0 && (
            <button
              onClick={handleClearAll}
              className="text-xs text-red-600 hover:text-red-800 font-medium cursor-pointer"
            >
              Clear All
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading history...</div>
        ) : entries.length === 0 ? (
          <div className="p-8 text-center">
            <Clock size={32} className="mx-auto text-slate-300 mb-3" />
            <p className="text-sm text-slate-500">No saved analyses yet.</p>
            <p className="text-xs text-slate-400 mt-1">Completed analyses can be saved from the Medical RAG workspace.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {entries.map(entry => (
              <div key={entry.id} className="p-4 flex items-center justify-between hover:bg-slate-50">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-900 truncate">
                      {entry.drugNames.join(', ')}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      entry.gateDecision === 'release' ? 'bg-emerald-100 text-emerald-800' :
                      entry.gateDecision === 'qualify' ? 'bg-amber-100 text-amber-800' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {entry.gateDecision}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {new Date(entry.timestamp).toLocaleString()} · {entry.inputMode}
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-4">
                  <button onClick={() => setSelectedEntry(entry)} className="p-1.5 text-slate-400 hover:text-blue-600 cursor-pointer" title="View">
                    <Eye size={16} />
                  </button>
                  <button onClick={() => handleDownloadMd(entry)} className="p-1.5 text-slate-400 hover:text-blue-600 cursor-pointer" title="Download Markdown">
                    <FileText size={16} />
                  </button>
                  <button onClick={() => handleDownloadJson(entry)} className="p-1.5 text-slate-400 hover:text-blue-600 cursor-pointer" title="Download JSON">
                    <FileJson size={16} />
                  </button>
                  <button onClick={() => handleDelete(entry.id)} className="p-1.5 text-slate-400 hover:text-red-600 cursor-pointer" title="Delete">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <p className="text-xs text-slate-400 text-center">
        ⚠️ History is stored locally in your browser. Patient context is excluded from exports by default.
      </p>
    </div>
  );
}
