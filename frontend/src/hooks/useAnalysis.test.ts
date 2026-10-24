import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useAnalysis } from './useAnalysis';
import * as api from '../services/api';

// Synthetic drug names only; no patient data.
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, submitAnalysis: vi.fn(), connectStream: vi.fn() };
});

type Handler = (event: string, data: unknown) => void;

function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>(r => { resolve = r; });
  return { promise, resolve };
}

const TEXT = 'drug_names' as never;

describe('useAnalysis stale-result prevention', () => {
  const handlers = new Map<string, Handler>();

  beforeEach(() => {
    handlers.clear();
    vi.mocked(api.connectStream).mockReset();
    vi.mocked(api.submitAnalysis).mockReset();
    vi.mocked(api.connectStream).mockImplementation(((url: string, onEvent: Handler) => {
      handlers.set(url, onEvent);
      return () => { handlers.delete(url); };
    }) as never);
  });

  it('never connects the stream of an analysis replaced while it was still submitting', async () => {
    const first = deferred<{ request_id: string; stream_url: string }>();
    vi.mocked(api.submitAnalysis)
      .mockImplementationOnce(() => first.promise as never)
      .mockResolvedValueOnce({ request_id: 'req-new', stream_url: '/stream/new' } as never);

    const { result } = renderHook(() => useAnalysis());
    let firstRun: Promise<void> | undefined;
    act(() => { firstRun = result.current.analyze({ drugNames: ['DrugA'], inputMode: TEXT }); });
    await act(async () => { await result.current.analyze({ drugNames: ['DrugB'], inputMode: TEXT }); });
    await act(async () => {
      first.resolve({ request_id: 'req-old', stream_url: '/stream/old' });
      await firstRun;
    });

    expect(handlers.has('/stream/old')).toBe(false);
    expect(handlers.has('/stream/new')).toBe(true);
  });

  it('ignores events from an earlier stream once a new analysis starts', async () => {
    vi.mocked(api.submitAnalysis)
      .mockResolvedValueOnce({ request_id: 'req-1', stream_url: '/stream/1' } as never)
      .mockResolvedValueOnce({ request_id: 'req-2', stream_url: '/stream/2' } as never);
    const { result } = renderHook(() => useAnalysis());

    await act(async () => { await result.current.analyze({ drugNames: ['DrugA'], inputMode: TEXT }); });
    const oldHandler = handlers.get('/stream/1')!;
    await act(async () => { await result.current.analyze({ drugNames: ['DrugB'], inputMode: TEXT }); });

    act(() => oldHandler('answer', { conclusion: 'stale answer', claims: [], evidence: [] }));
    expect(result.current.result).toBeNull();

    act(() => handlers.get('/stream/2')!('abstention', { reason: 'current abstention', trust: {} }));
    await waitFor(() => expect(result.current.result?.abstention_reason).toBe('current abstention'));
    expect(result.current.result?.conclusion).toBeUndefined();
  });

  it('keeps the excluded sources and abstention state the backend reports', async () => {
    vi.mocked(api.submitAnalysis).mockResolvedValueOnce({ request_id: 'r', stream_url: '/stream/r' } as never);
    const { result } = renderHook(() => useAnalysis());
    await act(async () => { await result.current.analyze({ drugNames: ['DrugA', 'DrugB'], inputMode: TEXT }); });
    const excluded = [{
      chunk_id: 'c1', document_id: 'SPL-PLACEHOLDER', source_link_status: 'PLACEHOLDER',
      source_identity_status: 'REJECTED_SOURCE_IDENTITY', reason: 'placeholder link',
    }];
    act(() => handlers.get('/stream/r')!('abstention', { reason: 'no verified evidence', trust: {}, excluded_sources: excluded }));
    expect(result.current.result?.excluded_sources).toEqual(excluded);
    expect(result.current.result?.gate_decision).toBe('abstain');
    expect(result.current.currentStage).toBe('abstained');
  });
});
