type ToastVariant = 'error' | 'info' | 'success';

interface ToastItem {
  id: number;
  message: string;
  variant: ToastVariant;
  /**
   * Request ID stripped off the end of the message when present. Set by
   * `parseRequestId` so the viewport can render it as a separate
   * copy-able pill instead of forcing the user to select a substring of
   * the toast text.
   */
  requestId: string | null;
}

let nextId = 1;
let items = $state<ToastItem[]>([]);
const timers = new Map<number, ReturnType<typeof setTimeout>>();

/**
 * Default visible-time per variant.
 *
 * Errors stay on screen longer (15s) than info/success (3.2s) because
 * they usually carry the request ID the user needs to copy into a bug
 * report, and a too-short window makes that impossible. They are not
 * permanent though - leaving stale red toasts on screen forever
 * trains users to ignore them. The `×` button still dismisses
 * manually at any time.
 */
const DEFAULT_DURATION_MS: Record<ToastVariant, number | null> = {
  error: 15000,
  info: 3200,
  success: 3200,
};

/**
 * Maximum number of toasts visible at once across all variants.
 * Pushing past this dismisses the oldest one(s) first so the screen
 * does not stack up an unreadable column. Five fits comfortably above
 * typical browser chrome heights without overflowing the viewport.
 */
const MAX_OPEN_TOASTS = 5;

/**
 * Pull a trailing `(Error ID: VL-...)` suffix off the message so the
 * viewport can render it separately. Matches both uppercase `VL-` and
 * any future prefix the request-ID middleware might use, and is
 * tolerant of trailing punctuation or whitespace.
 *
 * Returns `{ message, requestId }` where `message` is the original
 * text with the suffix removed. If no suffix is present, `requestId`
 * is null and `message` is unchanged.
 */
function parseRequestId(raw: string): { message: string; requestId: string | null } {
  const match = raw.match(/^(.*?)\s*\(Error ID:\s*([^)]+?)\)\s*$/);
  if (!match) return { message: raw, requestId: null };
  return { message: match[1].trim(), requestId: match[2].trim() };
}

function remove(id: number) {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
  items = items.filter((item) => item.id !== id);
}

function push(rawMessage: string, variant: ToastVariant, duration?: number) {
  // Cap the visible stack. Items are appended in chronological order
  // (nextId is monotonic), so items[0] is always the oldest. Drop
  // oldest ones first until we have room for the incoming toast.
  while (items.length >= MAX_OPEN_TOASTS) {
    remove(items[0].id);
  }

  const id = nextId++;
  const { message, requestId } = parseRequestId(rawMessage);
  items = [...items, { id, message, variant, requestId }];
  const effectiveDuration = duration ?? DEFAULT_DURATION_MS[variant];
  if (effectiveDuration !== null) {
    const timer = setTimeout(() => remove(id), effectiveDuration);
    timers.set(id, timer);
  }
  return id;
}

export const toast = {
  get items() {
    return items;
  },
  success(message: string, duration?: number) {
    return push(message, 'success', duration);
  },
  error(message: string, duration?: number) {
    return push(message, 'error', duration);
  },
  info(message: string, duration?: number) {
    return push(message, 'info', duration);
  },
  dismiss(id: number) {
    remove(id);
  },
};
