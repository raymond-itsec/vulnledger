interface User {
  user_id: string;
  username: string;
  full_name: string | null;
  role: string;
  linked_client_id: string | null;
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

export const auth = {
  get token() { return token; },
  get user() { return user; },
  get isAuthenticated() { return !!token; },
};

export async function login(username: string, password: string): Promise<void> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new Error(await readErrorMessage(res, 'Login failed. Please try again later.'));
  }
  const data = await parseJsonSafely<{ access_token?: string }>(res);
  if (!data?.access_token) {
    throw new Error('Login failed');
  }
  token = data.access_token;
  await fetchMe();
}

export async function fetchMe(): Promise<void> {
  if (!token) return;
  const res = await fetch('/api/users/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.ok) {
    user = await res.json();
  }
}

export async function refreshToken(): Promise<boolean> {
  try {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) return false;
    const data = await parseJsonSafely<{ access_token?: string }>(res);
    if (!data?.access_token) return false;
    token = data.access_token;
    await fetchMe();
    return true;
  } catch {
    return false;
  }
}

export async function bootstrapAuth(): Promise<void> {
  if (token) {
    await fetchMe();
    return;
  }

  const refreshed = await refreshToken();
  if (!refreshed) {
    token = null;
    user = null;
  }
}

export async function logout(): Promise<void> {
  try {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  } finally {
    token = null;
    user = null;
  }
}
