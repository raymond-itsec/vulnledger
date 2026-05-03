import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import ErrorState from './ErrorState.svelte';

describe('ErrorState', () => {
  it('renders the default title and no message/request id when none provided', () => {
    const { getByText, queryByText } = render(ErrorState);
    expect(getByText('Something went wrong')).toBeInTheDocument();
    expect(queryByText('Error ID:')).not.toBeInTheDocument();
  });

  it('renders the supplied message and request id', () => {
    const { getByText } = render(ErrorState, {
      title: 'Could not load findings',
      message: 'The list endpoint returned 500.',
      requestId: 'VL-abc-123',
    });
    expect(getByText('Could not load findings')).toBeInTheDocument();
    expect(getByText('The list endpoint returned 500.')).toBeInTheDocument();
    expect(getByText('VL-abc-123')).toBeInTheDocument();
  });

  it('shows the retry button only when onRetry is provided', () => {
    const { queryByRole } = render(ErrorState, { message: 'Boom' });
    expect(queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument();

    const onRetry = vi.fn();
    const { getByRole } = render(ErrorState, { message: 'Boom', onRetry });
    expect(getByRole('button', { name: 'Try again' })).toBeInTheDocument();
  });

  it('calls onRetry when the retry button is clicked', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    const { getByRole } = render(ErrorState, { message: 'Boom', onRetry });

    await user.click(getByRole('button', { name: 'Try again' }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('copies the request id to the clipboard when the copy button is clicked', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    // jsdom's navigator.clipboard is a read-only getter; defineProperty
    // bypasses that so the component's `navigator.clipboard.writeText`
    // call lands on our spy.
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });

    // Use fireEvent rather than userEvent here: user-event v14 installs
    // its own clipboard interceptor in setup(), which bypasses the
    // navigator.clipboard.writeText spy we want to assert on.
    const { getByRole } = render(ErrorState, { requestId: 'VL-zzz' });

    await fireEvent.click(getByRole('button', { name: 'Copy error ID' }));
    expect(writeText).toHaveBeenCalledWith('VL-zzz');
  });
});
