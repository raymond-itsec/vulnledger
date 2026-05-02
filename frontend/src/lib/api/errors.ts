/**
 * Error envelope returned by every API error response. Documented in
 * `backend/app/schemas/error.py`.
 */
interface ErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    request_id?: string | null;
    x_request_id?: string;
    details?: unknown;
    timestamp?: string;
  };
  // Legacy flat shape (pre Phase 1.6) - kept here so the reader does
  // not break if a stale backend deploys against a fresh frontend.
  detail?: string;
}

async function parseJsonSafely<T>(res: Response): Promise<T | null> {
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Append the request ID to a user-facing error message so the user can
 * paste the whole string into a bug report and get straight to the
 * matching log line.
 *
 * Format: `<message> (Error ID: VL-fb16d4ac-...)`
 */
function appendRequestId(message: string, requestId: string | null | undefined): string {
  if (!requestId) return message;
  return `${message} (Error ID: ${requestId})`;
}

/**
 * Extract a user-facing error message from a failed Response. Reads the
 * canonical `{error: {message, request_id, ...}}` envelope, falls back
 * to the legacy flat `{detail: ...}` shape, and finally to a
 * scrubbed-text or fallback string.
 *
 * The returned string includes the `request_id` when present so that
 * any toast or inline error display surfaces it automatically.
 */
export async function readPublicErrorMessage(
  res: Response,
  fallback = 'Request failed. Please try again later.',
): Promise<string> {
  if (res.status >= 500) {
    // Try to surface the request ID even on 500s so users can report.
    const data = await parseJsonSafely<ErrorEnvelope>(res.clone());
    return appendRequestId(fallback, data?.error?.request_id);
  }

  const data = await parseJsonSafely<ErrorEnvelope>(res.clone());

  // Canonical envelope (Phase 1.6+).
  if (data?.error?.message) {
    return appendRequestId(data.error.message, data.error.request_id);
  }

  // Legacy flat shape.
  if (data?.detail) {
    return data.detail;
  }

  const text = await res.text().catch(() => '');
  const trimmed = text.trim();
  if (!trimmed) return fallback;
  if (trimmed.startsWith('<')) return fallback;

  const technicalMarkers = ['traceback', 'exception', 'internal server error', 'attributeerror', 'valueerror'];
  const normalized = trimmed.toLowerCase();
  if (technicalMarkers.some((marker) => normalized.includes(marker))) {
    return fallback;
  }

  return trimmed.length > 200 ? fallback : trimmed;
}
