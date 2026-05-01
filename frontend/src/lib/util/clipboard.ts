/**
 * Copy a string to the user's clipboard.
 *
 * Prefers the modern `navigator.clipboard.writeText` API. Falls back to
 * the legacy `document.execCommand('copy')` path when the modern API is
 * unavailable, which happens on plain-HTTP non-localhost origins (e.g.
 * the dev box at http://192.168.178.250:8880).
 *
 * Returns true on success, false on any failure. Callers should surface
 * a toast / error message based on the return value.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (typeof window === 'undefined') return false;

  // Modern path. Requires secure context (HTTPS or localhost) on most
  // browsers. window.isSecureContext is the reliable gate.
  if (window.isSecureContext && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fall through to legacy path.
    }
  }

  // Legacy fallback. Requires a user gesture in the same tick (a click
  // handler is fine). Creates an off-screen textarea, selects its
  // contents, runs execCommand('copy'), and tears it down.
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-9999px';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}
