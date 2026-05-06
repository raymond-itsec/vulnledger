// Shared rate-limit cooperation state for all /api/* fetches.
//
// When the edge proxy returns 429 with a Retry-After hint, ALL outgoing
// API requests (whether they go through authorizedFetch in client.ts or
// directly through fetchWithAvailability in auth.svelte.ts) wait on the
// same cooling promise before firing. Without this single source of
// truth, concurrent requests would each independently hit the limiter
// during recovery and keep the cool-down extended indefinitely.
//
// Cap is conservative: we cooperate up to MAX_RETRY_AFTER_MS, beyond
// which we surface failure rather than freeze the UI for arbitrarily
// long.

export const MAX_RETRY_AFTER_MS = 8000;
export const DEFAULT_RETRY_AFTER_MS = 3000;

let coolingPromise: Promise<void> | null = null;

/**
 * Returns the current cooling promise, or a resolved promise if no
 * cooling is in progress. Callers should `await` this before sending
 * a new /api/* request to cooperate with an active rate-limit.
 */
export function awaitRateLimitCooling(): Promise<void> {
  return coolingPromise ?? Promise.resolve();
}

/**
 * Begin a cooling period of `ms` milliseconds (or join an existing
 * one). Concurrent calls share the same promise — only the first
 * caller actually arms the timer.
 */
export function startCooling(ms: number): Promise<void> {
  if (coolingPromise) return coolingPromise;
  const promise = new Promise<void>((resolve) => {
    setTimeout(() => {
      if (coolingPromise === promise) coolingPromise = null;
      resolve();
    }, ms);
  });
  coolingPromise = promise;
  return promise;
}

/**
 * Parse an HTTP `Retry-After` header value (in seconds) to milliseconds.
 * Falls back to DEFAULT_RETRY_AFTER_MS if missing or unparseable.
 * Always capped at MAX_RETRY_AFTER_MS.
 */
export function parseRetryAfter(raw: string | null): number {
  if (!raw) return DEFAULT_RETRY_AFTER_MS;
  const seconds = Number(raw);
  if (!Number.isFinite(seconds) || seconds <= 0) return DEFAULT_RETRY_AFTER_MS;
  return Math.min(seconds * 1000, MAX_RETRY_AFTER_MS);
}
