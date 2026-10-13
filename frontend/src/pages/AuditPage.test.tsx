import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { AuditPage } from './AuditPage';
import * as api from '../services/api';
import type { ResearchState } from '../services/api';

vi.mock('../services/api', () => ({
  fetchResearchState: vi.fn(),
}));

const control = (status: string) => ({ status, reason: 'test', reference: 'test' });

const RESEARCH_STATE: ResearchState = {
  dataset_integrity: control('PASS'),
  case_order_integrity: control('PASS'),
  frozen_retrieval: control('PASS'),
  trust_evidence_control: control('VALIDATED'),
  claim_verification: control('VALIDATED'),
  controlled_abstention: control('VALIDATED'),
  prompt_freeze: control('BLOCKED'),
  provider_readiness: control('READY'),
  researcher_authorization: control('NOT_STARTED'),
  real_llm_evaluation: control('NOT_STARTED'),
  medical_evaluation_requests_total: 160,
  medical_evaluation_requests_executed: 0,
  protocol: 'REAL_LLM_EVALUATION_PROTOCOL_V1_2',
};

describe('AuditPage error state', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('shows an error state instead of raw text, and Retry calls the loader again', async () => {
    vi.mocked(api.fetchResearchState)
      .mockRejectedValueOnce(new Error('Failed to fetch research state: 502'))
      .mockResolvedValueOnce(RESEARCH_STATE);

    render(<AuditPage />);

    expect(await screen.findByRole('alert')).toHaveTextContent("Couldn't load research state");
    expect(screen.getByText('Failed to fetch research state: 502')).toBeInTheDocument();
    expect(api.fetchResearchState).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByText('Research Audit Status')).toBeInTheDocument();
    expect(api.fetchResearchState).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
