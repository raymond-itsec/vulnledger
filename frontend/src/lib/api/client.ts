import { auth, lastRefreshWasAuthFailure, logout, refreshToken } from '$lib/stores/auth.svelte';
import {
  APPLICATION_UNAVAILABLE_MESSAGE,
  appAvailability,
  fetchWithAvailability,
} from '$lib/stores/app-availability.svelte';
import { readPublicErrorMessage } from '$lib/api/errors';
import { awaitRateLimitCooling, parseRetryAfter, startCooling } from '$lib/api/rate-limit';

// Maximum 429 retries per request before giving up. With Retry-After-aware
// cooling each retry waits for the budget to free up; 3 attempts spans up
// to ~24s of cool-down which covers the worst-case sustained-burst case
// without freezing the UI indefinitely.
const MAX_429_RETRIES = 3;

export async function authorizedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (auth.token) {
    headers['Authorization'] = `Bearer ${auth.token}`;
  }

  let res: Response;
  let attempt = 0;
  while (true) {
    // If the edge already told us "back off", queue here until cooling
    // expires before sending another request. Shared with auth.svelte.ts
    // so refreshes also cooperate with the same cool-down window.
    await awaitRateLimitCooling();

    res = await fetchWithAvailability(path, { ...options, headers }, true);

    // 429 — keep cooling and retrying up to MAX_429_RETRIES. Concurrent
    // requests share the same cool-down promise, so a single Retry-After
    // value paces the whole burst rather than each request scheduling
    // its own retry.
    if (res.status === 429 && attempt < MAX_429_RETRIES) {
      const waitMs = parseRetryAfter(res.headers.get('Retry-After'));
      await startCooling(waitMs);
      attempt++;
      continue;
    }

    break;
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
