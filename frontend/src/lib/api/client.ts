import { auth, lastRefreshWasAuthFailure, logout, refreshToken } from '$lib/stores/auth.svelte';
import {
  APPLICATION_UNAVAILABLE_MESSAGE,
  appAvailability,
  fetchWithAvailability,
} from '$lib/stores/app-availability.svelte';
import { readPublicErrorMessage } from '$lib/api/errors';

// ── Rate-limit cooperation ──────────────────────────────────────────────
//
// When the edge proxy returns 429 with a Retry-After hint, we hold all
// in-flight and incoming /api/* calls in a single shared "cooling" promise
// until the server-suggested wait elapses, then retry once. Without this,
// every concurrent request would individually hammer the limit again and
// keep pushing the recovery time further out.
//
// We cap the cooperation window at MAX_RETRY_AFTER_MS so a misbehaving
// limiter can't freeze the UI for arbitrarily long; beyond that we surface
// the failure to the caller.

const MAX_RETRY_AFTER_MS = 8000;
const DEFAULT_RETRY_AFTER_MS = 3000;
let rateLimitCooling: Promise<void> | null = null;

function parseRetryAfter(raw: string | null): number {
  if (!raw) return DEFAULT_RETRY_AFTER_MS;
  const seconds = Number(raw);
  if (!Number.isFinite(seconds) || seconds <= 0) return DEFAULT_RETRY_AFTER_MS;
  return Math.min(seconds * 1000, MAX_RETRY_AFTER_MS);
}

function startCooling(ms: number): Promise<void> {
  if (rateLimitCooling) return rateLimitCooling;
  rateLimitCooling = new Promise<void>((resolve) => {
    setTimeout(() => {
      rateLimitCooling = null;
      resolve();
    }, ms);
  });
  return rateLimitCooling;
}

export async function authorizedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  // If the edge already told us "back off", queue here until cooling expires
  // before sending another request.
  if (rateLimitCooling) await rateLimitCooling;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (auth.token) {
    headers['Authorization'] = `Bearer ${auth.token}`;
  }

  let res = await fetchWithAvailability(path, { ...options, headers }, true);

  // 429 — server is rate-limiting us. Honor Retry-After (capped) once, then
  // retry the original request. Any other in-flight calls hitting 429 in
  // the same window will share this cooling promise.
  if (res.status === 429) {
    const waitMs = parseRetryAfter(res.headers.get('Retry-After'));
    await startCooling(waitMs);
    res = await fetchWithAvailability(path, { ...options, headers }, true);
  }

  if (res.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${auth.token}`;
      res = await fetchWithAvailability(path, { ...options, headers }, true);
    } else if (lastRefreshWasAuthFailure()) {
      // Refresh endpoint returned 401 → session is genuinely invalid.
      await logout(false);
      throw new Error('Session expired');
    } else {
      // Refresh failed for a transient reason (rate-limited, network blip,
      // backend 5xx). Don't clear the session — surface the original 401 so
      // the caller can retry. Next API call will trigger another refresh.
      throw new Error('Could not refresh session right now. Please retry in a moment.');
    }
  }

  return res;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }

  const res = await authorizedFetch(path, { ...options, headers });

  if (!res.ok) {
    if (appAvailability.unavailable) {
      throw new Error(APPLICATION_UNAVAILABLE_MESSAGE);
    }
    throw new Error(await readPublicErrorMessage(res));
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) =>
    request<T>(path, { method: 'DELETE' }),
};
