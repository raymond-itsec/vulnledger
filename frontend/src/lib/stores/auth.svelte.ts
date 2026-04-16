interface User {
  user_id: string;
  username: string;
  full_name: string | null;
  role: string;
  linked_client_id: string | null;
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
    const err = await res.json();
    throw new Error(err.detail || 'Login failed');
  }
  const data = await res.json();
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
    const data = await res.json();
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
