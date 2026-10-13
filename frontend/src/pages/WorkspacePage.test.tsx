import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { WorkspacePage } from './WorkspacePage';
import * as api from '../services/api';
import type { LLMModelInfo } from '../types';

vi.mock('../services/api', () => ({
  fetchModelCatalog: vi.fn(),
  submitAnalysis: vi.fn(),
  submitPrescriptionAnalysis: vi.fn(),
}));

// The model selector lives in the collapsed "Advanced settings" disclosure.
async function openAdvancedSettings() {
  await userEvent.click(screen.getByRole('button', { name: /Advanced settings/i }));
}

describe('WorkspacePage Model Selector & Catalog Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('TEST 1: Displays warning when model catalog fetch fails', async () => {
    // Reject only after the disclosure is open, so the loading state is observable.
    let rejectCatalog: (err: Error) => void = () => {};
    vi.mocked(api.fetchModelCatalog).mockReturnValueOnce(
      new Promise<LLMModelInfo[]>((_, reject) => { rejectCatalog = reject; })
    );

    render(<WorkspacePage />);
    await openAdvancedSettings();

    // Initially loading
    expect(screen.getByText('Loading model catalog...')).toBeInTheDocument();
    rejectCatalog(new Error('Failed to fetch model catalog: HTTP 500'));

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
    await openAdvancedSettings();

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

  it('TEST 3: Model selector is collapsed under Advanced settings by default', async () => {
    vi.mocked(api.fetchModelCatalog).mockResolvedValueOnce([]);
    render(<WorkspacePage />);

    const toggle = screen.getByRole('button', { name: /Advanced settings/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('combobox', { name: /Answer-generation model/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Automatic Failover')).not.toBeInTheDocument();

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('combobox', { name: /Answer-generation model/i })).toHaveValue('auto');
  });
});

describe('WorkspacePage Analyze button states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchModelCatalog).mockResolvedValue([]);
  });

  it('is disabled with a hint until a drug is entered', async () => {
    render(<WorkspacePage />);
    const button = screen.getByRole('button', { name: 'Analyze Medications' });
    expect(button).toBeDisabled();
    expect(button).toHaveAccessibleDescription('Add at least one drug to analyze.');

    await userEvent.type(screen.getByRole('textbox', { name: 'Drug name 1' }), 'Metformin');
    expect(button).toBeEnabled();
    expect(screen.queryByText('Add at least one drug to analyze.')).not.toBeInTheDocument();
  });

  it('asks for an image in prescription mode', async () => {
    render(<WorkspacePage />);
    await userEvent.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    const button = screen.getByRole('button', { name: 'Analyze Medications' });
    expect(button).toBeDisabled();
    expect(button).toHaveAccessibleDescription('Choose a prescription image to analyze.');
  });
});
