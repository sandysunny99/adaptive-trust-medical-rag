import { describe, it, expect, vi } from 'vitest';
import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { Disclosure } from './Disclosure';
import { SegmentedControl } from './SegmentedControl';

describe('Disclosure', () => {
  it('is closed by default and toggles aria-expanded and the panel', async () => {
    render(<Disclosure title="Advanced settings"><p>Panel body</p></Disclosure>);

    const button = screen.getByRole('button', { name: /Advanced settings/ });
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('Panel body')).not.toBeVisible();

    await userEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Panel body')).toBeVisible();

    await userEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('Panel body')).not.toBeVisible();
  });

  it('links the button to its panel with aria-controls', () => {
    render(<Disclosure title="Patient context" defaultOpen><p>Body</p></Disclosure>);
    const button = screen.getByRole('button', { name: /Patient context/ });
    const panelId = button.getAttribute('aria-controls');
    expect(panelId).toBeTruthy();
    expect(document.getElementById(panelId!)).toContainElement(screen.getByText('Body'));
  });
});

type Mode = 'image' | 'drugs';

function Harness({ onChange }: { onChange?: (v: Mode) => void }) {
  const [value, setValue] = useState<Mode>('drugs');
  return (
    <SegmentedControl<Mode>
      ariaLabel="Input method"
      value={value}
      onChange={v => { setValue(v); onChange?.(v); }}
      options={[
        { value: 'image', label: 'Upload Prescription' },
        { value: 'drugs', label: 'Enter Drug Names' },
      ]}
    />
  );
}

describe('SegmentedControl', () => {
  it('marks the selected segment and keeps only it in the tab order', () => {
    render(<Harness />);
    const drugs = screen.getByRole('tab', { name: 'Enter Drug Names' });
    const image = screen.getByRole('tab', { name: 'Upload Prescription' });
    expect(drugs).toHaveAttribute('aria-selected', 'true');
    expect(drugs).toHaveAttribute('tabindex', '0');
    expect(image).toHaveAttribute('aria-selected', 'false');
    expect(image).toHaveAttribute('tabindex', '-1');
  });

  it('moves selection and focus with arrow keys, wrapping, and Home/End', async () => {
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);
    const drugs = screen.getByRole('tab', { name: 'Enter Drug Names' });
    const image = screen.getByRole('tab', { name: 'Upload Prescription' });

    drugs.focus();
    await userEvent.keyboard('{ArrowLeft}');
    expect(image).toHaveAttribute('aria-selected', 'true');
    expect(image).toHaveFocus();
    expect(onChange).toHaveBeenLastCalledWith('image');

    await userEvent.keyboard('{ArrowLeft}');
    expect(drugs).toHaveAttribute('aria-selected', 'true');
    expect(drugs).toHaveFocus();

    await userEvent.keyboard('{ArrowRight}');
    expect(image).toHaveAttribute('aria-selected', 'true');

    await userEvent.keyboard('{End}');
    expect(drugs).toHaveAttribute('aria-selected', 'true');

    await userEvent.keyboard('{Home}');
    expect(image).toHaveAttribute('aria-selected', 'true');
    expect(image).toHaveFocus();
  });
});
