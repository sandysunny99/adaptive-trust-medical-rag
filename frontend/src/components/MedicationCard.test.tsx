import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MedicationCard } from './MedicationCard';
import type { MedicationInfo } from '../types';

// 2026-10-26 audit round 2: the backend sends SERVICE_UNAVAILABLE when RxNav cannot be reached and
// ERROR when the normalizer raised; neither had a card style, so the card failed to render.
const med = (status: string) => ({
  raw_text: 'warfarin', canonical_name: 'warfarin', rxcui: null, status, source: 'rxnav_unavailable',
}) as unknown as MedicationInfo;

describe('MedicationCard statuses', () => {
  it('says RxNorm was unreachable instead of "Not Found"', () => {
    render(<MedicationCard medication={med('SERVICE_UNAVAILABLE')} />);
    expect(screen.getByText('RxNorm unreachable')).toBeInTheDocument();
    expect(screen.queryByText('Not Found')).not.toBeInTheDocument();
  });

  it.each(['ERROR', 'SOMETHING_NEW'])('renders the %s status without failing', status => {
    render(<MedicationCard medication={med(status)} />);
    expect(screen.getByText('warfarin')).toBeInTheDocument();
  });
});

describe('MedicationCard ingredient link', () => {
  it('shows the RxNorm ingredient of a salt without replacing its identity', () => {
    render(<MedicationCard medication={{ ...med('MATCHED'), rxcui: '114194', canonical_name: 'warfarin sodium',
      rxnorm_ingredients: [{ rxcui: '11289', name: 'warfarin' }] } as MedicationInfo} />);
    expect(screen.getByText('114194')).toBeInTheDocument();
    expect(screen.getByText(/RxNorm ingredient: warfarin \(RxCUI 11289\)/)).toBeInTheDocument();
  });
});
