<script lang="ts">
  import { toast } from '$lib/stores/toast.svelte';

  // Per-toast "Copied" feedback so the button label flips briefly after
  // the user clicks. Keyed on the toast id; cleared when the toast is
  // dismissed (the entry just becomes stale).
  let copiedFor = $state<Record<number, boolean>>({});

  async function copyRequestId(id: number, requestId: string) {
    try {
      await navigator.clipboard.writeText(requestId);
      copiedFor = { ...copiedFor, [id]: true };
      setTimeout(() => {
        const { [id]: _drop, ...rest } = copiedFor;
        copiedFor = rest;
      }, 1500);
    } catch {
      // Clipboard API can fail in non-secure contexts (plain HTTP).
      // Falling through is fine — the ID is still selectable in the pill.
    }
  }
</script>

<div class="toast-viewport" aria-live="polite" aria-atomic="true">
  {#each toast.items as item (item.id)}
    <div class="toast" class:error={item.variant === 'error'} class:success={item.variant === 'success'}>
      <div class="body">
        <span class="message">{item.message}</span>
        {#if item.requestId}
          <div class="request-id-row">
            <span class="request-id-label">Error ID:</span>
            <code class="request-id">{item.requestId}</code>
            <button
              type="button"
              class="copy-btn"
              onclick={() => copyRequestId(item.id, item.requestId!)}
              aria-label="Copy error ID"
            >
              {copiedFor[item.id] ? 'Copied' : 'Copy'}
            </button>
          </div>
        {/if}
      </div>
      <button
        type="button"
        class="toast-close"
        aria-label="Dismiss notification"
        onclick={() => toast.dismiss(item.id)}
      >
        &times;
      </button>
    </div>
  {/each}
</div>

<style>
  .toast-viewport {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    z-index: 1200;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    pointer-events: none;
  }
  .toast {
    min-width: 280px;
    max-width: 420px;
    padding: 0.75rem 0.875rem;
    border-radius: 0.5rem;
    background: rgba(17, 24, 39, 0.96);
    color: white;
    box-shadow: 0 14px 32px rgba(0, 0, 0, 0.25);
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    pointer-events: auto;
  }
  .toast.error {
    background: rgba(153, 27, 27, 0.96);
  }
  .toast.success {
    background: rgba(22, 101, 52, 0.96);
  }
  .body {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .message {
    font-size: 0.875rem;
    line-height: 1.35;
  }
  .request-id-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    font-size: 0.75rem;
  }
  .request-id-label {
    opacity: 0.85;
  }
  .request-id {
    background: rgba(255, 255, 255, 0.18);
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    font-family: var(--font-mono, ui-monospace, monospace);
    font-size: 0.72rem;
    color: white;
    word-break: break-all;
    user-select: all;
  }
  .copy-btn {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: white;
    border-radius: 0.25rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.7rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 120ms ease;
  }
  .copy-btn:hover {
    background: rgba(255, 255, 255, 0.28);
  }
  .toast-close {
    border: none;
    background: transparent;
    color: inherit;
    font-size: 1rem;
    line-height: 1;
    opacity: 0.8;
    cursor: pointer;
    padding: 0;
    align-self: flex-start;
  }
  .toast-close:hover {
    opacity: 1;
  }
</style>
