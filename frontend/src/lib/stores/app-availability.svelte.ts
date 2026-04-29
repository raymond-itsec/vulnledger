export const APPLICATION_UNAVAILABLE_MESSAGE = 'Application is currently not available';

const POLL_INTERVAL_MS = 15000;
const MAX_IDLE_HEALTH_CHECKS = 2;
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
let idleHealthChecks = 0;

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

async function logHealthCheckResult(context: string, response: Response): Promise<void> {
  const logBase = `[health-check:${context}]`;
  const meta = {
    timestamp: new Date().toISOString(),
    httpStatus: response.status,
  };

  try {
    const body = await response.clone().json();
    if (response.ok) {
      console.info(logBase, { ...meta, body });
    } else {
      console.warn(logBase, { ...meta, body });
    }
    return;
  } catch {
    // Fall back to status-only logs when response body isn't JSON.
  }

  if (response.ok) {
    console.info(logBase, meta);
  } else {
    console.warn(logBase, meta);
  }
}

function stopPollingLoop() {
  if (!intervalHandle) return;
  clearInterval(intervalHandle);
  intervalHandle = null;
}

function startPollingLoop() {
  if (intervalHandle) return;
  intervalHandle = setInterval(() => {
    void appAvailability.checkNow();
  }, POLL_INTERVAL_MS);
}

function markUserActivity() {
  idleHealthChecks = 0;
  if (!monitorStarted || typeof window === 'undefined') return;
  if (!intervalHandle) {
    void appAvailability.checkNow();
    startPollingLoop();
  }
}

function handleUserActivity() {
  markUserActivity();
}

function handleVisibilityChange() {
  if (typeof document === 'undefined') return;
  if (document.visibilityState === 'visible') {
    markUserActivity();
  }
}

function readCachedBoolean(key: string): boolean | null {
  if (typeof window === 'undefined') return null;
  let raw: string | null = null;
  try {
    raw = window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
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
  try {
    window.sessionStorage.setItem(key, JSON.stringify({ value }));
  } catch {
    // Best effort.
  }
}

function requestPathname(input: RequestInfo | URL): string {
  if (input instanceof URL) return input.pathname;

  const raw = input instanceof Request ? input.url : String(input);
  const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
  try {
    return new URL(raw, base).pathname;
  } catch {
    return raw.split('?')[0]?.split('#')[0] || raw;
  }
}

function isHealthProbeSuccess(
  input: RequestInfo | URL,
  res: Response,
  clearOnSuccess: boolean,
): boolean {
  if (!clearOnSuccess) return false;
  if (res.status < 200 || res.status >= 300) return false;
  return requestPathname(input) === '/api/health';
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
  resetAfterLogout() {
    this.stop();
    setUnavailable(false);
    authToken = null;
    pollPromise = null;
    idleHealthChecks = 0;
    loginPageAppAvailabilityProbePromise = null;
    loginPageAppAvailabilityChecked = false;
    loginPageOidcAvailabilityProbePromise = null;
    loginPageOidcAvailability = null;
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
        const response = await fetchWithAvailability(
          `/api/health?ts=${Date.now()}`,
          {
            method: 'GET',
            cache: 'no-store',
          },
          true,
        );
        await logHealthCheckResult('login-probe', response);
        try {
          const body = await response.clone().json() as { features?: { oidc_enabled?: boolean } };
          loginPageOidcAvailability = body.features?.oidc_enabled === true;
          writeCachedBoolean(LOGIN_PAGE_OIDC_AVAILABILITY_CACHE_KEY, loginPageOidcAvailability);
        } catch {
          loginPageOidcAvailability = false;
        }
      } catch {
        // fetchWithAvailability already updates the shared availability flag.
        loginPageOidcAvailability = false;
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

    await this.checkLoginPageAppAvailabilityOnce();
    return loginPageOidcAvailability ?? false;
  },
  observeResponse(
    input: RequestInfo | URL,
    res: Response,
    clearOnSuccess = false,
  ): Response {
    if (res.status >= 500) {
      setUnavailable(true);
    } else if (isHealthProbeSuccess(input, res, clearOnSuccess)) {
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
    if (pollPromise) {
      await pollPromise;
      return;
    }

    pollPromise = (async () => {
      try {
        const requestInit: RequestInit = {
          cache: 'no-store',
        };
        if (authToken) {
          requestInit.headers = {
            Authorization: `Bearer ${authToken}`,
          };
        }

        const response = await fetchWithAvailability(
          `/api/health?ts=${Date.now()}`,
          requestInit,
          clearOnSuccess,
        );
        await logHealthCheckResult('poll', response);
      } catch {
        // fetchWithAvailability already updates the shared availability state.
      } finally {
        if (monitorStarted) {
          idleHealthChecks += 1;
          if (idleHealthChecks >= MAX_IDLE_HEALTH_CHECKS) {
            stopPollingLoop();
          }
        }
        pollPromise = null;
      }
    })();

    await pollPromise;
  },
  start() {
    if (typeof window === 'undefined' || monitorStarted) return;
    monitorStarted = true;
    idleHealthChecks = 0;
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('pointerdown', handleUserActivity, { passive: true });
    window.addEventListener('keydown', handleUserActivity);
    window.addEventListener('wheel', handleUserActivity, { passive: true });
    window.addEventListener('touchstart', handleUserActivity, { passive: true });
    document.addEventListener('visibilitychange', handleVisibilityChange);
    void this.checkNow();
    startPollingLoop();
  },
  stop() {
    if (typeof window === 'undefined' || !monitorStarted) return;
    monitorStarted = false;
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
    window.removeEventListener('pointerdown', handleUserActivity);
    window.removeEventListener('keydown', handleUserActivity);
    window.removeEventListener('wheel', handleUserActivity);
    window.removeEventListener('touchstart', handleUserActivity);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    stopPollingLoop();
  },
};

export async function fetchWithAvailability(
  input: RequestInfo | URL,
  init?: RequestInit,
  clearOnSuccess = false,
): Promise<Response> {
  try {
    const res = await fetch(input, init);
    return appAvailability.observeResponse(input, res, clearOnSuccess);
  } catch (error) {
    throw appAvailability.handleFetchError(error);
  }
}
