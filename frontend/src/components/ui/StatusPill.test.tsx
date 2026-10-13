import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { RiskTierPill, SecurityStatusPill, StatusPill } from './StatusPill';
import { Icons } from '../../ui/icons';

describe('StatusPill', () => {
  it('always renders its text, with the icon hidden from assistive tech', () => {
    const { container } = render(<StatusPill icon={Icons.pass} label="ALLOW" tone="success" />);
    expect(screen.getByText('ALLOW')).toBeVisible();
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
  });

  it.each(['ALLOW', 'FLAG', 'BLOCK'])('shows the backend status %s verbatim', status => {
    render(<SecurityStatusPill status={status} />);
    expect(screen.getByText(status)).toBeInTheDocument();
  });

  it('shows PENDING when there is no status and unknown values verbatim', () => {
    const { rerender } = render(<SecurityStatusPill status={null} />);
    expect(screen.getByText('PENDING')).toBeInTheDocument();
    rerender(<SecurityStatusPill status="QUARANTINE" />);
    expect(screen.getByText('QUARANTINE')).toBeInTheDocument();
  });

  it('shows the risk tier as returned', () => {
    render(<RiskTierPill tier="R0" />);
    expect(screen.getByText('R0')).toBeInTheDocument();
  });
});
