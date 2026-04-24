async function parseJsonSafely<T>(res: Response): Promise<T | null> {
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function readPublicErrorMessage(
  res: Response,
  fallback = 'Request failed. Please try again later.',
): Promise<string> {
  if (res.status >= 500) {
    return fallback;
  }

  const data = await parseJsonSafely<{ detail?: string }>(res.clone());
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
