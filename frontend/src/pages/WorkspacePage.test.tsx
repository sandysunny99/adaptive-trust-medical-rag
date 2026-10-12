import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { WorkspacePage } from './WorkspacePage';
import * as api from '../services/api';
import type { LLMModelInfo } from '../types';

vi.mock('../services/api', () => ({
  fetchModelCatalog: vi.fn(),
  submitAnalysis: vi.fn(),
  submitPrescriptionAnalysis: vi.fn(),
}));

describe('WorkspacePage Model Selector & Catalog Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('TEST 1: Displays warning when model catalog fetch fails', async () => {
    vi.mocked(api.fetchModelCatalog).mockRejectedValueOnce(
      new Error('Failed to fetch model catalog: HTTP 500')
    );

    render(<WorkspacePage />);

    // Initially loading
    expect(screen.getByText('Loading model catalog...')).toBeInTheDocument();

    // After failure, error message appears and dropdown defaults to auto
    await waitFor(() => {
      expect(
        screen.getByText('Could not load remote model catalog. Defaulting to automatic routing.')
      ).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox', { name: /Answer-generation model/i });
    expect(select).not.toBeDisabled();
    expect(screen.getByText('Automatic selection (recommended)')).toBeInTheDocument();
  });

  it('TEST 2: Successfully renders models with unconfigured options disabled', async () => {
    const mockModels: LLMModelInfo[] = [
      {
        id: 'nvidia/nemotron-3-super-120b-a12b',
        provider: 'nvidia',
        name: 'NVIDIA Nemotron-3 Super 120B',
        description: 'Biomedical reasoning model',
        is_available: true,
      },
      {
        id: 'openai/gpt-oss-120b',
        provider: 'groq',
        name: 'Groq GPT-OSS 120B',
        description: 'Open-weights model on Groq',
        is_available: false,
      },
    ];

    vi.mocked(api.fetchModelCatalog).mockResolvedValueOnce(mockModels);

    render(<WorkspacePage />);

    await waitFor(() => {
      expect(screen.getByText(/NVIDIA Nemotron-3 Super 120B/i)).toBeInTheDocument();
    });

    expect(
      screen.getByText('Groq GPT-OSS 120B (groq) — Not configured')
    ).toBeInTheDocument();

    const disabledOption = screen.getByText<HTMLOptionElement>(
      'Groq GPT-OSS 120B (groq) — Not configured'
    );
    expect(disabledOption.disabled).toBe(true);

    const enabledOption = screen.getByText<HTMLOptionElement>(
      'NVIDIA Nemotron-3 Super 120B (nvidia)'
    );
    expect(enabledOption.disabled).toBe(false);
  });
});
