import { useState } from 'react';
import { Pill, Check, Edit2, X, Plus, AlertTriangle } from 'lucide-react';
import type { MedicationCandidate } from '../types';

interface Props {
  candidates: MedicationCandidate[];
  onConfirm: (confirmedNames: string[]) => void;
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
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-100 bg-slate-50">
        <h2 className="text-base font-semibold text-slate-900">Review Detected Medications</h2>
        <p className="text-sm text-slate-500 mt-1">
          Review and confirm the medications extracted from the prescription image. 
          Uncertain extractions must be resolved.
        </p>
      </div>

      <div className="p-5 space-y-4">
        {activeCandidates.length === 0 && (
          <div className="text-sm text-slate-500 text-center py-4">
            No medications detected.
          </div>
        )}

        {activeCandidates.map(c => (
          <div key={c.id} className={`flex items-start justify-between p-4 rounded-lg border ${
            c.status === 'UNCERTAIN' ? 'border-amber-200 bg-amber-50' : 
            c.status === 'DETECTED' ? 'border-blue-200 bg-blue-50' :
            'border-green-200 bg-green-50'
          }`}>
            <div className="flex-1">
              {editingId === c.id ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="px-3 py-1.5 border border-slate-300 rounded text-sm w-full max-w-xs"
                    autoFocus
                  />
                  <button onClick={() => handleSaveEdit(c.id)} className="p-1.5 bg-blue-600 text-white rounded hover:bg-blue-700">
                    <Check size={14} />
                  </button>
                  <button onClick={() => setEditingId(null)} className="p-1.5 text-slate-500 hover:text-slate-700">
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Pill size={16} className={c.status === 'UNCERTAIN' ? 'text-amber-500' : 'text-slate-500'} />
                  <span className="font-semibold text-slate-900">
                    {c.normalized_text || c.raw_text}
                  </span>
                  {c.normalized_text && c.normalized_text !== c.raw_text && (
                    <span className="text-xs text-slate-400 block sm:inline sm:ml-2">
                      (Extracted: "{c.raw_text}")
                    </span>
                  )}
                </div>
              )}
              
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                {c.source === 'USER' ? (
                  <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded-full">User Added</span>
                ) : (
                  <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded-full">
                    Source: Image
                  </span>
                )}
                
                {c.source !== 'USER' && (
                  <span className={`px-2 py-0.5 rounded-full ${
                    c.confidence === 'HIGH' ? 'bg-green-100 text-green-700' :
                    c.confidence === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    Extraction confidence: {c.confidence}
                  </span>
                )}
                
                <span className={`px-2 py-0.5 rounded-full ${
                  c.status === 'CONFIRMED' || c.status === 'USER_ADDED' || c.status === 'EDITED' 
                    ? 'bg-green-100 text-green-800' 
                    : c.status === 'UNCERTAIN'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  Status: {c.status}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 ml-4">
              {c.status !== 'CONFIRMED' && c.status !== 'USER_ADDED' && c.status !== 'EDITED' && (
                <button 
                  onClick={() => handleToggleStatus(c.id)}
                  className="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 rounded text-sm hover:bg-slate-50"
                >
                  Confirm
                </button>
              )}
              <button 
                onClick={() => {
                  setEditingId(c.id);
                  setEditValue(c.normalized_text || c.raw_text);
                }}
                className="p-1.5 text-slate-400 hover:text-blue-600"
                title="Edit"
              >
                <Edit2 size={16} />
              </button>
              <button 
                onClick={() => handleRemove(c.id)}
                className="p-1.5 text-slate-400 hover:text-red-600"
                title="Remove"
              >
                <X size={16} />
              </button>
            </div>
          </div>
        ))}

        {isAdding ? (
          <div className="flex items-center gap-2 p-4 border border-slate-200 rounded-lg bg-slate-50">
            <input
              type="text"
              value={newMedName}
              onChange={(e) => setNewMedName(e.target.value)}
              placeholder="Enter medication name"
              className="px-3 py-2 border border-slate-300 rounded text-sm w-full max-w-xs"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            />
            <button onClick={handleAdd} className="px-3 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
              Add
            </button>
            <button onClick={() => setIsAdding(false)} className="p-2 text-slate-500 hover:text-slate-700">
              <X size={16} />
            </button>
          </div>
        ) : (
          <button 
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-2 text-sm text-blue-600 font-medium hover:text-blue-800"
          >
            <Plus size={16} /> Add medication manually
          </button>
        )}
      </div>

      <div className="p-5 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
        <div className="text-sm text-amber-700 flex items-center gap-2">
          {hasUncertain && (
            <>
              <AlertTriangle size={16} />
              Please review and confirm all uncertain medications.
            </>
          )}
          {!hasUncertain && activeCandidates.length === 0 && (
            <>
              <AlertTriangle size={16} />
              No medications to analyze.
            </>
          )}
        </div>
        
        <button
          onClick={() => {
            if (hasConfirmed) {
              // Submit array of strings for confirmed med names
              const resolved = activeCandidates.map(c => c.normalized_text || c.raw_text);
              onConfirm(resolved);
            }
          }}
          disabled={!hasConfirmed}
          className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Confirm Medications & Analyze
        </button>
      </div>
    </div>
  );
}
