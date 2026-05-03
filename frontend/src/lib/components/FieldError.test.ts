import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import FieldError from './FieldError.svelte';

describe('FieldError', () => {
  it('renders the message when provided', () => {
    const { getByRole, getByText } = render(FieldError, { message: 'Email is required.' });
    expect(getByText('Email is required.')).toBeInTheDocument();
    expect(getByRole('alert')).toBeInTheDocument();
  });

  it('renders nothing when the message is empty/null/undefined', () => {
    const { container: emptyContainer } = render(FieldError, { message: '' });
    expect(emptyContainer.textContent?.trim()).toBe('');

    const { container: nullContainer } = render(FieldError, { message: null });
    expect(nullContainer.textContent?.trim()).toBe('');

    const { container: undefContainer } = render(FieldError, { message: undefined });
    expect(undefContainer.textContent?.trim()).toBe('');
  });

  it('uses the supplied id so aria-describedby can target it', () => {
    const { getByRole } = render(FieldError, { id: 'email-err', message: 'Required' });
    expect(getByRole('alert').id).toBe('email-err');
  });
});
