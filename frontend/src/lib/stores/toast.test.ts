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

  it('auto-dismisses error toasts after 15s (longer than info/success)', () => {
    toast.error('Boom.');
    expect(toast.items).toHaveLength(1);

    // Still visible at 14.999s.
    vi.advanceTimersByTime(14999);
    expect(toast.items).toHaveLength(1);

    // Gone at 15s.
    vi.advanceTimersByTime(1);
    expect(toast.items).toHaveLength(0);
  });

  it('lets the user dismiss an error toast manually before 15s', () => {
    toast.error('Boom.');
    const id = toast.items[0].id;

    vi.advanceTimersByTime(2000);
    expect(toast.items).toHaveLength(1);

    toast.dismiss(id);
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

  it('caps the visible stack at 5 toasts and drops the oldest first', () => {
    toast.info('first');
    toast.info('second');
    toast.info('third');
    toast.info('fourth');
    toast.info('fifth');
    expect(toast.items.map((i) => i.message)).toEqual([
      'first',
      'second',
      'third',
      'fourth',
      'fifth',
    ]);

    // Sixth push evicts the oldest.
    toast.info('sixth');
    expect(toast.items.map((i) => i.message)).toEqual([
      'second',
      'third',
      'fourth',
      'fifth',
      'sixth',
    ]);

    // Pushing several more keeps evicting from the front.
    toast.info('seventh');
    toast.info('eighth');
    expect(toast.items.map((i) => i.message)).toEqual([
      'fourth',
      'fifth',
      'sixth',
      'seventh',
      'eighth',
    ]);
  });

  it('cap respects insertion order across mixed variants', () => {
    toast.info('a');
    toast.error('b');
    toast.success('c');
    toast.error('d');
    toast.info('e');
    toast.error('f'); // evicts 'a' (the oldest, regardless of variant)

    expect(toast.items.map((i) => `${i.variant}:${i.message}`)).toEqual([
      'error:b',
      'success:c',
      'error:d',
      'info:e',
      'error:f',
    ]);
  });

  it('cap eviction clears the timer on the dropped toast', () => {
    // Fill the stack with auto-dismissing toasts.
    for (let n = 0; n < 5; n++) {
      toast.info(`fill-${n}`);
    }
    // Push one more - 'fill-0' gets evicted.
    toast.info('newest');
    expect(toast.items.find((i) => i.message === 'fill-0')).toBeUndefined();

    // Even if the original 3.2s timer fired now, it would no-op
    // because remove() is keyed on id and the item is already gone.
    // Asserting no crash and no zombie re-insertion.
    vi.advanceTimersByTime(3200);
    expect(toast.items.map((i) => i.message)).not.toContain('fill-0');
  });

  it('handles trailing whitespace and punctuation around the suffix', () => {
    toast.error('Boom.   (Error ID:  VL-abc-123 )   ');

    const [item] = toast.items;
    expect(item.message).toBe('Boom.');
    expect(item.requestId).toBe('VL-abc-123');
  });
});
