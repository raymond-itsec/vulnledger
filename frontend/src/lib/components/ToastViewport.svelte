<script lang="ts">
  import { toast } from '$lib/stores/toast.svelte';
</script>

<div class="toast-viewport" aria-live="polite" aria-atomic="true">
  {#each toast.items as item (item.id)}
    <div class="toast" class:error={item.variant === 'error'}>
      <span>{item.message}</span>
      <button type="button" class="toast-close" aria-label="Dismiss notification" onclick={() => toast.dismiss(item.id)}>
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
    min-width: 260px;
    max-width: 360px;
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
  .toast span {
    flex: 1;
    font-size: 0.875rem;
    line-height: 1.35;
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
  }
</style>
