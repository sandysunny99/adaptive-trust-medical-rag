import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import App from './App';

vi.mock('./services/api', () => ({
  fetchModelCatalog: vi.fn().mockResolvedValue([]),
  fetchResearchState: vi.fn().mockRejectedValue(new Error('offline')),
}));

vi.mock('./services/historyDb', () => ({
  getAllAnalyses: vi.fn().mockResolvedValue([]),
  deleteAnalysis: vi.fn(),
  clearAllAnalyses: vi.fn(),
  saveAnalysis: vi.fn(),
}));

describe('App keeps Analyze mounted', () => {
  beforeEach(() => {
    window.location.hash = '';
  });

  it('hides Analyze (not unmounts) on other pages and restores typed input', async () => {
    render(<App />);
    const input = screen.getByRole('textbox', { name: 'Drug name 1' });
    await userEvent.type(input, 'Metformin');

    await userEvent.click(screen.getByRole('link', { name: 'History' }));
    expect(screen.queryByRole('textbox', { name: 'Drug name 1' })).not.toBeInTheDocument();
    // Still in the DOM, but hidden from the accessibility tree.
    expect(input.closest('[hidden]')).not.toBeNull();

    await userEvent.click(screen.getByRole('link', { name: 'Analyze' }));
    expect(screen.getByRole('textbox', { name: 'Drug name 1' })).toHaveValue('Metformin');
  });

  it('falls back to Analyze for an unknown hash', async () => {
    render(<App />);
    await act(async () => {
      window.location.hash = '#does-not-exist';
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });
    expect(screen.getByRole('link', { name: 'Analyze' })).toHaveAttribute('aria-current', 'page');
  });
});
