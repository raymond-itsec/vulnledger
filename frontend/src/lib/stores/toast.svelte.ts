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
 * Errors persist until the user dismisses them. They are rare, they
 * usually carry the request ID the user needs to copy into a bug
 * report, and auto-dismissing them after a few seconds means a slow
 * reader watches the message disappear before they can do anything
 * with it. Info / success toasts still auto-dismiss because they are
 * disposable confirmations.
 */
const DEFAULT_DURATION_MS: Record<ToastVariant, number | null> = {
  error: null,
  info: 3200,
  success: 3200,
};

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
