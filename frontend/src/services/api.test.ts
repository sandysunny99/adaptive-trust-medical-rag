import { afterEach, describe, expect, it, vi } from 'vitest';
import { connectStream } from './api';

class MockEventSource {
  static instances: MockEventSource[] = [];
  listeners = new Map<string, (event: MessageEvent) => void>();
  onerror: ((event: Event) => void) | null = null;
  close = vi.fn();

  constructor() {
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    this.listeners.set(type, listener);
  }

  emit(type: string, data?: string) {
    this.listeners.get(type)?.({ data } as MessageEvent);
  }

  emitTransportError() {
    this.onerror?.(new Event('error'));
  }
}

describe('connectStream', () => {
  afterEach(() => {
    MockEventSource.instances = [];
    vi.unstubAllGlobals();
  });

  it('ignores native error events without data and reports the transport error once', () => {
    vi.stubGlobal('EventSource', MockEventSource);
    const onEvent = vi.fn();
    const onError = vi.fn();
    const onClose = vi.fn();

    connectStream('/api/v1/stream/test', onEvent, onError, onClose);
    const source = MockEventSource.instances[0];

    source.emit('error');
    expect(onEvent).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();

    source.emitTransportError();
    expect(onError).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
    expect(source.close).toHaveBeenCalledOnce();
  });

  it('does not report a second transport error after a terminal SSE error event', () => {
    vi.stubGlobal('EventSource', MockEventSource);
    const onEvent = vi.fn();
    const onError = vi.fn();

    connectStream('/api/v1/stream/test', onEvent, onError);
    const source = MockEventSource.instances[0];

    source.emit('error', JSON.stringify({ code: 'PIPELINE_ERROR' }));
    source.emitTransportError();

    expect(onEvent).toHaveBeenCalledWith('error', { code: 'PIPELINE_ERROR' });
    expect(onError).not.toHaveBeenCalled();
  });

  it('delivers medication candidates from the application event stream', () => {
    vi.stubGlobal('EventSource', MockEventSource);
    const onEvent = vi.fn();

    connectStream('/api/v1/stream/test', onEvent);
    const source = MockEventSource.instances[0];

    source.emit(
      'medication_candidates_extracted',
      JSON.stringify({ candidates: [{ raw_text: 'metformin' }] }),
    );

    expect(onEvent).toHaveBeenCalledWith(
      'medication_candidates_extracted',
      { candidates: [{ raw_text: 'metformin' }] },
    );
  });
});
