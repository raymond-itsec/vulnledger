<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    title = '',
    show = false,
    onclose,
    children,
  }: {
    title?: string;
    show?: boolean;
    onclose?: () => void;
    children?: Snippet;
  } = $props();
</script>

{#if show}
  <div class="overlay" role="dialog" aria-modal="true">
    <div class="modal">
      <div class="modal-header">
        <h2>{title}</h2>
        <button class="close-btn" onclick={onclose}>&times;</button>
      </div>
      <div class="modal-body">
        {#if children}{@render children()}{/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(40, 25, 70, 0.42);
    backdrop-filter: blur(6px) saturate(140%);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }
  .modal {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.72);
    border-radius: 0.75rem;
    width: 100%;
    max-width: 640px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow:
      0 16px 40px rgba(80, 40, 120, 0.18),
      0 32px 72px rgba(80, 40, 120, 0.16);
  }
  .modal-header {
    position: sticky;
    top: 0;
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    background: rgba(255, 255, 255, 0.78);
    backdrop-filter: blur(14px) saturate(150%);
    border-bottom: 1px solid rgba(203, 187, 229, 0.42);
  }
  .modal-header h2 { font-size: 1.125rem; font-weight: 600; }
  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: var(--text-secondary);
    line-height: 1;
    padding: 0 0.25rem;
    border-radius: 0.25rem;
    transition: background-color 0.15s, color 0.15s;
  }
  .close-btn:hover {
    background: rgba(80, 40, 120, 0.08);
    color: var(--text-primary);
  }
  .modal-body { padding: 1.5rem; }
</style>
