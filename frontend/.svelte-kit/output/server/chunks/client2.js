import { r as refreshToken, a as auth, l as logout } from "./auth.svelte.js";
async function request(path, options = {}) {
  const headers = {
    ...options.headers || {}
  };
  if (auth.token) {
    headers["Authorization"] = `Bearer ${auth.token}`;
  }
  if (options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  let res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${auth.token}`;
      res = await fetch(path, { ...options, headers });
    } else {
      logout();
      throw new Error("Session expired");
    }
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return void 0;
  return res.json();
}
const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: "DELETE" })
};
export {
  api as a
};
