/**
 * REST + SSE client for the Medical RAG backend.
 *
 * Handles:
 * - POST /api/v1/analyze → AnalyzeAccepted
 * - GET /api/v1/stream/{request_id} → SSE event stream
 * - GET /health → health check
 */

import type {
  PatientContext,
  InputMode,
} from '../types';

const API_BASE = '';  // proxied by Vite in dev

// ── Types ────────────────────────────────────────────────────────────────────

export interface AnalyzeAccepted {
  request_id: string;
  stream_url: string;
}

export interface HealthStatus {
  status: string;
  database: boolean;
  pgvector: boolean;
  version: string;
  uptime_seconds: number | null;
}

export type SSEEventHandler = (event: string, data: unknown) => void;

// ── REST Client ──────────────────────────────────────────────────────────────

export async function submitAnalysis(
  drugNames: string[],
  patientContext?: PatientContext | null,
  inputMode: InputMode = 'direct_drugs',
): Promise<AnalyzeAccepted> {
  const response = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input_mode: inputMode,
      drug_names: drugNames,
      patient_context: patientContext || null,
    }),
  });

  if (!response.ok) {
    const errBody = await response.text();
    throw new Error(`Analysis request failed (${response.status}): ${errBody}`);
  }

  return response.json();
}

export async function submitPrescriptionImage(
  file: File,
  patientContext?: PatientContext | null,
): Promise<AnalyzeAccepted & { validation: any }> {
  const formData = new FormData();
  formData.append('image', file);
  if (patientContext) {
    formData.append('patient_context', JSON.stringify(patientContext));
  }

  const response = await fetch(`${API_BASE}/api/v1/analyze/prescription`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errBody = await response.text();
    throw new Error(`Image upload failed (${response.status}): ${errBody}`);
  }

  return response.json();
}

export async function confirmMedications(
  requestId: string,
  confirmedMedications: string[]
): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/api/v1/analyze/${requestId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmed_medications: confirmedMedications }),
  });

  if (!response.ok) {
    const errBody = await response.text();
    throw new Error(`Confirmation failed (${response.status}): ${errBody}`);
  }

  return response.json();
}

export async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

// ── SSE Stream Client ────────────────────────────────────────────────────────

export function connectStream(
  streamUrl: string,
  onEvent: SSEEventHandler,
  onError?: (error: Event) => void,
  onClose?: () => void,
): () => void {
  const eventSource = new EventSource(`${API_BASE}${streamUrl}`);

  // Known event types from the backend
  const EVENT_TYPES = [
    'stage_update',
    'extraction',
    'confirmation_required',
    'rxnorm',
    'retrieval',
    'trust',
    'security',
    'interactions',
    'verification',
    'answer',
    'abstention',
    'error',
    'complete',
  ];

  for (const eventType of EVENT_TYPES) {
    eventSource.addEventListener(eventType, (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(eventType, data);
      } catch (e) {
        console.error(`Failed to parse SSE event '${eventType}':`, e);
      }
    });
  }

  eventSource.onerror = (event) => {
    console.error('SSE connection error:', event);
    onError?.(event);
    eventSource.close();
    onClose?.();
  };

  // Return cleanup function
  return () => {
    eventSource.close();
    onClose?.();
  };
}
