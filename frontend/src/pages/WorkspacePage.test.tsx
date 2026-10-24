import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { WorkspacePage } from './WorkspacePage';
import * as api from '../services/api';
import type { LLMModelInfo } from '../types';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    fetchModelCatalog: vi.fn(),
    submitAnalysis: vi.fn(),
    submitPrescriptionImage: vi.fn(),
    confirmMedications: vi.fn(),
    connectStream: vi.fn(),
    cancelAnalysis: vi.fn(),
  };
});

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

function png(name = 'rx.png', size?: number, type = 'image/png') {
  const file = new File(['png-bytes'], name, { type });
  if (size !== undefined) Object.defineProperty(file, 'size', { value: size });
  return file;
}

const fileDrag = (files: File[] = []) => ({ dataTransfer: { types: ['Files'], files } });

describe('WorkspacePage prescription upload', () => {
  let objectUrlCount = 0;

  beforeEach(() => {
    vi.clearAllMocks();
    objectUrlCount = 0;
    vi.mocked(api.fetchModelCatalog).mockResolvedValue([]);
    vi.mocked(api.connectStream).mockReturnValue(vi.fn());
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: vi.fn(() => `blob:preview-${++objectUrlCount}`),
    });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, writable: true, value: vi.fn() });
  });

  async function openUploadTab() {
    const user = userEvent.setup({ applyAccept: false });
    const view = render(<WorkspacePage />);
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    const dropzone = screen.getByTestId('prescription-dropzone');
    const input = screen.getByLabelText('Prescription image file') as HTMLInputElement;
    return { user, view, dropzone, input };
  }

  it('opens the file picker from a keyboard-operable browse button', async () => {
    const { user, input } = await openUploadTab();
    const pick = vi.spyOn(input, 'click').mockImplementation(() => undefined);

    const browse = screen.getByRole('button', { name: 'Browse files' });
    expect(browse).toHaveAccessibleDescription('One JPEG, PNG or WEBP image • Max 5 MB');
    browse.focus();
    await user.keyboard('{Enter}');
    expect(pick).toHaveBeenCalledTimes(1);
    await user.keyboard(' ');
    expect(pick).toHaveBeenCalledTimes(2);
  });

  it('opens the file picker when the empty zone is clicked', async () => {
    const { user, dropzone, input } = await openUploadTab();
    const pick = vi.spyOn(input, 'click').mockImplementation(() => undefined);
    await user.click(dropzone);
    expect(pick).toHaveBeenCalledTimes(1);
    // The Browse button opens it once, not twice.
    await user.click(screen.getByRole('button', { name: 'Browse files' }));
    expect(pick).toHaveBeenCalledTimes(2);
  });

  it('shows drag state and accepts a dropped image with a preview', async () => {
    const { dropzone } = await openUploadTab();

    expect(fireEvent.dragEnter(dropzone, fileDrag())).toBe(false);
    expect(dropzone).toHaveAttribute('data-dragging', 'true');
    expect(screen.getByText('Drop the image to upload it')).toBeInTheDocument();
    // preventDefault on dragover is what makes the zone a valid drop target.
    expect(fireEvent.dragOver(dropzone, fileDrag())).toBe(false);

    fireEvent.dragLeave(dropzone, fileDrag());
    expect(dropzone).toHaveAttribute('data-dragging', 'false');

    fireEvent.dragEnter(dropzone, fileDrag());
    expect(fireEvent.drop(dropzone, fileDrag([png('dropped.png')]))).toBe(false);
    expect(dropzone).toHaveAttribute('data-dragging', 'false');

    expect(await screen.findByRole('img', { name: 'Preview of dropped.png' })).toHaveAttribute('src', 'blob:preview-1');
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeEnabled();
  });

  it('keeps the drag state while moving over child elements', async () => {
    const { dropzone } = await openUploadTab();
    fireEvent.dragEnter(dropzone, fileDrag());
    fireEvent.dragEnter(screen.getByRole('button', { name: 'Browse files' }), fileDrag());
    fireEvent.dragLeave(dropzone, fileDrag());
    expect(dropzone).toHaveAttribute('data-dragging', 'true');
    fireEvent.dragLeave(dropzone, fileDrag());
    expect(dropzone).toHaveAttribute('data-dragging', 'false');
  });

  it('stops a file dropped outside the zone from replacing the app', async () => {
    await openUploadTab();
    expect(fireEvent.dragOver(document.body, fileDrag())).toBe(false);
    expect(fireEvent.drop(document.body, fileDrag([png('outside.png')]))).toBe(false);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeDisabled();
  });

  it('rejects multiple dropped files', async () => {
    const { dropzone } = await openUploadTab();
    fireEvent.drop(dropzone, fileDrag([png('a.png'), png('b.png')]));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Only one prescription image can be uploaded at a time; 2 files were provided.',
    );
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeDisabled();
  });

  it('rejects the wrong type, an empty file and a file over 5 MB', async () => {
    const { user, input } = await openUploadTab();

    await user.upload(input, new File(['%PDF'], 'scan.pdf', { type: 'application/pdf' }));
    expect(screen.getByRole('alert')).toHaveTextContent('"scan.pdf" is not a supported image. Use a JPEG, PNG or WEBP file');

    await user.upload(input, png('empty.png', 0));
    expect(screen.getByRole('alert')).toHaveTextContent('"empty.png" is empty (0 bytes).');

    await user.upload(input, png('huge.png', 6 * 1024 * 1024));
    expect(screen.getByRole('alert')).toHaveTextContent('"huge.png" is 6.0 MB, which exceeds the 5 MB upload limit.');

    expect(URL.createObjectURL).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeDisabled();
  });

  it('replaces and removes the image, revoking each preview URL', async () => {
    const { user, input, view } = await openUploadTab();

    await user.upload(input, png('first.png'));
    expect(await screen.findByRole('img', { name: 'Preview of first.png' })).toHaveAttribute('src', 'blob:preview-1');

    const pick = vi.spyOn(input, 'click').mockImplementation(() => undefined);
    await user.click(screen.getByRole('button', { name: 'Replace image' }));
    expect(pick).toHaveBeenCalledTimes(1);
    await user.upload(input, png('second.png'));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-1');
    expect(await screen.findByRole('img', { name: 'Preview of second.png' })).toHaveAttribute('src', 'blob:preview-2');

    // An invalid replacement keeps the current image and explains why.
    await user.upload(input, png('third.gif', 10, 'image/gif'));
    expect(screen.getByRole('alert')).toHaveTextContent('"third.gif" is not a supported image');
    expect(screen.getByRole('img', { name: 'Preview of second.png' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Remove image' }));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-2');
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Browse files' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeDisabled();

    await user.upload(input, png('third.png'));
    expect(await screen.findByRole('img', { name: 'Preview of third.png' })).toBeInTheDocument();
    view.unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-3');
  });

  it('keeps the chosen image and its preview after switching input mode and back', async () => {
    const { user, input } = await openUploadTab();
    await user.upload(input, png('kept.png'));
    expect(screen.getByRole('img', { name: 'Preview of kept.png' })).toHaveAttribute('src', 'blob:preview-1');

    await user.click(screen.getByRole('tab', { name: 'Enter Drug Names' }));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview-1');
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    expect(screen.getByRole('img', { name: 'Preview of kept.png' })).toHaveAttribute('src', 'blob:preview-2');
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeEnabled();
  });

  it('submits the chosen image when Analyze is clicked', async () => {
    vi.mocked(api.submitPrescriptionImage).mockResolvedValue({ request_id: 'req-1', stream_url: '/api/v1/stream/req-1', validation: {} });
    const { user, input } = await openUploadTab();
    const image = png('rx.png');
    await user.upload(input, image);
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.submitPrescriptionImage).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.submitPrescriptionImage).mock.calls[0][0]).toBe(image);
    expect(api.connectStream).toHaveBeenCalledWith('/api/v1/stream/req-1', expect.any(Function), expect.any(Function));
  });
});

describe('WorkspacePage prescription confirmation', () => {
  type Handler = (event: string, data: unknown) => void;
  let emit: Handler = () => undefined;
  let streamClosed: () => void = () => undefined;
  let disconnect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchModelCatalog).mockResolvedValue([]);
    vi.mocked(api.submitPrescriptionImage).mockResolvedValue({ request_id: 'req-7', stream_url: '/api/v1/stream/req-7', validation: {} });
    vi.mocked(api.cancelAnalysis).mockResolvedValue('cancelled');
    disconnect = vi.fn();
    vi.mocked(api.connectStream).mockImplementation((_url, onEvent, onError) => {
      emit = onEvent as Handler;
      streamClosed = () => onError?.(new Event('error'));
      return disconnect;
    });
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, writable: true, value: vi.fn(() => 'blob:rx') });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, writable: true, value: vi.fn() });
  });

  async function reachConfirmation() {
    const user = userEvent.setup();
    render(<WorkspacePage />);
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    await user.upload(screen.getByLabelText('Prescription image file'), new File(['png'], 'rx.png', { type: 'image/png' }));
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalled());
    act(() => {
      emit('medication_candidates_extracted', {
        candidates: [
          { id: 'ocr-0', raw_text: 'Simvastatin 40 mg', normalized_text: 'Simvastatin', confidence: 'HIGH', status: 'DETECTED', source: 'VISION' },
          { id: 'ocr-1', raw_text: 'Clarithromycin 500 mg', normalized_text: 'Clarithromycin', confidence: 'HIGH', status: 'DETECTED', source: 'VISION' },
        ],
      });
      emit('confirmation_required', {});
    });
    for (const button of screen.getAllByRole('button', { name: 'Confirm' })) await user.click(button);
    await user.click(screen.getByRole('button', { name: /Confirm Medications & Analyze/i }));
    return user;
  }

  it('sends the reviewed candidates as objects to the same request', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    expect(api.confirmMedications).toHaveBeenCalledTimes(1);
    expect(api.confirmMedications).toHaveBeenCalledWith('req-7', [
      { name: 'Simvastatin', status: 'CONFIRMED', source: 'VISION', raw_detected_name: 'Simvastatin 40 mg' },
      { name: 'Clarithromycin', status: 'CONFIRMED', source: 'VISION', raw_detected_name: 'Clarithromycin 500 mg' },
    ]);
    // A 200 from /confirm is not a finished analysis: the page waits for the stream.
    expect(screen.getByText('Analyzing…')).toBeInTheDocument();
  });

  it('shows the review panel when the image yields no medications, so one can be added by hand', async () => {
    // Without the panel the backend waits for a confirmation that can never be sent (CONFIRMATION_TIMEOUT).
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    const user = userEvent.setup();
    render(<WorkspacePage />);
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    await user.upload(screen.getByLabelText('Prescription image file'), new File(['png'], 'rx.png', { type: 'image/png' }));
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalled());
    act(() => {
      emit('medication_candidates_extracted', { candidates: [] });
      emit('confirmation_required', {});
    });
    expect(screen.getByText('No medications detected.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Confirm Medications & Analyze/i })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: /Add medication manually/i }));
    await user.type(screen.getByPlaceholderText('Enter medication name'), 'Lisinopril');
    await user.click(screen.getByRole('button', { name: 'Add' }));
    await user.click(screen.getByRole('button', { name: /Confirm Medications & Analyze/i }));
    expect(api.confirmMedications).toHaveBeenCalledWith('req-7', [
      expect.objectContaining({ name: 'Lisinopril', source: 'USER' }),
    ]);
  });

  it('shows an abstention after confirmation as a result, not a disconnected stream', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    act(() => {
      emit('rxnorm', { entities: [{ raw_text: 'Simvastatin', canonical_name: 'simvastatin', rxcui: '36567', status: 'MATCHED', source: 'VISION' }] });
      emit('trust', { overall_score: 0, threshold: 0.3, risk_class: 'R0', is_eligible: false, factors: {}, missing_factors: [] });
      emit('abstention', {
        reason: 'Insufficient eligible evidence retrieved to meet trust threshold.',
        trust: { overall_score: 0, threshold: 0.3, risk_class: 'R0' },
      });
    });
    // The backend closes the stream right after an abstention; that close is not a failure.
    expect(disconnect).toHaveBeenCalled();
    act(() => streamClosed());
    expect(screen.getByText('The system abstained from answering.')).toBeInTheDocument();
    expect(screen.getByText('Insufficient eligible evidence retrieved to meet trust threshold.')).toBeInTheDocument();
    expect(screen.queryByText(/Analysis Failed|disconnected unexpectedly/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeEnabled();
  });

  it('does not mark stages after an early abstention as completed', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    act(() => {
      for (const stage of ['uploading', 'extracting', 'normalizing', 'retrieving', 'security_checking', 'trust_evaluating']) {
        emit('stage_update', { stage, status: 'complete', timestamp: '2026-10-13T00:00:00Z' });
      }
      emit('abstention', { reason: 'Insufficient eligible evidence retrieved to meet trust threshold.', trust: { overall_score: 0, threshold: 0.3, risk_class: 'R0' } });
    });
    const row = (label: string) => screen.getByText(label).parentElement as HTMLElement;
    for (const label of ['LLM Analysis', 'Claim Verification', 'Safety Gate', 'Relationship Verification']) {
      expect(within(row(label)).getByText('Not run')).toBeInTheDocument();
    }
    for (const label of ['Trust Evaluation', 'Evidence Retrieval', 'User Confirmation']) {
      expect(within(row(label)).queryByText('Not run')).not.toBeInTheDocument();
    }
  });

  it('shows the evidence a post-generation abstention was checked against', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    act(() => {
      emit('abstention', {
        reason: '3 of 3 generated claims failed post-generation verification.',
        trust: { overall_score: 0.94, threshold: 0.3, risk_class: 'R0', is_eligible: true },
        evidence: [{
          chunk_id: 'DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01', document_id: 'SPL-SIMVASTATIN-001',
          source_type: 'DAILYMED', source_name: 'https://dailymed.example', title: 'Evidence [Source 1]',
          text: 'Simvastatin label text', source_authority: 0.95, trust_score: 0.94, freshness: 0.9,
          retrieval_method: 'hybrid-rrf', provenance_status: 'RETRIEVED',
        }],
      });
    });
    act(() => streamClosed());
    expect(screen.getByText('Evidence & Sources (1)')).toBeInTheDocument();
    expect(screen.queryByText(/No evidence/)).not.toBeInTheDocument();
  });

  it('shows why the risk tier was chosen and how many unrelated chunks were left out', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    act(() => {
      emit('trust', {
        overall_score: 0.94, threshold: 0.75, risk_class: 'R3', is_eligible: true,
        risk_basis: 'approved relationship record REL-1: simvastatin and clarithromycin contraindicated',
        unrelated_excluded: 3, factors: {}, missing_factors: [],
      });
      emit('abstention', {
        reason: '1 of 1 generated claims failed post-generation verification.',
        trust: {
          overall_score: 0.94, threshold: 0.75, risk_class: 'R3', is_eligible: true,
          risk_basis: 'approved relationship record REL-1: simvastatin and clarithromycin contraindicated',
        },
      });
    });
    act(() => streamClosed());
    expect(screen.getByText(/Risk tier basis: approved relationship record REL-1/)).toBeInTheDocument();
    expect(screen.getByText('3 retrieved chunk(s) named none of these medications and were excluded.')).toBeInTheDocument();
    expect(screen.getByText('0.75')).toBeInTheDocument();
  });

  it('says no evidence was eligible when an abstention carries none', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    act(() => {
      emit('abstention', { reason: 'none was eligible', trust: { overall_score: 0.2, threshold: 0.3, risk_class: 'R0', is_eligible: false } });
    });
    act(() => streamClosed());
    expect(screen.getByText('No evidence passed the eligibility checks for this analysis.')).toBeInTheDocument();
  });

  it('still reports a stream that drops before any terminal event', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' });
    await reachConfirmation();
    act(() => streamClosed());
    expect(screen.getByText(/disconnected unexpectedly/)).toBeInTheDocument();
  });

  it('shows a readable confirmation error instead of the raw validation payload', async () => {
    vi.mocked(api.confirmMedications).mockRejectedValue(new Error(api.confirmationErrorMessage(422)));
    await reachConfirmation();
    expect(await screen.findByText(/rejected the medication confirmation as invalid \(HTTP 422\)/)).toBeInTheDocument();
    expect(screen.queryByText(/model_attributes_type|confirmed_medications/)).not.toBeInTheDocument();
  });

  it('shows a refused confirmation (409) as an error, never as an analysis in progress', async () => {
    vi.mocked(api.confirmMedications).mockRejectedValue(new Error(api.confirmationErrorMessage(409)));
    await reachConfirmation();
    expect(await screen.findByText(/not waiting for a confirmation, or has already ended \(HTTP 409\)/)).toBeInTheDocument();
    expect(screen.queryByText('Analyzing…')).not.toBeInTheDocument();
    expect(api.confirmMedications).toHaveBeenCalledTimes(1);
  });

  it('offers a new upload when the image yields no medications, leaving the old analysis', async () => {
    const user = userEvent.setup();
    render(<WorkspacePage />);
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    await user.upload(screen.getByLabelText('Prescription image file'), new File(['png'], 'rx.png', { type: 'image/png' }));
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalled());
    act(() => {
      emit('medication_candidates_extracted', { candidates: [] });
      emit('confirmation_required', {});
    });
    expect(screen.getByRole('status')).toHaveTextContent(/No medications could be read from this image/);
    await user.click(screen.getByRole('button', { name: 'Cancel and upload a different image' }));
    await waitFor(() => expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument());
    expect(api.cancelAnalysis).toHaveBeenCalledWith('req-7');  // the server ends the old request
    expect(disconnect).toHaveBeenCalled();  // the old stream is closed
    expect(api.confirmMedications).not.toHaveBeenCalled();
  });

  async function reachReview() {
    const user = userEvent.setup();
    render(<WorkspacePage />);
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    await user.upload(screen.getByLabelText('Prescription image file'), new File(['png'], 'rx.png', { type: 'image/png' }));
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalled());
    act(() => {
      emit('medication_candidates_extracted', { candidates: [
        { id: 'ocr-0', raw_text: 'Warfarin 5 mg', normalized_text: 'warfarin', confidence: 'HIGH', status: 'DETECTED',
          source: 'VISION', image_text_evidence: 'Warfarin' },
      ] });
      emit('confirmation_required', {});
    });
    return user;
  }

  it('abandons a request under review without a reload: the server cancels it and its late events change nothing', async () => {
    const user = await reachReview();
    const oldEmit = emit;
    await user.click(screen.getByRole('button', { name: 'Cancel and upload a different image' }));
    await waitFor(() => expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument());
    expect(api.cancelAnalysis).toHaveBeenCalledTimes(1);
    expect(api.cancelAnalysis).toHaveBeenCalledWith('req-7');
    expect(api.confirmMedications).not.toHaveBeenCalled();
    // Back on the form, focused on choosing another image.
    await waitFor(() => expect(document.activeElement).toHaveTextContent('Replace image'));
    expect(screen.getByRole('button', { name: 'Analyze Medications' })).toBeEnabled();

    // A late event of the abandoned request is ignored.
    act(() => {
      oldEmit('medication_candidates_extracted', { candidates: [
        { id: 'ocr-0', raw_text: 'Stale', normalized_text: 'stale', confidence: 'HIGH', status: 'DETECTED', source: 'VISION' },
      ] });
      oldEmit('confirmation_required', {});
    });
    expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument();

    // A new upload is a new request with its own candidates.
    vi.mocked(api.submitPrescriptionImage).mockResolvedValue({ request_id: 'req-8', stream_url: '/api/v1/stream/req-8', validation: {} });
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalledTimes(2));
    expect(vi.mocked(api.connectStream).mock.calls[1][0]).toBe('/api/v1/stream/req-8');
    act(() => {
      emit('medication_candidates_extracted', { candidates: [
        { id: 'ocr-0', raw_text: 'Ibuprofen 400 mg', normalized_text: 'ibuprofen', confidence: 'HIGH', status: 'DETECTED',
          source: 'VISION', image_text_evidence: 'Ibuprofen' },
      ] });
      emit('confirmation_required', {});
    });
    expect(screen.getByText('ibuprofen')).toBeInTheDocument();
    expect(screen.queryByText('warfarin')).not.toBeInTheDocument();
    expect(screen.queryByText('stale')).not.toBeInTheDocument();
  });

  it('sends one cancel however often it is clicked', async () => {
    let finish: (v: 'cancelled') => void = () => undefined;
    vi.mocked(api.cancelAnalysis).mockReturnValue(new Promise(resolve => { finish = resolve; }));
    const user = await reachReview();
    await user.click(screen.getByRole('button', { name: 'Cancel and upload a different image' }));
    const pending = screen.getAllByRole('button', { name: 'Cancelling…' });  // the panel's and the form's
    expect(pending).toHaveLength(2);
    for (const button of pending) {
      expect(button).toBeDisabled();
      await user.click(button);
    }
    expect(api.cancelAnalysis).toHaveBeenCalledTimes(1);
    await act(async () => finish('cancelled'));
    await waitFor(() => expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument());
  });

  it('reports a cancellation the server did not acknowledge, keeps the old stream out, and retries it', async () => {
    vi.mocked(api.cancelAnalysis).mockRejectedValueOnce(new TypeError('Failed to fetch'));
    const user = await reachReview();
    const oldEmit = emit;
    await user.click(screen.getByRole('button', { name: 'Cancel and upload a different image' }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/did not confirm that the earlier image analysis was cancelled/);
    expect(screen.queryByText(/has ended on the server/)).not.toBeInTheDocument();  // no false success
    expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument();
    await waitFor(() => expect(document.activeElement).toHaveTextContent('Replace image'));  // no reload needed

    // While it is unresolved, the old stream changes nothing.
    const stale = { id: 'ocr-0', raw_text: 'Stale', normalized_text: 'stale', confidence: 'HIGH', status: 'DETECTED', source: 'VISION' };
    act(() => {
      oldEmit('medication_candidates_extracted', { candidates: [stale] });
      oldEmit('confirmation_required', {});
      oldEmit('error', { code: 'CONFIRMATION_TIMEOUT', message: 'late' });
    });
    expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument();
    expect(screen.queryByText('Analysis Failed')).not.toBeInTheDocument();

    // A new upload meanwhile is its own request; the old one cannot attach to it.
    vi.mocked(api.submitPrescriptionImage).mockResolvedValue({ request_id: 'req-8', stream_url: '/api/v1/stream/req-8', validation: {} });
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalledTimes(2));
    act(() => {
      emit('medication_candidates_extracted', { candidates: [
        { id: 'ocr-0', raw_text: 'Ibuprofen 400 mg', normalized_text: 'ibuprofen', confidence: 'HIGH', status: 'DETECTED', source: 'VISION' },
      ] });
      emit('confirmation_required', {});
      oldEmit('medication_candidates_extracted', { candidates: [stale] });
    });
    expect(screen.getByText('ibuprofen')).toBeInTheDocument();
    expect(screen.queryByText('stale')).not.toBeInTheDocument();

    // The retry reaches the server; its first cancel may have landed, so "already ended" also resolves it.
    vi.mocked(api.cancelAnalysis).mockResolvedValueOnce('already_ended');
    await user.click(screen.getByRole('button', { name: 'Retry cancellation' }));
    expect(await screen.findByText('The earlier image analysis has ended on the server.')).toBeInTheDocument();
    expect(screen.queryByText(/did not confirm/)).not.toBeInTheDocument();
    expect(vi.mocked(api.cancelAnalysis).mock.calls).toEqual([['req-7'], ['req-7']]);  // never the new request
    expect(screen.getByText('ibuprofen')).toBeInTheDocument();
    expect(api.confirmMedications).not.toHaveBeenCalled();
  });

  it('says so again when a retry gets no answer either, sending one retry at a time', async () => {
    vi.mocked(api.cancelAnalysis).mockRejectedValueOnce(new Error('The analysis could not be cancelled (HTTP 502).'));
    const user = await reachReview();
    await user.click(screen.getByRole('button', { name: 'Cancel and upload a different image' }));
    await screen.findByRole('alert');
    let fail: () => void = () => undefined;
    vi.mocked(api.cancelAnalysis).mockReturnValueOnce(new Promise((_, reject) => { fail = () => reject(new Error('timeout')); }));
    await user.click(screen.getByRole('button', { name: 'Retry cancellation' }));
    const retrying = screen.getByRole('button', { name: 'Retrying…' });
    expect(retrying).toBeDisabled();
    await user.click(retrying);
    expect(api.cancelAnalysis).toHaveBeenCalledTimes(2);
    await act(async () => fail());
    expect(screen.getByRole('alert')).toHaveTextContent(/still has not confirmed/);
    expect(screen.getByRole('button', { name: 'Retry cancellation' })).toBeEnabled();
    expect(screen.queryByText(/has ended on the server/)).not.toBeInTheDocument();
    expect(api.confirmMedications).not.toHaveBeenCalled();
  });
  async function startImageAnalysis() {
    const user = userEvent.setup();
    render(<WorkspacePage />);
    await user.click(screen.getByRole('tab', { name: 'Upload Prescription' }));
    await user.upload(screen.getByLabelText('Prescription image file'), new File(['png'], 'rx.png', { type: 'image/png' }));
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalled());
    // A slow image read or provider: the extraction stage starts, and nothing else arrives yet.
    act(() => emit('stage_update', { stage: 'extracting', status: 'running', message: 'Reading the image' }));
    return user;
  }
  const stale = { id: 'ocr-0', raw_text: 'Stale', normalized_text: 'stale', confidence: 'HIGH', status: 'DETECTED', source: 'VISION' };

  it('offers Cancel analysis while the image is still being read, before any medication is shown', async () => {
    let finish: (v: 'cancelled') => void = () => undefined;
    vi.mocked(api.cancelAnalysis).mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
    const user = await startImageAnalysis();
    const oldEmit = emit;
    expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Cancel analysis' }));
    const cancelling = screen.getByRole('button', { name: 'Cancelling…' });
    expect(cancelling).toBeDisabled();  // cancelling is not yet cancelled
    expect(screen.queryByText(/was cancelled; nothing from it was analysed/)).not.toBeInTheDocument();
    await user.click(cancelling);
    expect(vi.mocked(api.cancelAnalysis).mock.calls).toEqual([['req-7']]);
    await act(async () => finish('cancelled'));
    expect(await screen.findByText(/The image analysis was cancelled; nothing from it was analysed/)).toBeInTheDocument();
    expect(disconnect).toHaveBeenCalled();
    await waitFor(() => expect(document.activeElement).toHaveTextContent('Replace image'));
    expect(screen.queryByRole('button', { name: /Cancel analysis|Cancelling/ })).not.toBeInTheDocument();

    act(() => {  // late events of the abandoned request change nothing
      oldEmit('medication_candidates_extracted', { candidates: [stale] });
      oldEmit('confirmation_required', {});
    });
    expect(screen.queryByText('Review Detected Medications')).not.toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Enter Drug Names' })).toBeEnabled();  // manual entry stays open
    expect(api.confirmMedications).not.toHaveBeenCalled();
  });

  it('keeps Cancel analysis through the review; both cancel controls share one cancellation, and nothing is confirmed', async () => {
    let finish: (v: 'cancelled') => void = () => undefined;
    vi.mocked(api.cancelAnalysis).mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
    const user = await reachReview();
    await user.click(screen.getByRole('button', { name: 'Confirm' }));
    await user.click(screen.getByRole('button', { name: 'Cancel analysis' }));
    await user.click(screen.getByRole('button', { name: /Confirm Medications & Analyze/ }));  // too late: cancelling
    await user.click(screen.getByRole('button', { name: 'Cancel and upload a different image' }));
    expect(api.cancelAnalysis).toHaveBeenCalledTimes(1);
    expect(api.confirmMedications).not.toHaveBeenCalled();
    await act(async () => finish('cancelled'));
    expect(await screen.findByText(/The image analysis was cancelled/)).toBeInTheDocument();
  });

  it('reports a cancel from Cancel analysis that the server did not acknowledge, never as cancelled', async () => {
    vi.mocked(api.cancelAnalysis).mockRejectedValueOnce(new TypeError('Failed to fetch'));
    const user = await startImageAnalysis();
    await user.click(screen.getByRole('button', { name: 'Cancel analysis' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/did not confirm that the earlier image analysis was cancelled/);
    expect(screen.queryByText(/was cancelled; nothing from it was analysed/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry cancellation' })).toBeEnabled();
  });

  it('offers Cancel analysis again for the next image request, and clears the old status', async () => {
    const user = await startImageAnalysis();
    await user.click(screen.getByRole('button', { name: 'Cancel analysis' }));
    await screen.findByText(/The image analysis was cancelled/);
    vi.mocked(api.submitPrescriptionImage).mockResolvedValue({ request_id: 'req-8', stream_url: '/api/v1/stream/req-8', validation: {} });
    await user.click(screen.getByRole('button', { name: 'Analyze Medications' }));
    await waitFor(() => expect(api.connectStream).toHaveBeenCalledTimes(2));
    expect(screen.getByRole('button', { name: 'Cancel analysis' })).toBeEnabled();
    expect(screen.queryByText(/The image analysis was cancelled/)).not.toBeInTheDocument();
  });

  it('no longer offers a cancel once the medications are confirmed', async () => {
    vi.mocked(api.confirmMedications).mockResolvedValue({ status: 'success' } as never);
    const user = await reachReview();
    await user.click(screen.getByRole('button', { name: 'Confirm' }));
    await user.click(screen.getByRole('button', { name: /Confirm Medications & Analyze/ }));
    await waitFor(() => expect(api.confirmMedications).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole('button', { name: 'Cancel analysis' })).not.toBeInTheDocument();
  });
});
