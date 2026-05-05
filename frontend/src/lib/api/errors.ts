/**
 * Frontend error model. Wraps the canonical error envelope returned by
 * the backend (documented in `backend/app/schemas/error.py`):
 *
 *     {
 *       "error": {
 *         "code": "validation_error",
 *         "message": "Request validation failed.",
 *         "request_id": "VL-fb16d4ac-...",
 *         "x_request_id": "abc-...",   (only when upstream provided one)
 *         "details": {...},            (only when structured payload exists)
 *         "timestamp": "2026-..."
 *       }
 *     }
 *
 * The `ApiError` class preserves all fields so consumers can render
 * inline per-field validation errors (`fieldErrors()`), branch on the
 * stable `code`, or copy the request ID from `requestId`.
 */

/** One entry from FastAPI's RequestValidationError list. */
export interface ApiValidationError {
  /** Path to the offending field, e.g. `["body", "email"]` or `["query", "page"]`. */
  loc: (string | number)[];
  /** Human-readable per-field message. */
  msg: string;
  /** Pydantic error type, e.g. `"value_error.email"`, `"missing"`, etc. */
  type: string;
}

/** Inner `error` body of the canonical envelope. */
export interface ApiErrorBody {
  code: string;
  message: string;
  request_id: string | null;
  x_request_id?: string;
  details?: { errors?: ApiValidationError[] } | Record<string, unknown> | unknown;
  timestamp?: string;
}

/** Outer envelope. */
export interface ApiErrorEnvelope {
  error?: ApiErrorBody;
  /** Legacy flat shape (predates the standardized error envelope). Reader still tolerates it. */
  detail?: string;
}

const FALLBACK_MESSAGE = 'Request failed. Please try again later.';

const TECHNICAL_MARKERS = [
  'traceback',
  'exception',
  'internal server error',
  'attributeerror',
  'valueerror',
];

async function parseJsonSafely(res: Response): Promise<ApiErrorEnvelope | null> {
  try {
    return (await res.json()) as ApiErrorEnvelope;
  } catch {
    return null;
  }
}

/**
 * Append the request ID to a user-facing error message so the user can
 * paste the whole string into a bug report and the support side can jump
 * straight to the matching log line.
 *
 * Format: `<message> (Error ID: VL-fb16d4ac-...)`. No-op when `requestId`
 * is null/undefined/empty.
 */
export function appendRequestId(message: string, requestId: string | null | undefined): string {
  if (!requestId) return message;
  return `${message} (Error ID: ${requestId})`;
}

/**
 * Reduce FastAPI's per-field validation errors to a flat
 * `{ fieldName: message }` map. The frontend forms key on the field
 * name (matching the request body key), not the full `loc` path.
 *
 * `loc` typically looks like `["body", "email"]` or
 * `["body", "addresses", 0, "city"]`. We strip a leading `"body"` /
 * `"query"` / `"path"` segment and join the rest with dots so nested
 * fields get a stable key like `"addresses.0.city"`.
 *
 * If two errors hit the same field, the first one wins (consistent
 * with FastAPI's own validation order).
 */
export function extractFieldErrors(err: ApiError): Record<string, string> {
  const out: Record<string, string> = {};
  const errors = err.validationErrors;
  if (!errors) return out;
  for (const v of errors) {
    const loc = [...v.loc];
    if (loc.length > 1 && (loc[0] === 'body' || loc[0] === 'query' || loc[0] === 'path')) {
      loc.shift();
    }
    const key = loc.join('.') || '_';
    if (!(key in out)) {
      out[key] = v.msg;
    }
  }
  return out;
}

/** Options accepted by the `ApiError` constructor. */
interface ApiErrorOptions {
  status: number;
  code: string;
  message: string;
  requestId?: string | null;
  xRequestId?: string;
  details?: unknown;
  timestamp?: string;
}

/**
 * Structured API error.
 *
 * Always thrown by the API client layer (`api.get/post/...`) when the
 * server returns a non-2xx response. Consumers can:
 *
 * - Display `e.toUserMessage()` in a toast (request ID auto-appended).
 * - Branch on `e.code` for stable, locale-independent error handling.
 * - Render `extractFieldErrors(e)` inline next to form inputs when
 *   `e.isValidationError()` is true.
 * - Copy `e.requestId` for bug reports.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly xRequestId?: string;
  readonly details?: unknown;
  readonly timestamp?: string;

  constructor(opts: ApiErrorOptions) {
    super(opts.message);
    this.name = 'ApiError';
    this.status = opts.status;
    this.code = opts.code;
    this.requestId = opts.requestId ?? null;
    this.xRequestId = opts.xRequestId;
    this.details = opts.details;
    this.timestamp = opts.timestamp;
  }

  /**
   * Build an `ApiError` from a non-OK `Response`. Tries the canonical
   * envelope first, falls back to legacy `{detail}`, then to scrubbed
   * response text, then to the supplied fallback string.
   *
   * Always returns an `ApiError`. Never throws (parsing failures are
   * absorbed into a generic-message error of the same status).
   */
  static async fromResponse(res: Response, fallback = FALLBACK_MESSAGE): Promise<ApiError> {
    const envelope = await parseJsonSafely(res.clone());
    const body = envelope?.error;

    // Server returned 5xx: use fallback message but still surface the
    // request ID if the envelope made it through.
    if (res.status >= 500) {
      return new ApiError({
        status: res.status,
        code: body?.code ?? 'internal_error',
        message: fallback,
        requestId: body?.request_id ?? null,
        xRequestId: body?.x_request_id,
        details: body?.details,
        timestamp: body?.timestamp,
      });
    }

    // Canonical envelope (current shape).
    if (body?.message) {
      return new ApiError({
        status: res.status,
        code: body.code ?? 'unknown_error',
        message: body.message,
        requestId: body.request_id ?? null,
        xRequestId: body.x_request_id,
        details: body.details,
        timestamp: body.timestamp,
      });
    }

    // Legacy flat shape.
    if (envelope?.detail) {
      return new ApiError({
        status: res.status,
        code: 'unknown_error',
        message: envelope.detail,
      });
    }

    // Plain text body. Scrub HTML / tracebacks / over-long noise.
    const text = await res.text().catch(() => '');
    const trimmed = text.trim();
    let message = fallback;
    if (trimmed && !trimmed.startsWith('<') && trimmed.length <= 200) {
      const normalized = trimmed.toLowerCase();
      if (!TECHNICAL_MARKERS.some((m) => normalized.includes(m))) {
        message = trimmed;
      }
    }

    return new ApiError({
      status: res.status,
      code: 'unknown_error',
      message,
    });
  }

  /**
   * User-facing string suitable for toast / inline display. Includes
   * the request ID suffix (`(Error ID: VL-...)`) when present.
   */
  toUserMessage(): string {
    return appendRequestId(this.message, this.requestId);
  }

  /** True iff this is a 422 with FastAPI per-field validation errors. */
  isValidationError(): boolean {
    return this.status === 422 && Array.isArray(this.validationErrors);
  }

  /** Convenience: extract the FastAPI per-field error array if present. */
  get validationErrors(): ApiValidationError[] | null {
    const d = this.details as { errors?: ApiValidationError[] } | undefined | null;
    if (d && Array.isArray(d.errors)) return d.errors;
    return null;
  }
}

/**
 * Coerce any thrown value into a user-facing string suitable for a
 * toast. Use this at the boundary between a `try { ... } catch (e)`
 * block and `toast.error(...)` so non-`ApiError` throws (TypeErrors,
 * network failures) still get a sane message.
 */
export function toToastMessage(e: unknown, fallback = FALLBACK_MESSAGE): string {
  if (e instanceof ApiError) return e.toUserMessage();
  if (e instanceof Error && e.message) return e.message;
  return fallback;
}

/**
 * Form-submit error router. Single call site at the bottom of every
 * form's `try { ... } catch (e) { ... }` block.
 *
 * - If the error is a 422 validation error AND `setFieldErrors` is
 *   provided: dispatch the per-field map inline; do NOT toast (the
 *   inline `<FieldError>` rows already surface what's wrong, and a
 *   redundant generic toast just adds noise).
 * - Otherwise: clear the previous field-error map (if any) and surface
 *   the message via `onToast`.
 *
 * Both callbacks are optional so callers that only want one behavior
 * (e.g. a form with no inline rendering yet) can omit the other.
 */
export function handleFormError(
  e: unknown,
  opts: {
    setFieldErrors?: (m: Record<string, string>) => void;
    onToast?: (msg: string) => void;
    fallback?: string;
  } = {},
): void {
  if (e instanceof ApiError && e.isValidationError()) {
    if (opts.setFieldErrors) {
      opts.setFieldErrors(extractFieldErrors(e));
      return;
    }
  }
  opts.setFieldErrors?.({});
  opts.onToast?.(toToastMessage(e, opts.fallback));
}

/**
 * Backward-compatible wrapper around the old `readPublicErrorMessage`
 * API. New code should call `ApiError.fromResponse(res)` directly and
 * decide between `toUserMessage()` (toast) and inline field rendering.
 *
 * @deprecated by the typed ApiError class. Use `ApiError.fromResponse` instead.
 */
export async function readPublicErrorMessage(
  res: Response,
  fallback = FALLBACK_MESSAGE,
): Promise<string> {
  const err = await ApiError.fromResponse(res, fallback);
  return err.toUserMessage();
}
