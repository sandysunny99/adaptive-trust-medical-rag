import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { Layout } from '../Layout';
import { HistoryPage } from '../../pages/HistoryPage';
import { WorkspacePage } from '../../pages/WorkspacePage';

vi.mock('../../services/api', () => ({
  fetchModelCatalog: vi.fn().mockResolvedValue([]),
}));

vi.mock('../../services/historyDb', () => ({
  getAllAnalyses: vi.fn().mockResolvedValue([{
    id: 'synthetic-1',
    timestamp: '2026-10-13T00:00:00.000Z',
    drugNames: ['metformin', 'amoxicillin'],
    inputMode: 'direct_drugs',
    gateDecision: 'release',
    result: {},
  }]),
  deleteAnalysis: vi.fn(),
  clearAllAnalyses: vi.fn(),
  saveAnalysis: vi.fn(),
}));

function expectEveryButtonNamed() {
  for (const button of screen.getAllByRole('button')) {
    expect(button).toHaveAccessibleName();
  }
}

describe('every button, including icon-only ones, has an accessible name', () => {
  it('header and navigation', () => {
    render(<Layout currentPage="analyze" onNavigate={() => {}} showResearchTabs>content</Layout>);
    expectEveryButtonNamed();
    for (const link of screen.getAllByRole('link')) expect(link).toHaveAccessibleName();
  });

  it('History list rows', async () => {
    render(<HistoryPage />);
    expect(await screen.findByRole('button', { name: 'Delete analysis of metformin, amoxicillin' })).toHaveAttribute('title', 'Delete');
    expectEveryButtonNamed();
  });

  it('analysis form with several drugs', async () => {
    render(<WorkspacePage />);
    await userEvent.click(screen.getByRole('button', { name: '+ Add another drug' }));
    expect(screen.getByRole('button', { name: 'Remove drug 2' })).toHaveAttribute('title', 'Remove drug 2');
    expectEveryButtonNamed();
  });
});
