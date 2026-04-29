export function sanitizeUrl(url: string): string | null {
  const value = url.trim();
  if (/^(https?:\/\/|mailto:|\/|#)/i.test(value)) {
    return value;
  }
  return null;
}
