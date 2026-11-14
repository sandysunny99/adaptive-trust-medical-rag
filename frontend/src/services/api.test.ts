import { describe, it, expect, vi, afterEach } from 'vitest';
import { confirmMedications, connectStream } from './api';

class FakeEventSource {
  static last: FakeEventSource;
  listeners: Record<string, ((e: MessageEvent) => void)[]> = {};
  onerror: ((e: Event) => void) | null = null;
  closed = false;
  url: string;
  constructor(url: string) { this.url = url; FakeEventSource.last = this; }
  addEventListener(type: string, fn: (e: MessageEvent) => void) { (this.listeners[type] ||= []).push(fn); }
  close() { this.closed = true; }
  // Mirrors the browser: a named event runs its listeners, and an 'error' one also runs onerror.
  dispatch(e: Event) {
    for (const fn of this.listeners[e.type] || []) fn(e as MessageEvent);
    if (e.type === 'error') this.onerror?.(e);
  }
}

describe('connectStream', () => {
  afterEach(() => vi.unstubAllGlobals());

  it("does not report the server's own error event as a dropped connection", () => {
    vi.stubGlobal('EventSource', FakeEventSource);
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const onEvent = vi.fn();
    const onError = vi.fn();
    connectStream('/api/v1/stream/r1', onEvent, onError);

    FakeEventSource.last.dispatch(new MessageEvent('error', { data: '{"code":"INPUT_REJECTED","message":"x"}' }));
    expect(onEvent).toHaveBeenCalledWith('error', { code: 'INPUT_REJECTED', message: 'x' });
    expect(onError).not.toHaveBeenCalled();
    expect(consoleError).not.toHaveBeenCalled();

    // A real connection failure (a plain Event) is still reported and closes the stream.
    FakeEventSource.last.dispatch(new Event('error'));
    expect(onError).toHaveBeenCalledTimes(1);
    expect(FakeEventSource.last.closed).toBe(true);
    consoleError.mockRestore();
  });
});
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
