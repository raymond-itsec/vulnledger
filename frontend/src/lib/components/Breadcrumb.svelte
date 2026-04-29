<script lang="ts">
  // Breadcrumb trail for the topbar.
  //
  // Design rules (from VulnLedger design system):
  //  - Each crumb label is hard-capped at 20 characters; longer labels truncate
  //    to 17 chars + "…" (full text remains in the title attribute on hover).
  //  - All but the last crumb are clickable when an href is provided.
  //  - The last crumb represents the current page and is never clickable.

  import type { Crumb } from '$lib/stores/breadcrumb.svelte';

  let { crumbs }: { crumbs: Crumb[] } = $props();

  const MAX_LABEL_LEN = 20;
  function truncate(label: string): string {
    if (!label) return '';
    return label.length > MAX_LABEL_LEN ? label.slice(0, 17) + '…' : label;
  }
</script>

{#if crumbs && crumbs.length > 0}
  <nav class="breadcrumb" aria-label="Breadcrumb">
    {#each crumbs as crumb, i}
      {@const isLast = i === crumbs.length - 1}
      {#if i > 0}
        <span class="sep" aria-hidden="true">/</span>
      {/if}
      {#if isLast || !crumb.href}
        <span class="crumb current" title={crumb.label} aria-current={isLast ? 'page' : undefined}>
          {truncate(crumb.label)}
        </span>
      {:else}
        <a class="crumb link" href={crumb.href} title={crumb.label}>
          {truncate(crumb.label)}
        </a>
      {/if}
    {/each}
  </nav>
{/if}

<style>
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
    font-size: 12px;
    line-height: 1.4;
  }
  .crumb {
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-decoration: none;
    transition: opacity 120ms;
  }
  .crumb.current {
    color: #6b6560;
    font-weight: 500;
    cursor: default;
  }
  .crumb.link {
    color: #d05a28;
    font-weight: 600;
    cursor: pointer;
  }
  .crumb.link:hover {
    opacity: 0.7;
    text-decoration: none;
  }
  .crumb.link:focus-visible {
    outline: 2px solid #f07340;
    outline-offset: 2px;
    border-radius: 3px;
  }
  .sep {
    color: #9b9188;
    user-select: none;
  }
</style>
