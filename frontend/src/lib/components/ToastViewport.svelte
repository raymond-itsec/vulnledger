<script lang="ts">
  import { toast } from '$lib/stores/toast.svelte';
  import { copyToClipboard } from '$lib/util/clipboard';

  // Per-toast "Copied" feedback so the icon swaps to a checkmark
  // briefly after the user clicks. Keyed on the toast id; the entry
  // is dropped after the timeout, or when the toast is dismissed (then
  // it's just stale and harmless).
  let copiedFor = $state<Record<number, boolean>>({});

  async function copyRequestId(id: number, requestId: string) {
    // Use the shared helper so the copy works on plain-HTTP origins
    // (the dev box). Modern navigator.clipboard.writeText requires a
    // secure context; the helper falls back to document.execCommand
    // when that's not available.
    const ok = await copyToClipboard(requestId);
    if (!ok) {
      toast.error('Could not copy to clipboard.');
      return;
    }
    // Two layers of feedback: a success toast (auto-dismissing 3.2s
    // confirmation, mirrors the SHA-copy pattern in
    // routes/sessions/[id]/+page.svelte) and a brief icon swap on
    // the button itself so the cursor focal point also confirms.
    toast.success('Error ID copied to clipboard.');
    copiedFor = { ...copiedFor, [id]: true };
    setTimeout(() => {
      const { [id]: _drop, ...rest } = copiedFor;
      copiedFor = rest;
    }, 1500);
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
              class:copied={copiedFor[item.id]}
              onclick={() => copyRequestId(item.id, item.requestId!)}
              title={copiedFor[item.id] ? 'Copied' : 'Copy error ID'}
              aria-label={copiedFor[item.id] ? 'Copied' : 'Copy error ID'}
            >
              {#if copiedFor[item.id]}
                <!-- Checkmark while feedback is showing. -->
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M5 13l4 4L19 7"/>
                </svg>
              {:else}
                <!-- Default two-square copy icon. Same SVG as the SHA copy
                     button in routes/sessions/[id]/+page.svelte for visual
                     consistency. -->
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <rect x="9" y="9" width="13" height="13" rx="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
              {/if}
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
    color: #ffffff;
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
    color: #ffffff;
  }
  /* Force white on every text-bearing descendant explicitly. The global
     `body { color: var(--text-primary) }` cascades down by inheritance,
     but global element-level rules (e.g. design-tokens.css `code, .code
     { color: var(--text-primary) }`) can override it on specific
     elements. Setting color on each child directly wins regardless. */
  .message,
  .request-id-label,
  .request-id {
    color: #ffffff;
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
    word-break: break-all;
    user-select: all;
    /* Override the design-tokens.css `code, .code` rule's pastel
       background tint that would otherwise show through on the dark
       toast surface. */
    border: 1px solid rgba(255, 255, 255, 0.25);
  }
  .copy-btn {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #ffffff;
    border-radius: 0.25rem;
    padding: 0.25rem;
    line-height: 0;
    cursor: pointer;
    transition: background 120ms ease, color 120ms ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .copy-btn:hover {
    background: rgba(255, 255, 255, 0.28);
  }
  .copy-btn.copied {
    background: rgba(255, 255, 255, 0.85);
    color: var(--color-success, #166534);
    border-color: rgba(255, 255, 255, 0.85);
  }
  .toast-close {
    border: none;
    background: transparent;
    color: #ffffff;
    font-size: 1.1rem;
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
