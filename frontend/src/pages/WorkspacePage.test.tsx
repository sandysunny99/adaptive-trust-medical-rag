import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
    connectStream: vi.fn(),
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
