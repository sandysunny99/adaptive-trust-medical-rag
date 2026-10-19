import { useState } from 'react';
import { Icons } from '../ui/icons';
import type { ConfirmedMedication, MedicationCandidate } from '../types';

interface Props {
  candidates: MedicationCandidate[];
  onConfirm: (confirmed: ConfirmedMedication[]) => void;
}

/** The confirmation item for a reviewed candidate, keeping who supplied the name. */
function toConfirmedMedication(c: MedicationCandidate): ConfirmedMedication {
  const name = (c.normalized_text || c.raw_text).trim();
  if (c.source === 'USER') {
    return { name, status: 'USER_ADDED', source: 'USER', raw_detected_name: null };
  }
  if (c.status === 'EDITED') {
    return { name, status: 'EDITED', source: 'USER_EDITED', raw_detected_name: c.raw_text };
  }
  return { name, status: 'CONFIRMED', source: c.source === 'OCR' ? 'OCR' : 'VISION', raw_detected_name: c.raw_text };
}

export function MedicationConfirmationPanel({ candidates: initialCandidates, onConfirm }: Props) {
  const [candidates, setCandidates] = useState<MedicationCandidate[]>(
    initialCandidates.map(c => ({ ...c }))
  );
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  
  const [newMedName, setNewMedName] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const handleToggleStatus = (id: string) => {
    setCandidates(prev => prev.map(c => {
      if (c.id === id) {
        if (c.status === 'CONFIRMED' || c.status === 'USER_ADDED' || c.status === 'EDITED') {
          // You can't just un-confirm a user added one back to DETECTED, but we can set it to UNCERTAIN if we want.
          // Or just REJECTED.
          return { ...c, status: 'REJECTED' };
        }
        return { ...c, status: 'CONFIRMED' };
      }
      return c;
    }));
  };

  const handleRemove = (id: string) => {
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, status: 'REJECTED' } : c));
  };

  const handleSaveEdit = (id: string) => {
    if (!editValue.trim()) return;
    setCandidates(prev => prev.map(c => {
      if (c.id === id) {
        return {
          ...c,
          normalized_text: editValue.trim(),
          status: 'EDITED'
        };
      }
      return c;
    }));
    setEditingId(null);
  };

  const handleAdd = () => {
    if (!newMedName.trim()) return;
    const newCand: MedicationCandidate = {
      id: `user-${Date.now()}`,
      raw_text: newMedName.trim(),
      normalized_text: newMedName.trim(),
      confidence: 'HIGH',
      status: 'USER_ADDED',
      source: 'USER'
    };
    setCandidates(prev => [...prev, newCand]);
    setNewMedName("");
    setIsAdding(false);
  };

  const activeCandidates = candidates.filter(c => c.status !== 'REJECTED');
  
  const hasUncertain = activeCandidates.some(c => c.status === 'UNCERTAIN' || c.status === 'DETECTED');
  const hasConfirmed = activeCandidates.length > 0 && !hasUncertain;

  return (
    <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
      <div className="p-5 border-b border-border bg-muted">
        <h2 className="text-base font-semibold text-foreground">Review Detected Medications</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Review and confirm the medications extracted from the prescription image. 
          Uncertain extractions must be resolved.
        </p>
      </div>

      <div className="p-5 space-y-4">
        {activeCandidates.length === 0 && (
          <div className="text-sm text-muted-foreground text-center py-4">
            No medications detected.
          </div>
        )}

        {activeCandidates.map(c => (
          <div key={c.id} className={`flex items-start justify-between p-4 rounded-lg border ${
            c.status === 'UNCERTAIN' ? 'border-warning/30 bg-warning-soft' : 
            c.status === 'DETECTED' ? 'border-primary/30 bg-primary-soft' :
            'border-success/30 bg-success-soft'
          }`}>
            <div className="flex-1">
              {editingId === c.id ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="px-3 py-1.5 border border-input rounded text-sm w-full max-w-xs"
                    autoFocus
                  />
                  <button onClick={() => handleSaveEdit(c.id)} className="p-1.5 bg-primary text-primary-foreground rounded hover:bg-primary/90">
                    <Icons.pass size={14} />
                  </button>
                  <button onClick={() => setEditingId(null)} className="p-1.5 text-muted-foreground hover:text-foreground">
                    <Icons.remove size={14} />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Icons.medication size={16} className={c.status === 'UNCERTAIN' ? 'text-warning' : 'text-muted-foreground'} />
                  <span className="font-semibold text-foreground">
                    {c.normalized_text || c.raw_text}
                  </span>
                  {c.normalized_text && c.normalized_text !== c.raw_text && (
                    <span className="text-xs text-muted-foreground block sm:inline sm:ml-2">
                      (Extracted: "{c.raw_text}")
                    </span>
                  )}
                </div>
              )}
              
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                {c.source === 'USER' ? (
                  <span className="px-2 py-0.5 bg-border text-foreground rounded-full">User Added</span>
                ) : (
                  <span className="px-2 py-0.5 bg-border text-foreground rounded-full">
                    Source: Image
                  </span>
                )}
                
                {c.source !== 'USER' && (
                  <span className={`px-2 py-0.5 rounded-full ${
                    c.confidence === 'HIGH' ? 'bg-success-soft text-success' :
                    c.confidence === 'MEDIUM' ? 'bg-warning-soft text-warning' :
                    'bg-destructive-soft text-destructive'
                  }`}>
                    Extraction confidence: {c.confidence}
                  </span>
                )}
                
                <span className={`px-2 py-0.5 rounded-full ${
                  c.status === 'CONFIRMED' || c.status === 'USER_ADDED' || c.status === 'EDITED' 
                    ? 'bg-success-soft text-success' 
                    : c.status === 'UNCERTAIN'
                    ? 'bg-warning-soft text-warning'
                    : 'bg-primary-soft text-primary'
                }`}>
                  Status: {c.status}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 ml-4">
              {c.status !== 'CONFIRMED' && c.status !== 'USER_ADDED' && c.status !== 'EDITED' && (
                <button 
                  onClick={() => handleToggleStatus(c.id)}
                  className="px-3 py-1.5 bg-card border border-input text-foreground rounded text-sm hover:bg-muted"
                >
                  Confirm
                </button>
              )}
              <button 
                onClick={() => {
                  setEditingId(c.id);
                  setEditValue(c.normalized_text || c.raw_text);
                }}
                className="p-1.5 text-muted-foreground hover:text-primary"
                title="Edit"
                aria-label={`Edit ${c.normalized_text || c.raw_text}`}
              >
                <Icons.edit size={16} />
              </button>
              <button 
                onClick={() => handleRemove(c.id)}
                className="p-1.5 text-muted-foreground hover:text-destructive"
                title="Remove"
                aria-label={`Remove ${c.normalized_text || c.raw_text}`}
              >
                <Icons.remove size={16} />
              </button>
            </div>
          </div>
        ))}

        {isAdding ? (
          <div className="flex items-center gap-2 p-4 border border-border rounded-lg bg-muted">
            <input
              type="text"
              value={newMedName}
              onChange={(e) => setNewMedName(e.target.value)}
              placeholder="Enter medication name"
              className="px-3 py-2 border border-input rounded text-sm w-full max-w-xs"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            />
            <button onClick={handleAdd} className="px-3 py-2 bg-primary text-primary-foreground rounded text-sm font-medium hover:bg-primary/90">
              Add
            </button>
            <button onClick={() => setIsAdding(false)} className="p-2 text-muted-foreground hover:text-foreground" aria-label="Cancel adding a medication" title="Cancel">
              <Icons.remove size={16} />
            </button>
          </div>
        ) : (
          <button 
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-2 text-sm text-primary font-medium hover:text-primary"
          >
            <Icons.add size={16} /> Add medication manually
          </button>
        )}
      </div>

      <div className="p-5 border-t border-border bg-muted flex items-center justify-between">
        <div className="text-sm text-warning flex items-center gap-2">
          {hasUncertain && (
            <>
              <Icons.caution size={16} />
              Please review and confirm all uncertain medications.
            </>
          )}
          {!hasUncertain && activeCandidates.length === 0 && (
            <>
              <Icons.caution size={16} />
              No medications to analyze.
            </>
          )}
        </div>
        
        <button
          onClick={() => {
            if (hasConfirmed) {
              onConfirm(activeCandidates.map(toConfirmedMedication));
            }
          }}
          disabled={!hasConfirmed}
          className="px-6 py-2.5 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Confirm Medications & Analyze
        </button>
      </div>
    </div>
  );
}
