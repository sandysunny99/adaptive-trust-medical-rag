import { describe, it, expect } from 'vitest';
import { requestErrorMessage } from './api';

describe('requestErrorMessage', () => {
  it('shows the API detail', async () => {
    const r = new Response(JSON.stringify({ detail: 'Image too large' }), { status: 413 });
    expect(await requestErrorMessage('Image upload failed', r)).toBe('Image upload failed (413): Image too large');
  });

  it('never shows a proxy HTML page', async () => {
    const r = new Response('<!DOCTYPE html><html><title>502</title></html>', { status: 502 });
    const msg = await requestErrorMessage('Image upload failed', r);
    expect(msg).not.toContain('<');
    expect(msg).toContain('restarting');
  });
});
