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
            className="flex items-center gap-2 text-sm text-primary hover:text-primary font-medium cursor-pointer"
          >
            ← Back to History
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => handleDownloadMd(selectedEntry)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-input rounded-lg hover:bg-muted cursor-pointer"
            >
              <FileText size={14} /> Markdown
            </button>
            <button
              onClick={() => handleDownloadJson(selectedEntry)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-input rounded-lg hover:bg-muted cursor-pointer"
            >
              <FileJson size={14} /> JSON
            </button>
          </div>
        </div>
        <div className="text-xs text-muted-foreground">
          Saved: {new Date(selectedEntry.timestamp).toLocaleString()} · Drugs: {selectedEntry.drugNames.join(', ')}
        </div>
        <ResultPanel result={selectedEntry.result} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-5 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock size={20} className="text-primary" />
            <h2 className="text-base font-semibold text-foreground">Analysis History</h2>
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">{entries.length} saved</span>
          </div>
          {entries.length > 0 && (
            <button
              onClick={handleClearAll}
              className="text-xs text-destructive hover:text-destructive font-medium cursor-pointer"
            >
              Clear All
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading history...</div>
        ) : entries.length === 0 ? (
          <div className="flex flex-col items-center gap-2 px-6 py-6 text-center sm:flex-row sm:text-left">
            <Clock size={24} className="shrink-0 text-muted-foreground" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">No saved analyses yet.</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Saved analyses stay in this browser only. Patient context is excluded from exports by default.
              </p>
            </div>
            <a
              href="#analyze"
              className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:mt-0"
            >
              Start an analysis
            </a>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {entries.map(entry => (
              <div key={entry.id} className="p-4 flex items-center justify-between hover:bg-muted">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground truncate">
                      {entry.drugNames.join(', ')}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      entry.gateDecision === 'release' ? 'bg-success-soft text-success' :
                      entry.gateDecision === 'qualify' ? 'bg-warning-soft text-warning' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      {entry.gateDecision}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {new Date(entry.timestamp).toLocaleString()} · {entry.inputMode}
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-4">
                  <button onClick={() => setSelectedEntry(entry)} className="p-1.5 text-muted-foreground hover:text-primary cursor-pointer" title="View">
                    <Eye size={16} />
                  </button>
                  <button onClick={() => handleDownloadMd(entry)} className="p-1.5 text-muted-foreground hover:text-primary cursor-pointer" title="Download Markdown">
                    <FileText size={16} />
                  </button>
                  <button onClick={() => handleDownloadJson(entry)} className="p-1.5 text-muted-foreground hover:text-primary cursor-pointer" title="Download JSON">
                    <FileJson size={16} />
                  </button>
                  <button onClick={() => handleDelete(entry.id)} className="p-1.5 text-muted-foreground hover:text-destructive cursor-pointer" title="Delete">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {entries.length > 0 && (
        <p className="text-xs text-muted-foreground text-center">
          History is stored locally in your browser. Patient context is excluded from exports by default.
        </p>
      )}
    </div>
  );
}
