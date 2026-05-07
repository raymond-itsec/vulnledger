/**
 * Shared formatting helpers used across pages.
 *
 * Consolidates implementations that were previously duplicated in
 * `routes/sessions/[id]/+page.svelte`, `routes/profile/+page.svelte`,
 * `routes/admin/+page.svelte`, and `lib/api/attachments.ts`. Pages
 * import from here rather than re-implementing.
 */

/**
 * ISO timestamp -> locale-formatted date+time string.
 *
 * Uses Intl.DateTimeFormat('en-GB', medium / short) for stable,
 * locale-controlled output (e.g. `7 May 2026, 10:42`). This matches
 * the existing format on the profile and admin pages.
 *
 * Returns `placeholder` (default '--') for null / undefined / empty
 * values. Returns the input string verbatim if `Date` cannot parse it
 * (corrupted timestamp; better to render the raw value than crash or
 * show 'Invalid Date').
 *
 * Callers wanting different placeholder text (e.g. 'Never' for an
 * invite that's never been claimed) can pass it as the second arg.
 */
export function formatDateTime(
  value: string | null | undefined,
  placeholder: string = '--',
): string {
  if (!value) return placeholder;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed);
}

/**
 * Byte count -> human-readable size (B / KB / MB).
 * Returns '--' for null / undefined values, '0 B' for zero,
 * and uses one decimal place at KB+ scales.
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '--';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
