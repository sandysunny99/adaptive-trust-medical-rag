import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { HistoryPage } from './HistoryPage';

vi.mock('../services/historyDb', () => ({
  getAllAnalyses: vi.fn().mockResolvedValue([]),
  deleteAnalysis: vi.fn(),
  clearAllAnalyses: vi.fn(),
}));

describe('HistoryPage privacy note', () => {
  it('states exactly where history lives and that exports leave patient context out', async () => {
    render(<HistoryPage />);
    expect(
      await screen.findByText(
        'Saved analyses, including any patient context, are stored only in this browser. Patient context is left out of exports.'
      )
    ).toBeInTheDocument();
  });
});
