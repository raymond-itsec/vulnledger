export const APPLICATION_UNAVAILABLE_MESSAGE = 'Application is currently not available';

const POLL_INTERVAL_MS = 15000;
const LOGIN_PAGE_APP_AVAILABILITY_CACHE_KEY = 'findings.loginPageAppAvailabilityProbe';
const LOGIN_PAGE_OIDC_AVAILABILITY_CACHE_KEY = 'findings.loginPageOidcAvailabilityProbe';

let unavailable = $state(false);
let monitorStarted = false;
let intervalHandle: ReturnType<typeof setInterval> | null = null;
let pollPromise: Promise<void> | null = null;
let authToken = $state<string | null>(null);
let loginPageAppAvailabilityProbePromise: Promise<void> | null = null;
let loginPageAppAvailabilityChecked = $state(false);
let loginPageOidcAvailabilityProbePromise: Promise<boolean> | null = null;
let loginPageOidcAvailability = $state<boolean | null>(null);

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

function setUnavailable(next: boolean) {
  unavailable = next;
}

function handleOnline() {
  void appAvailability.checkNow(true);
}

function handleOffline() {
  setUnavailable(true);
}

function readCachedBoolean(key: string): boolean | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(key);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as { value?: boolean };
    return typeof parsed.value === 'boolean' ? parsed.value : null;
  } catch {
    return null;
  }
}

function writeCachedBoolean(key: string, value: boolean) {
  if (typeof window === 'undefined') return;
  window.sessionStorage.setItem(key, JSON.stringify({ value }));
}

export const appAvailability = {
  get unavailable() {
    return unavailable;
  },
  get message() {
    return APPLICATION_UNAVAILABLE_MESSAGE;
  },
  markUnavailable() {
    setUnavailable(true);
  },
  clear() {
    setUnavailable(false);
  },
  setAuthToken(token: string | null) {
    authToken = token;
    if (!token) {
      pollPromise = null;
    }
  },
  async checkLoginPageAppAvailabilityOnce(): Promise<void> {
    if (loginPageAppAvailabilityChecked) {
      return;
    }

    const cached = readCachedBoolean(LOGIN_PAGE_APP_AVAILABILITY_CACHE_KEY);
    if (cached !== null) {
      loginPageAppAvailabilityChecked = true;
      if (cached) {
        setUnavailable(false);
      }
      return;
    }

    if (typeof window !== 'undefined' && !navigator.onLine) {
      setUnavailable(true);
      loginPageAppAvailabilityChecked = true;
      return;
    }

    if (loginPageAppAvailabilityProbePromise) {
      await loginPageAppAvailabilityProbePromise;
      return;
    }

    loginPageAppAvailabilityProbePromise = (async () => {
      try {
        await fetchWithAvailability(
          `/api/health?ts=${Date.now()}`,
          {
            method: 'GET',
            cache: 'no-store',
          },
          true,
        );
      } catch {
        // fetchWithAvailability already updates the shared availability flag.
      } finally {
        if (!unavailable) {
          writeCachedBoolean(LOGIN_PAGE_APP_AVAILABILITY_CACHE_KEY, true);
        }
        loginPageAppAvailabilityChecked = true;
        loginPageAppAvailabilityProbePromise = null;
      }
    })();

    await loginPageAppAvailabilityProbePromise;
  },
  async checkLoginPageOidcAvailabilityOnce(): Promise<boolean> {
    if (loginPageOidcAvailability !== null) {
      return loginPageOidcAvailability;
    }

    const cached = readCachedBoolean(LOGIN_PAGE_OIDC_AVAILABILITY_CACHE_KEY);
    if (cached !== null) {
      loginPageOidcAvailability = cached;
      return loginPageOidcAvailability;
    }

    if (typeof window !== 'undefined' && !navigator.onLine) {
      loginPageOidcAvailability = false;
      return loginPageOidcAvailability;
    }

    if (loginPageOidcAvailabilityProbePromise) {
      return await loginPageOidcAvailabilityProbePromise;
    }

    loginPageOidcAvailabilityProbePromise = (async () => {
      let available = false;
      try {
        const res = await fetchWithAvailability(
          '/api/auth/oidc/login',
          { method: 'HEAD', redirect: 'manual', cache: 'no-store' },
          false,
        );
        available = res.status !== 404;
      } catch {
        available = false;
      } finally {
        loginPageOidcAvailability = available;
        writeCachedBoolean(LOGIN_PAGE_OIDC_AVAILABILITY_CACHE_KEY, available);
        loginPageOidcAvailabilityProbePromise = null;
      }
      return available;
    })();

    return await loginPageOidcAvailabilityProbePromise;
  },
  observeResponse(res: Response, clearOnSuccess = false): Response {
    if (res.status >= 500) {
      setUnavailable(true);
    } else if (clearOnSuccess) {
      setUnavailable(false);
    }
    return res;
  },
  handleFetchError(error: unknown): Error {
    if (isAbortError(error)) {
      return error instanceof Error ? error : new Error('Request aborted');
    }
    setUnavailable(true);
    return new Error(APPLICATION_UNAVAILABLE_MESSAGE);
  },
  async checkNow(clearOnSuccess = true): Promise<void> {
    if (typeof window === 'undefined') return;
    if (!navigator.onLine) {
      setUnavailable(true);
      return;
    }
    if (!authToken) {
      return;
    }
    if (pollPromise) {
      await pollPromise;
      return;
    }

    pollPromise = (async () => {
      try {
        await fetchWithAvailability(
          `/api/health?ts=${Date.now()}`,
          {
            cache: 'no-store',
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
          },
          clearOnSuccess,
        );
      } catch {
        // fetchWithAvailability already updates the shared availability state.
      } finally {
        pollPromise = null;
      }
    })();

    await pollPromise;
  },
  start() {
    if (typeof window === 'undefined' || monitorStarted) return;
    monitorStarted = true;
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    void this.checkNow();
    intervalHandle = setInterval(() => {
      void this.checkNow();
    }, POLL_INTERVAL_MS);
  },
  stop() {
    if (typeof window === 'undefined' || !monitorStarted) return;
    monitorStarted = false;
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
    if (intervalHandle) {
      clearInterval(intervalHandle);
      intervalHandle = null;
    }
  },
};

export async function fetchWithAvailability(
  input: RequestInfo | URL,
  init?: RequestInit,
  clearOnSuccess = false,
): Promise<Response> {
  try {
    const res = await fetch(input, init);
    return appAvailability.observeResponse(res, clearOnSuccess);
  } catch (error) {
    throw appAvailability.handleFetchError(error);
  }
}
