import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { MedicationConfirmationPanel } from './MedicationConfirmationPanel';
import type { MedicationCandidate } from '../types';

describe('MedicationConfirmationPanel', () => {
  const mockCandidates: MedicationCandidate[] = [
    {
      id: 'ocr-1',
      raw_text: 'Warfarin 5mg',
      normalized_text: 'warfarin',
      confidence: 'HIGH',
      status: 'DETECTED',
      source: 'VISION'
    },
    {
      id: 'ocr-2',
      raw_text: 'Asp..n',
      normalized_text: 'aspirin',
      confidence: 'LOW',
      status: 'UNCERTAIN',
      source: 'VISION',
      warnings: ['Low confidence']
    }
  ];

  it('TEST 1: Candidate list renders', () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    expect(screen.getByText('warfarin')).toBeInTheDocument();
    expect(screen.getByText('aspirin')).toBeInTheDocument();
  });

  it('TEST 2: Confidence is displayed', () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    expect(screen.getByText('Extraction confidence: HIGH')).toBeInTheDocument();
    expect(screen.getByText('Extraction confidence: LOW')).toBeInTheDocument();
  });

  it('TEST 3: High-confidence candidate can be confirmed', async () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    const buttons = screen.getAllByRole('button', { name: /Confirm/i });
    
    // First confirm button is for warfarin
    fireEvent.click(buttons[0]);
    // It should now say Status: CONFIRMED
    const statuses = screen.getAllByText(/Status: CONFIRMED/i);
    expect(statuses.length).toBeGreaterThan(0);
  });

  it('TEST 4: Low-confidence candidate requires review', () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    expect(screen.getByText('Status: UNCERTAIN')).toBeInTheDocument();
    expect(screen.getByText(/Please review and confirm all uncertain medications/i)).toBeInTheDocument();
  });

  it('TEST 5: Candidate can be edited', async () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    const editButtons = screen.getAllByTitle('Edit');
    fireEvent.click(editButtons[0]);
    
    const input = screen.getByDisplayValue('warfarin');
    await userEvent.clear(input);
    await userEvent.type(input, 'warfarin sodium');
    
    // Save
    const saveButton = input.nextSibling as HTMLButtonElement;
    fireEvent.click(saveButton);
    
    expect(screen.getByText('warfarin sodium')).toBeInTheDocument();
    expect(screen.getByText('Status: EDITED')).toBeInTheDocument();
  });

  it('TEST 6: Candidate can be removed', () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    const removeButtons = screen.getAllByTitle('Remove');
    fireEvent.click(removeButtons[0]); // Remove warfarin
    
    // It shouldn't be in the active candidates list anymore (it gets rejected/hidden)
    expect(screen.queryByText('Status: DETECTED')).not.toBeInTheDocument();
  });

  it('TEST 7: User can manually add medication', async () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    fireEvent.click(screen.getByText(/Add medication manually/i));
    
    const input = screen.getByPlaceholderText(/Enter medication name/i);
    await userEvent.type(input, 'paracetamol');
    
    fireEvent.click(screen.getByRole('button', { name: 'Add' }));
    
    expect(screen.getByText('paracetamol')).toBeInTheDocument();
    expect(screen.getByText('User Added')).toBeInTheDocument();
  });

  it('TEST 8: Unresolved candidate disables final confirmation', () => {
    render(<MedicationConfirmationPanel candidates={mockCandidates} onConfirm={vi.fn()} />);
    const submitBtn = screen.getByRole('button', { name: /Confirm Medications & Analyze/i });
    expect(submitBtn).toBeDisabled();
  });

  it('TEST 9: No medications disables final confirmation', () => {
    render(<MedicationConfirmationPanel candidates={[]} onConfirm={vi.fn()} />);
    const submitBtn = screen.getByRole('button', { name: /Confirm Medications & Analyze/i });
    expect(submitBtn).toBeDisabled();
  });

  it('TEST 10: Confirmation creates correct resolved medication list', () => {
    const onConfirmMock = vi.fn();
    render(<MedicationConfirmationPanel candidates={[mockCandidates[0]]} onConfirm={onConfirmMock} />);
    
    const confirmButtons = screen.getAllByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmButtons[0]);
    
    const submitBtn = screen.getByRole('button', { name: /Confirm Medications & Analyze/i });
    expect(submitBtn).not.toBeDisabled();
    
    fireEvent.click(submitBtn);
    expect(onConfirmMock).toHaveBeenCalledWith(['warfarin']);
  });
});
