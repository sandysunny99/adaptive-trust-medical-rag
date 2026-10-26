import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SecurityChecks } from './SecurityChecks';
import type { AnalysisResult } from '../../types';

// AUD-12 (2026-10-26 audit): the backend excludes retrieved chunks that carry instructions and
// says so in injection_reason; the row must show that, not "No injection markers detected".
function withSecurity(security: Record<string, unknown>): AnalysisResult {
  return { security } as unknown as AnalysisResult;
}

describe('SecurityChecks prompt-injection row', () => {
  it('shows why retrieved evidence was blocked', () => {
    render(<SecurityChecks result={withSecurity({
      injection_status: 'BLOCK',
      injection_reason: 'Excluded 1 retrieved chunk(s) carrying instructions',
      poisoning_status: 'ALLOW',
      poisoning_reason: null,
    })} />);
    expect(screen.getByText('Excluded 1 retrieved chunk(s) carrying instructions')).toBeInTheDocument();
    expect(screen.queryByText('No injection markers detected')).not.toBeInTheDocument();
  });

  it('says nothing was detected only when the gate allowed everything', () => {
    render(<SecurityChecks result={withSecurity({
      injection_status: 'ALLOW',
      injection_reason: null,
      poisoning_status: 'ALLOW',
      poisoning_reason: null,
    })} />);
    expect(screen.getByText('No injection markers detected')).toBeInTheDocument();
  });
});
