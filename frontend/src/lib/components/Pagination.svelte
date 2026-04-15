<script lang="ts">
  let {
    page = 1,
    pages = 1,
    total = 0,
    onpage,
  }: {
    page: number;
    pages: number;
    total: number;
    onpage: (p: number) => void;
  } = $props();
</script>

{#if pages > 1}
  <div class="pagination">
    <span class="total">{total} items</span>
    <div class="controls">
      <button
        class="btn btn-sm btn-secondary"
        disabled={page <= 1}
        onclick={() => onpage(page - 1)}
      >
        Prev
      </button>
      <span class="page-info">Page {page} of {pages}</span>
      <button
        class="btn btn-sm btn-secondary"
        disabled={page >= pages}
        onclick={() => onpage(page + 1)}
      >
        Next
      </button>
    </div>
  </div>
{/if}

<style>
  .pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-color);
  }
  .total { font-size: 0.8rem; color: var(--text-secondary); }
  .controls { display: flex; align-items: center; gap: 0.75rem; }
  .page-info { font-size: 0.85rem; color: var(--text-secondary); }
</style>
