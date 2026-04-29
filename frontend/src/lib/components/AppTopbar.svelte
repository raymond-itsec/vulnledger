<script lang="ts">
  // AppTopbar — breadcrumb-driven page header.
  //
  // Fixed-height bar (67px) so its bottom edge aligns with the sidebar's
  // brand divider, regardless of which page is rendered. Pages that want a
  // prominent heading should render their own <h1> in their body — the
  // topbar is just navigation context.

  import type { Snippet } from 'svelte';
  import Breadcrumb from '$lib/components/Breadcrumb.svelte';
  import type { Crumb } from '$lib/stores/breadcrumb.svelte';

  let {
    crumbs = [],
    actions,
  }: {
    crumbs?: Crumb[];
    actions?: Snippet;
  } = $props();

  let searchValue = $state('');
</script>

<header class="topbar">
  <div class="topbar-left">
    <Breadcrumb {crumbs} />
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
  /* Fixed 67px height aligns the bottom border with the sidebar's brand
     divider on every page, regardless of breadcrumb depth.

     Backdrop blur is graduated: 50px at the top → 24px at the bottom.
     Implemented via two stacked, absolutely-positioned pseudo-elements,
     each with its own backdrop-filter and a complementary linear-gradient
     mask. The masks fade in/out so the two blur strengths blend smoothly
     across the height. The cream tint also lives on the pseudos so we
     don't get a doubled fill in overlapping regions. */
  .topbar {
    position: sticky;
    top: 0;
    z-index: 40;
    isolation: isolate; /* keep the pseudos' z-index local to this element */
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    height: 67px;
    flex-shrink: 0;
    padding: 0 28px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.42);
    font-family: var(--font-sans);
  }
  .topbar::before,
  .topbar::after {
    content: '';
    position: absolute;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background: rgba(250, 228, 220, 0.62);
  }
  .topbar::before {
    backdrop-filter: blur(50px) saturate(170%);
    -webkit-backdrop-filter: blur(50px) saturate(170%);
    mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
    -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
  }
  .topbar::after {
    backdrop-filter: blur(24px) saturate(170%);
    -webkit-backdrop-filter: blur(24px) saturate(170%);
    mask-image: linear-gradient(to bottom, transparent 0%, black 100%);
    -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 100%);
  }
  .topbar-left {
    display: flex;
    align-items: center;
    min-width: 0;
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
      /* Allow the bar to grow to fit the stacked search field on narrow viewports. */
      height: auto;
      min-height: 67px;
      padding: 12px 28px;
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
