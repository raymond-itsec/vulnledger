import {
  APPLICATION_UNAVAILABLE_MESSAGE,
  appAvailability,
  fetchWithAvailability,
} from '$lib/stores/app-availability.svelte';
import { toast } from '$lib/stores/toast.svelte';

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
    return await res.json() as T;
  } catch {
    return null;
  }
}

async function readErrorMessage(res: Response, fallback: string): Promise<string> {
  if (res.status >= 500) return fallback;

  const data = await parseJsonSafely<{ detail?: string }>(res.clone());
  if (data?.detail) return data.detail;

  const text = await res.text().catch(() => '');
  const trimmed = text.trim();
  if (!trimmed) return fallback;

  // Avoid surfacing HTML error documents or giant stack traces verbatim in the UI.
  if (trimmed.startsWith('<')) return fallback;
  const technicalMarkers = ['traceback', 'exception', 'internal server error', 'attributeerror', 'valueerror'];
  const normalized = trimmed.toLowerCase();
  if (technicalMarkers.some((marker) => normalized.includes(marker))) {
    return fallback;
  }

  return trimmed.length > 200 ? fallback : trimmed;
}

let token = $state<string | null>(null);
let user = $state<User | null>(null);
let refreshPromise: Promise<boolean> | null = null;
let bootstrapPromise: Promise<void> | null = null;
let bootstrapAttempted = false;
let staleSessionCleanupPromise: Promise<void> | null = null;
let lastRefreshFailurePermanent = false;

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
  void import('$lib/stores/taxonomy.svelte')
    .then((module) => module.taxonomy.reset())
    .catch(() => {
      // Best effort.
    });
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
    throw new Error(await readErrorMessage(res, 'Login failed. Please try again later.'));
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

export async function refreshToken(): Promise<boolean> {
  if (refreshPromise) {
    return await refreshPromise;
  }

  refreshPromise = (async () => {
    let permanentFailure = false;
    try {
      const res = await fetchWithAvailability('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      }, true);
      if (!res.ok) {
        if (res.status === 401) {
          permanentFailure = true;
          await clearStaleSession();
        }
        return false;
      }
      const data = await parseJsonSafely<{ access_token?: string }>(res);
      if (!data?.access_token) return false;
      bootstrapAttempted = true;
      token = data.access_token;
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
    const refreshed = await refreshToken();
    if (refreshed) {
      bootstrapAttempted = true;
      return;
    }

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
      const detail = await readErrorMessage(res, 'Could not revoke server session during logout.');
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
  }
  return revokeSucceeded;
}
