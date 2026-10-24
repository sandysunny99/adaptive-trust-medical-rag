import { describe, it, expect, vi, afterEach } from 'vitest';
import { cancelAnalysis, confirmMedications } from './api';
import type { ConfirmedMedication } from '../types';

const CONFIRMED: ConfirmedMedication[] = [
  { name: 'Simvastatin', status: 'CONFIRMED', source: 'VISION', raw_detected_name: 'Simvastatin 40 mg' },
  { name: 'Clarithromycin', status: 'CONFIRMED', source: 'VISION', raw_detected_name: 'Clarithromycin 500 mg' },
];

function mockFetch(status: number, body: string) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(body, { status, headers: { 'Content-Type': 'application/json' } }));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('cancelAnalysis', () => {
  it('counts a cancelled, ended or confirmed request as done, and never waits unbounded', async () => {
    for (const [status, outcome] of [[200, 'cancelled'], [404, 'already_ended'], [409, 'already_ended']] as const) {
      const fetchMock = mockFetch(status, '{}');
      await expect(cancelAnalysis('req-1')).resolves.toBe(outcome);
      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toContain('/api/v1/analyze/req-1/cancel');
      expect(init.method).toBe('POST');
      expect(init.signal).toBeInstanceOf(AbortSignal);  // a timeout: no answer means an unknown outcome
    }
  });

  it('leaves the outcome unknown on a server error, a lost connection or a timeout', async () => {
    mockFetch(502, 'Bad Gateway');
    await expect(cancelAnalysis('req-1')).rejects.toThrow(/HTTP 502/);
    for (const failure of [new TypeError('Failed to fetch'), new DOMException('The operation timed out.', 'TimeoutError')]) {
      vi.stubGlobal('fetch', vi.fn().mockRejectedValue(failure));
      await expect(cancelAnalysis('req-1')).rejects.toBe(failure);
    }
  });
});

describe('confirmMedications', () => {
  it('posts one object per medication in order, never bare names', async () => {
    const fetchMock = mockFetch(200, JSON.stringify({ status: 'success' }));
    await confirmMedications('req-1', CONFIRMED);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/analyze/req-1/confirm');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' });
    const body = JSON.parse(init.body);
    expect(body).toEqual({ confirmed_medications: CONFIRMED });
    expect(body.confirmed_medications.every((m: unknown) => typeof m === 'object' && m !== null)).toBe(true);
  });

  it('turns a 422 into a readable message without the raw validation payload', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const pydantic = JSON.stringify({
      detail: [{ type: 'model_attributes_type', loc: ['body', 'confirmed_medications', 0], input: 'Simvastatin' }],
    });
    mockFetch(422, pydantic);
    const request = confirmMedications('req-1', CONFIRMED);
    await expect(request).rejects.toThrow(
      'The server rejected the medication confirmation as invalid (HTTP 422). Nothing was analyzed. Confirm the medications again.',
    );
    await expect(request).rejects.not.toThrow('model_attributes_type');
  });

  it('reports an unknown or expired request separately', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    mockFetch(404, JSON.stringify({ detail: 'Analysis request not found or expired' }));
    await expect(confirmMedications('req-gone', CONFIRMED)).rejects.toThrow(
      'This analysis request has expired or no longer exists (HTTP 404). Upload the prescription again.',
    );
  });
});
