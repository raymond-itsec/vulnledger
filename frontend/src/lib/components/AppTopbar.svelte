<script lang="ts">
  // AppTopbar — breadcrumb-driven page header.
  //
  // Displays the breadcrumb trail set by the active page (or a path-derived
  // fallback computed in +layout). The optional title slot (rendered via the
  // children snippet) is for in-page secondary nav / page actions.
  //
  // Visual spec follows /design-system/project/ui_kits/app/Header.jsx:
  //  - Cream-tinted bar with subtle backdrop blur
  //  - Breadcrumb at the top, optional page title below
  //  - Search field on the right (focus ring in brand orange)
  //  - Slot for primary CTA buttons

  import type { Snippet } from 'svelte';
  import Breadcrumb from '$lib/components/Breadcrumb.svelte';
  import type { Crumb } from '$lib/stores/breadcrumb.svelte';

  let {
    crumbs = [],
    title,
    actions,
  }: {
    crumbs?: Crumb[];
    title?: string;
    actions?: Snippet;
  } = $props();

  let searchValue = $state('');
</script>

<header class="topbar">
  <div class="topbar-left">
    <Breadcrumb {crumbs} />
    {#if title}
      <h1 class="page-title">{title}</h1>
    {/if}
  </div>

  <div class="topbar-right">
    <label class="search" aria-label="Search workspace">
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
      <input type="search" placeholder="Search clients, findings, sessions…" bind:value={searchValue} />
    </label>
    {#if actions}
      {@render actions()}
    {/if}
  </div>
</header>

<style>
  .topbar {
    position: sticky;
    top: 0;
    z-index: 40;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 28px 14px;
    background: rgba(242, 237, 230, 0.78);
    backdrop-filter: blur(16px) saturate(140%);
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    border-bottom: 1px solid rgba(200, 190, 178, 0.35);
    font-family: var(--font-sans);
  }
  .topbar-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }
  .page-title {
    margin: 0;
    font-size: 22px;
    font-weight: 700;
    color: #1e1e2e;
    line-height: 1.2;
    letter-spacing: -0.01em;
  }
  .topbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }
  .search {
    position: relative;
    display: inline-flex;
    align-items: center;
    width: 280px;
    padding: 7px 12px 7px 32px;
    border-radius: 10px;
    border: 1.5px solid rgba(200, 190, 178, 0.5);
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: #9f9fb8;
    transition: all 150ms;
  }
  .search:focus-within {
    background: rgba(255, 255, 255, 0.95);
    border-color: #f07340;
    box-shadow: 0 0 0 3px rgba(240, 115, 64, 0.12);
  }
  .search svg {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #9f9fb8;
    pointer-events: none;
  }
  .search input {
    width: 100%;
    border: 0;
    background: transparent;
    color: #1e1e2e;
    font: inherit;
    font-size: 13px;
    outline: none;
  }
  .search input::placeholder {
    color: #9f9fb8;
  }
  @media (max-width: 880px) {
    .topbar {
      flex-direction: column;
      align-items: stretch;
    }
    .topbar-right {
      width: 100%;
    }
    .search {
      flex: 1;
      width: auto;
    }
  }
</style>
