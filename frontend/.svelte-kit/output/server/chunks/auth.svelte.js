import "clsx";
let token = null;
let user = null;
const auth = {
  get token() {
    return token;
  },
  get user() {
    return user;
  },
  get isAuthenticated() {
    return !!token;
  }
};
async function fetchMe() {
  if (!token) return;
  const res = await fetch("/api/users/me", { headers: { Authorization: `Bearer ${token}` } });
  if (res.ok) {
    user = await res.json();
  }
}
async function refreshToken() {
  try {
    const res = await fetch("/api/auth/refresh", { method: "POST", credentials: "include" });
    if (!res.ok) return false;
    const data = await res.json();
    token = data.access_token;
    await fetchMe();
    return true;
  } catch {
    return false;
  }
}
function logout() {
  fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  token = null;
  user = null;
}
export {
  auth as a,
  logout as l,
  refreshToken as r
};
