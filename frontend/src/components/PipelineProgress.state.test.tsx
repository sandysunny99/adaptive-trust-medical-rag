import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PipelineProgress } from './PipelineProgress';
import type { PipelineStage, StageUpdate } from '../types';

const STAGES: { key: PipelineStage; label: string }[] = [
  { key: 'uploading', label: 'Input Processing' },
  { key: 'extracting', label: 'Medication Extraction' },
  { key: 'confirming', label: 'User Confirmation' },
  { key: 'normalizing', label: 'RxNorm Canonicalization' },
  { key: 'retrieving', label: 'Evidence Retrieval' },
  { key: 'claim_verifying', label: 'Claim Verification' },
  { key: 'relationship_verifying', label: 'Relationship Verification' },
];

const u = (stage: PipelineStage, status: StageUpdate['status']): StageUpdate => ({ stage, status, timestamp: '' });

function row(label: string) {
  return screen.getByText(label).closest('li') as HTMLElement;
}

describe('PipelineProgress stage states', () => {
  it('never shows user confirmation as complete after a failed extraction', () => {
    // The screenshot case: extraction timed out, so nothing could be confirmed.
    render(<PipelineProgress stages={STAGES} currentStage="error" inputMode="prescription_image"
      updates={[u('extracting', 'running'), u('extracting', 'failed')]} />);
    expect(row('Medication Extraction')).toHaveTextContent('(failed)');
    expect(within(row('User Confirmation')).getByText('Not run')).toBeInTheDocument();
  });

  it('shows confirmation complete only once the backend resumed after it', () => {
    const { rerender } = render(<PipelineProgress stages={STAGES} currentStage="confirming"
      inputMode="prescription_image" updates={[u('extracting', 'complete')]} />);
    expect(row('User Confirmation')).toHaveTextContent('(in progress)');

    rerender(<PipelineProgress stages={STAGES} currentStage="abstained" inputMode="prescription_image"
      updates={[u('extracting', 'complete'), u('uploading', 'complete'), u('normalizing', 'complete')]} />);
    expect(within(row('User Confirmation')).queryByText('Not run')).not.toBeInTheDocument();
    expect(row('User Confirmation')).not.toHaveTextContent('(failed)');
  });

  it('marks a confirmation the user never gave as not run when the stream ended', () => {
    render(<PipelineProgress stages={STAGES} currentStage="error" inputMode="prescription_image"
      updates={[u('extracting', 'complete')]} />);
    expect(within(row('User Confirmation')).getByText('Not run')).toBeInTheDocument();
  });

  it('labels the image-only stages "Not applicable" for manual entry and counts only the rest', () => {
    render(<PipelineProgress stages={STAGES} currentStage="abstained" inputMode="direct_drugs"
      updates={[u('uploading', 'complete'), u('normalizing', 'complete'), u('retrieving', 'complete')]} />);
    expect(screen.getByRole('button', { name: /Pipeline Progress/ })).toHaveTextContent('3 of 5 steps completed');
    expect(within(row('Medication Extraction')).getByText('Not applicable')).toBeInTheDocument();
    expect(within(row('User Confirmation')).getByText('Not applicable')).toBeInTheDocument();
  });

  it('takes relationship verification from claim verification, where it runs', () => {
    render(<PipelineProgress stages={STAGES} currentStage="error" inputMode="direct_drugs"
      updates={[u('claim_verifying', 'failed')]} />);
    expect(row('Relationship Verification')).toHaveTextContent('(failed)');
  });
});
