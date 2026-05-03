import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { toast } from './toast.svelte';

describe('toast store', () => {
  beforeEach(() => {
    // Drop any toasts left over from a previous test.
    for (const item of [...toast.items]) {
      toast.dismiss(item.id);
    }
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('strips the (Error ID: VL-...) suffix into a separate requestId field', () => {
    toast.error('Could not save client. (Error ID: VL-fb16d4ac-1234)');

    const [item] = toast.items;
    expect(item.message).toBe('Could not save client.');
    expect(item.requestId).toBe('VL-fb16d4ac-1234');
    expect(item.variant).toBe('error');
  });

  it('leaves the message untouched and requestId null when no suffix is present', () => {
    toast.error('Network unreachable.');

    const [item] = toast.items;
    expect(item.message).toBe('Network unreachable.');
    expect(item.requestId).toBeNull();
  });

  it('does NOT auto-dismiss error toasts (they persist until dismissed)', () => {
    toast.error('Persistent error.');
    expect(toast.items).toHaveLength(1);

    // Fast-forward an hour. Error toasts should still be there.
    vi.advanceTimersByTime(60 * 60 * 1000);
    expect(toast.items).toHaveLength(1);

    // Manual dismiss still works.
    toast.dismiss(toast.items[0].id);
    expect(toast.items).toHaveLength(0);
  });

  it('auto-dismisses success toasts after the default 3.2s', () => {
    toast.success('Saved!');
    expect(toast.items).toHaveLength(1);

    vi.advanceTimersByTime(3200);
    expect(toast.items).toHaveLength(0);
  });

  it('auto-dismisses info toasts after the default 3.2s', () => {
    toast.info('Heads up.');
    expect(toast.items).toHaveLength(1);

    vi.advanceTimersByTime(3200);
    expect(toast.items).toHaveLength(0);
  });

  it('honors an explicit duration override on error toasts', () => {
    toast.error('Brief flash.', 500);
    expect(toast.items).toHaveLength(1);

    vi.advanceTimersByTime(500);
    expect(toast.items).toHaveLength(0);
  });

  it('handles trailing whitespace and punctuation around the suffix', () => {
    toast.error('Boom.   (Error ID:  VL-abc-123 )   ');

    const [item] = toast.items;
    expect(item.message).toBe('Boom.');
    expect(item.requestId).toBe('VL-abc-123');
  });
});
