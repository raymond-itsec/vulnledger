import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/svelte';
import ErrorBoundary from './ErrorBoundary.svelte';
import Throws from './__fixtures__/Throws.svelte';
import Renders from './__fixtures__/Renders.svelte';

describe('ErrorBoundary', () => {
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // Svelte 5 logs caught boundary errors to console.error. Silence
    // the noise so the test output stays clean while still allowing
    // the tests to assert the boundary caught the throw.
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    errorSpy.mockRestore();
  });

  it('renders children when nothing throws', () => {
    const { getByText, queryByRole } = render(ErrorBoundary, {
      children: Renders as never,
    });
    expect(getByText('child rendered ok')).toBeInTheDocument();
    expect(queryByRole('alert')).not.toBeInTheDocument();
  });

  it('renders the fallback ErrorState when a child throws', () => {
    const { getByRole } = render(ErrorBoundary, {
      children: Throws as never,
      title: 'Widget broke',
      message: 'Try refreshing.',
    });
    const alert = getByRole('alert');
    expect(alert.textContent).toContain('Widget broke');
    expect(alert.textContent).toContain('Try refreshing.');
  });

  it('invokes the onError hook with the caught error', () => {
    const onError = vi.fn();
    render(ErrorBoundary, {
      children: Throws as never,
      onError,
    });
    expect(onError).toHaveBeenCalledOnce();
    const arg = onError.mock.calls[0][0];
    expect(arg).toBeInstanceOf(Error);
    expect((arg as Error).message).toBe('boom');
  });
});
