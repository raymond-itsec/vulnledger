import {
  APPLICATION_UNAVAILABLE_MESSAGE,
  appAvailability,
  fetchWithAvailability,
} from '$lib/stores/app-availability.svelte';
import { readPublicErrorMessage } from '$lib/api/errors';
import { taxonomy } from '$lib/stores/taxonomy.svelte';
import { toast } from '$lib/stores/toast.svelte';
import { LOGIN_PATH } from '$lib/config/routes';

interface User {
  user_id: string;
  username: string;
  full_name: string | null;
  company_name: string | null;
  email: string;
  role: string;
  linked_client_id: string | null;
  is_active: boolean;
}

async function parseJsonSafely<T>(res: Response): Promise<T | null> {
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

let token = $state<string | null>(null);
let user = $state<User | null>(null);
let refreshPromise: Promise<boolean> | null = null;
let bootstrapPromise: Promise<void> | null = null;
let bootstrapAttempted = false;
let staleSessionCleanupPromise: Promise<void> | null = null;
let lastRefreshFailurePermanent = false;
let lastRefreshRetryAfterMs = 0;

// Caps the cooperation window with a misbehaving / overly-aggressive rate
// limiter. We honor Retry-After up to this much; beyond it we surface the
// failure rather than freeze the UI for arbitrarily long.
const MAX_RETRY_AFTER_MS = 8000;
const DEFAULT_RETRY_AFTER_MS = 4000;

/** Parse an HTTP Retry-After header value (seconds) → ms, capped. */
function parseRetryAfter(raw: string | null): number {
  if (!raw) return DEFAULT_RETRY_AFTER_MS;
  const seconds = Number(raw);
  if (!Number.isFinite(seconds) || seconds <= 0) return DEFAULT_RETRY_AFTER_MS;
  return Math.min(seconds * 1000, MAX_RETRY_AFTER_MS);
}

export const auth = {
  get token() { return token; },
  get user() { return user; },
  get isAuthenticated() { return !!token; },
};

function clearBrowserStateOnLogout(): void {
  if (typeof window === 'undefined') return;

  try {
    window.sessionStorage.clear();
  } catch {
    // Best effort.
  }

  try {
    window.localStorage.clear();
  } catch {
    // Best effort.
  }

  // Also clear any in-browser HTTP caches scoped to this origin.
  if ('caches' in window) {
    void (async () => {
      try {
        const cacheKeys = await window.caches.keys();
        await Promise.all(cacheKeys.map((cacheKey) => window.caches.delete(cacheKey)));
      } catch {
        // Best effort.
      }
    })();
  }

  appAvailability.resetAfterLogout();
  taxonomy.reset();
}

function redirectToLoginShell(): void {
  if (typeof window === 'undefined') return;
  if (window.location.pathname === LOGIN_PATH) return;
  // Use a hard redirect after forced/expired logout so stale in-memory state
  // from the previous route cannot keep running in a broken state.
  window.location.replace(LOGIN_PATH);
}

async function clearStaleSession(): Promise<void> {
  if (staleSessionCleanupPromise) {
    await staleSessionCleanupPromise;
    return;
  }

  staleSessionCleanupPromise = (async () => {
    try {
      await fetchWithAvailability('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      }, true);
    } catch {
      // Best-effort cleanup only; local auth state is still cleared below.
    } finally {
      token = null;
      user = null;
      staleSessionCleanupPromise = null;
    }
  })();

  await staleSessionCleanupPromise;
}

export async function login(username: string, password: string): Promise<void> {
  const res = await fetchWithAvailability('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  }, true);
  if (!res.ok) {
    if (appAvailability.unavailable) {
      throw new Error(APPLICATION_UNAVAILABLE_MESSAGE);
    }
    throw new Error(await readPublicErrorMessage(res, 'Login failed. Please try again later.'));
  }
  const data = await parseJsonSafely<{ access_token?: string }>(res);
  if (!data?.access_token) {
    throw new Error('Login failed');
  }
  bootstrapAttempted = true;
  token = data.access_token;
  await fetchMe();
}

export async function fetchMe(): Promise<void> {
  if (!token) return;
  const res = await fetchWithAvailability('/api/users/me', {
    headers: { Authorization: `Bearer ${token}` },
  }, true);
  if (res.ok) {
    user = await res.json();
  }
}

/**
 * Returns whether the most recent refreshToken() failure was caused by a
 * 401 (i.e. truly invalid/expired session). Used by authorizedFetch to
 * decide whether to clear the session or just surface the error and let
 * the caller retry. Transient causes (429, 5xx, network) leave this false.
 */
export function lastRefreshWasAuthFailure(): boolean {
  return lastRefreshFailurePermanent;
}

export async function refreshToken(): Promise<boolean> {
  if (refreshPromise) {
    return await refreshPromise;
  }

  refreshPromise = (async () => {
    let permanentFailure = false;
    try {
      // Single attempt only — bootstrapAuth handles retry orchestration so
      // we don't double-tap the rate-limit budget. If we get 429 with a
      // Retry-After header, we honor it via the helper below.
      const res = await fetchWithAvailability('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      }, true);
      if (!res.ok) {
        if (res.status === 401) {
          permanentFailure = true;
          await clearStaleSession();
        } else if (res.status === 429) {
          // Surface server-suggested wait time (capped) so callers can
          // schedule a smarter retry without flooding the rate limiter.
          lastRefreshRetryAfterMs = parseRetryAfter(res.headers.get('Retry-After'));
        }
        return false;
      }
      const data = await parseJsonSafely<{ access_token?: string }>(res);
      if (!data?.access_token) return false;
      bootstrapAttempted = true;
      token = data.access_token;
      lastRefreshRetryAfterMs = 0;
      await fetchMe();
      return true;
    } catch {
      return false;
    } finally {
      lastRefreshFailurePermanent = permanentFailure;
      refreshPromise = null;
    }
  })();

  return await refreshPromise;
}

export async function bootstrapAuth(): Promise<void> {
  if (bootstrapPromise) {
    await bootstrapPromise;
    return;
  }

  if (token) {
    try {
      await fetchMe();
    } catch {
      // Keep the in-memory token state unchanged; layout-level availability handling
      // will route users to the login screen until the backend recovers.
    }
    return;
  }

  if (bootstrapAttempted) {
    token = null;
    user = null;
    return;
  }

  bootstrapPromise = (async () => {
    // First attempt.
    let refreshed = await refreshToken();

    // If the failure was transient (rate-limit, network, 5xx — anything
    // that is NOT a 401), wait the server-suggested Retry-After (capped at
    // MAX_RETRY_AFTER_MS) and try once more. We deliberately do not loop
    // — repeated retries would just keep eating the rate-limit budget and
    // pushing the recovery time further out. If a single, well-timed
    // retry can't recover, treat as bootstrap failure and let the layout
    // decide what to show (currently: redirect to /login).
    if (!refreshed && !lastRefreshFailurePermanent) {
      const wait = lastRefreshRetryAfterMs || DEFAULT_RETRY_AFTER_MS;
      await new Promise((resolve) => setTimeout(resolve, wait));
      refreshed = await refreshToken();
    }

    if (refreshed) {
      bootstrapAttempted = true;
      return;
    }

    // Either the refresh truly failed (401) or our single retry didn't help.
    // Mark bootstrapAttempted only on permanent (401) failures so a future
    // bootstrap can try again from scratch when transient.
    token = null;
    user = null;
    bootstrapAttempted = lastRefreshFailurePermanent;
  })();

  try {
    await bootstrapPromise;
  } finally {
    bootstrapPromise = null;
  }
}

export async function logout(notifyFailure = true): Promise<boolean> {
  let revokeSucceeded = false;
  try {
    const res = await fetchWithAvailability(
      '/api/auth/logout',
      { method: 'POST', credentials: 'include' },
      true,
    );
    if (!res.ok) {
      const detail = await readPublicErrorMessage(res, 'Could not revoke server session during logout.');
      if (notifyFailure) {
        toast.error(detail);
      }
    } else {
      revokeSucceeded = true;
    }
  } catch {
    if (notifyFailure) {
      toast.error('Could not reach backend to revoke session. Local logout completed.');
    }
  } finally {
    bootstrapAttempted = true;
    token = null;
    user = null;
    clearBrowserStateOnLogout();
    redirectToLoginShell();
  }
  return revokeSucceeded;
}
