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
  LLMModelInfo,
  LLMSelection,
  ConfirmedMedication,
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

export async function fetchModelCatalog(): Promise<LLMModelInfo[]> {
  const response = await fetch(`${API_BASE}/api/v1/llm/models`);
  if (!response.ok) {
    throw new Error(`Failed to fetch model catalog: HTTP ${response.status}`);
  }
  const data = await response.json();
  return data.models || [];
}

export async function submitAnalysis(
  drugNames: string[],
  patientContext?: PatientContext | null,
  inputMode: InputMode = 'direct_drugs',
  llmSelection?: LLMSelection | null,
  additionalInstructions?: string,
): Promise<AnalyzeAccepted> {
  const response = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input_mode: inputMode,
      drug_names: drugNames,
      patient_context: patientContext || null,
      llm_selection: llmSelection || null,
      additional_instructions: additionalInstructions || null,
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
  llmSelection?: LLMSelection | null,
  additionalInstructions?: string,
): Promise<AnalyzeAccepted & { validation: any }> {
  const formData = new FormData();
  formData.append('image', file);
  if (patientContext) {
    formData.append('patient_context', JSON.stringify(patientContext));
  }
  if (llmSelection) {
    formData.append('llm_selection', JSON.stringify(llmSelection));
  }
  if (additionalInstructions) {
    formData.append('additional_instructions', additionalInstructions);
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
  confirmedMedications: ConfirmedMedication[]
): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/api/v1/analyze/${encodeURIComponent(requestId)}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmed_medications: confirmedMedications }),
  });

  if (!response.ok) {
    const errBody = await response.text();
    // The raw validation payload is for developers, not the page.
    if (import.meta.env.DEV) console.warn(`Confirmation failed (${response.status})`, errBody);
    throw new Error(confirmationErrorMessage(response.status));
  }

  return response.json();
}

/** A cancel with no answer after this long has an unknown outcome; the page never waits on it longer. */
export const CANCEL_TIMEOUT_MS = 10_000;

/**
 * Abandon an image analysis before its medications are confirmed. 404 and 409 mean the request has
 * already ended (or was confirmed), so there is nothing left to cancel: both count as done.
 * Throws when there is no answer (network failure, timeout) or a server error: the outcome is then
 * unknown, and sending the cancel again is safe.
 */
export async function cancelAnalysis(requestId: string): Promise<'cancelled' | 'already_ended'> {
  const response = await fetch(`${API_BASE}/api/v1/analyze/${encodeURIComponent(requestId)}/cancel`, {
    method: 'POST',
    signal: AbortSignal.timeout(CANCEL_TIMEOUT_MS),
  });
  if (response.ok) return 'cancelled';
  if (response.status === 404 || response.status === 409) return 'already_ended';
  throw new Error(`The analysis could not be cancelled (HTTP ${response.status}).`);
}

export function confirmationErrorMessage(status: number): string {
  if (status === 422) {
    return 'The server rejected the medication confirmation as invalid (HTTP 422). Nothing was analyzed. Confirm the medications again.';
  }
  if (status === 404) {
    return 'This analysis request has expired or no longer exists (HTTP 404). Upload the prescription again.';
  }
  if (status === 409) {
    return 'This analysis is not waiting for a confirmation, or has already ended (HTTP 409). Nothing new was analyzed. Upload the prescription again.';
  }
  return `The medication confirmation could not be sent (HTTP ${status}). Nothing was analyzed. Try again.`;
}

export async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

// ── SSE Stream Client ────────────────────────────────────────────────────────





export interface ControlState {
  status: string;
  reason: string;
  reference: string;
}

export interface ResearchState {
  dataset_integrity: ControlState;
  case_order_integrity: ControlState;
  frozen_retrieval: ControlState;
  trust_evidence_control: ControlState;
  claim_verification: ControlState;
  controlled_abstention: ControlState;
  prompt_freeze: ControlState;
  provider_readiness: ControlState;
  researcher_authorization: ControlState;
  real_llm_evaluation: ControlState;
  medical_evaluation_requests_total: number;
  medical_evaluation_requests_executed: number;
  protocol: string;
}

export async function fetchResearchState(): Promise<ResearchState> {
  const response = await fetch(`${API_BASE}/research-state`);
  if (!response.ok) {
    throw new Error(`Failed to fetch research state: ${response.status}`);
  }
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(
      `Research state endpoint returned ${contentType || 'no content type'} instead of JSON. ` +
      'Check that /research-state is forwarded to the backend.'
    );
  }
  return response.json();
}

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
    'medication_candidates_extracted',
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
