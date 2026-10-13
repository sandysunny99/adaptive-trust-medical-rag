import type { AnalysisResult, InputMode } from '../types';

export interface HistoryRecord {
  id: string;
  createdAt: string;
  status: 'complete' | 'abstained' | 'failed' | 'partial';
  inputMode: InputMode;
  requestId: string;
  result: AnalysisResult;
}

const DB_NAME = 'medical_rag_history';
const DB_VERSION = 1;
const STORE_NAME = 'analyses';

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!('indexedDB' in window)) {
      reject(new Error('Browser storage is unavailable.'));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      const store = db.objectStoreNames.contains(STORE_NAME)
        ? request.transaction?.objectStore(STORE_NAME)
        : db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      store?.createIndex('createdAt', 'createdAt', { unique: false });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new Error('Unable to open local history storage.'));
  });
}

function transaction<T>(
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore, resolve: (value: T) => void, reject: (reason: Error) => void) => void,
): Promise<T> {
  return openDatabase().then(db => new Promise<T>((resolve, reject) => {
    const store = db.transaction(STORE_NAME, mode).objectStore(STORE_NAME);
    operation(store, resolve, reject);
  }).finally(() => db.close()));
}

function statusForResult(result: AnalysisResult): HistoryRecord['status'] {
  if (result.gate_decision === 'abstain') return 'abstained';
  if (result.gate_decision === 'release' || result.gate_decision === 'qualify') return 'complete';
  return 'partial';
}

export function createHistoryRecord(result: AnalysisResult): HistoryRecord {
  return {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    status: statusForResult(result),
    inputMode: result.input_mode,
    requestId: result.request_id,
    result: JSON.parse(JSON.stringify(result)) as AnalysisResult,
  };
}

export function saveHistoryRecord(record: HistoryRecord): Promise<void> {
  return transaction('readwrite', (store, resolve, reject) => {
    const request = store.put(record);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(new Error('Unable to save this analysis to local history.'));
  });
}

export function listHistoryRecords(): Promise<HistoryRecord[]> {
  return transaction('readonly', (store, resolve, reject) => {
    const request = store.index('createdAt').getAll();
    request.onsuccess = () => {
      const records = request.result as HistoryRecord[];
      resolve(records.sort((a, b) => b.createdAt.localeCompare(a.createdAt)));
    };
    request.onerror = () => reject(new Error('Unable to load local analysis history.'));
  });
}

export function getHistoryRecord(id: string): Promise<HistoryRecord | undefined> {
  return transaction('readonly', (store, resolve, reject) => {
    const request = store.get(id);
    request.onsuccess = () => resolve(request.result as HistoryRecord | undefined);
    request.onerror = () => reject(new Error('Unable to open the saved analysis.'));
  });
}

export function deleteHistoryRecord(id: string): Promise<void> {
  return transaction('readwrite', (store, resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(new Error('Unable to delete the saved analysis.'));
  });
}

export function clearHistory(): Promise<void> {
  return transaction('readwrite', (store, resolve, reject) => {
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(new Error('Unable to clear local analysis history.'));
  });
}
