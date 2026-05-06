<!--
  Static "something went wrong" panel. Used for page-level failures
  (failed-to-load lists, dead third-party widgets, the catch-all
  `<ErrorBoundary>` fallback). Surfaces:

  - A short headline.
  - Optional detail message (typically `apiError.toUserMessage()`).
  - Optional `requestId` shown in monospace with a copy button so the
    user can paste it into a bug report.
  - Optional retry callback.

  This is intentionally not a toast - toasts auto-dismiss; this panel
  stays put because the surrounding content is broken.
-->
<script lang="ts">
  interface Props {
    title?: string;
    message?: string | null;
    requestId?: string | null;
    onRetry?: () => void;
    retryLabel?: string;
  }

  let {
    title = 'Something went wrong',
    message = null,
    requestId = null,
    onRetry,
    retryLabel = 'Try again',
  }: Props = $props();

  let copied = $state(false);

  async function copyRequestId() {
    if (!requestId) return;
    try {
      await navigator.clipboard.writeText(requestId);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {
      // Clipboard API can fail in non-secure contexts; silently no-op.
    }
  }
</script>

<div class="error-state" role="alert">
  <div class="icon" aria-hidden="true">!</div>
  <div class="body">
    <h3 class="title">{title}</h3>
    {#if message}
      <p class="message">{message}</p>
    {/if}
    {#if requestId}
      <div class="request-id-row">
        <span class="request-id-label">Error ID:</span>
        <code class="request-id">{requestId}</code>
        <button
          type="button"
          class="copy-btn"
          onclick={copyRequestId}
          aria-label="Copy error ID"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    {/if}
    {#if onRetry}
      <button type="button" class="retry-btn" onclick={onRetry}>
        {retryLabel}
      </button>
    {/if}
  </div>
</div>

<style>
  .error-state {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1.25rem 1.5rem;
    background: var(--color-error-bg);
    border: 1px solid var(--color-error);
    border-radius: 0.5rem;
    color: var(--color-text-primary, #1a1a1a);
  }

  .icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: var(--color-error);
    color: white;
    font-size: 1.25rem;
    font-weight: 700;
    flex-shrink: 0;
  }

  .body {
    flex: 1;
    min-width: 0;
  }

  .title {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-error);
  }

  .message {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    line-height: 1.4;
  }

  .request-id-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
    font-size: 0.8125rem;
  }

  .request-id-label {
    color: var(--color-text-secondary, #6b7280);
  }

  .request-id {
    background: rgba(0, 0, 0, 0.05);
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    font-family: var(--font-mono, ui-monospace, monospace);
    font-size: 0.75rem;
    color: var(--color-text-primary, #1a1a1a);
    word-break: break-all;
  }

  .copy-btn,
  .retry-btn {
    background: white;
    border: 1px solid var(--color-error);
    color: var(--color-error);
    border-radius: 0.25rem;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 120ms ease, color 120ms ease;
  }

  .retry-btn {
    margin-top: 0.25rem;
    padding: 0.375rem 0.875rem;
    font-size: 0.8125rem;
  }

  .copy-btn:hover,
  .retry-btn:hover {
    background: var(--color-error);
    color: white;
  }
</style>
