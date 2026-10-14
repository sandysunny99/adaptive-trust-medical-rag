import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { PipelineProgress } from './PipelineProgress';
import type { PipelineStage } from '../types';

const STAGES: { key: PipelineStage; label: string }[] = [
  { key: 'uploading', label: 'Input Processing' },
  { key: 'retrieving', label: 'Evidence Retrieval' },
  { key: 'safety_gating', label: 'Safety Gate' },
];

describe('PipelineProgress', () => {
  it('shows the full step list while running', () => {
    render(<PipelineProgress stages={STAGES} currentStage="retrieving" updates={[]} />);
    expect(screen.getByText('Input Processing')).toBeVisible();
    expect(screen.getByText(/Evidence Retrieval/)).toHaveTextContent('(in progress)');
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('collapses to one summary row with the backend processing time when finished', async () => {
    render(<PipelineProgress stages={STAGES} currentStage="complete" updates={[]} processingTimeMs={14234} />);
    const summary = screen.getByRole('button', { name: /Pipeline Progress/ });
    expect(summary).toHaveTextContent('3 of 3 steps completed · 14.2 s');
    expect(summary).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('Input Processing')).not.toBeVisible();

    await userEvent.click(summary);
    expect(screen.getByText('Input Processing')).toBeVisible();
  });

  it('omits the time when the payload has none', () => {
    render(<PipelineProgress stages={STAGES} currentStage="complete" updates={[]} />);
    expect(screen.getByRole('button', { name: /Pipeline Progress/ })).toHaveTextContent('3 of 3 steps completed');
    expect(screen.getByRole('button', { name: /Pipeline Progress/ })).not.toHaveTextContent(' s)');
  });

  it('counts only the stages that ran when the analysis abstained', async () => {
    const updates = [{ stage: 'uploading' as PipelineStage, status: 'complete' as const, timestamp: '' }];
    render(<PipelineProgress stages={STAGES} currentStage="abstained" updates={updates} />);
    const summary = screen.getByRole('button', { name: /Pipeline Progress/ });
    expect(summary).toHaveTextContent('1 of 3 steps completed');

    await userEvent.click(summary);
    expect(screen.getAllByText('Not run')).toHaveLength(2);
  });

  it('stays expanded when a step failed', () => {
    render(<PipelineProgress stages={STAGES} currentStage="error" updates={[]} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(screen.getByText('Safety Gate')).toBeVisible();
  });
});
