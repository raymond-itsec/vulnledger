<script lang="ts">
  import { getContext, type Snippet } from 'svelte';
  import PublicHeader from '$lib/components/PublicHeader.svelte';
  import PublicFooter from '$lib/components/PublicFooter.svelte';
  import { APP_SHELL_CONTEXT_KEY } from '$lib/components/app-shell-context';

  let { children }: { children: Snippet } = $props();

  // If the /app shell (sidebar + topbar + footer) is already wrapping us
  // — i.e. an authenticated user navigated to /trust, /privacy, etc. via
  // the in-app PublicFooter links — skip our own header/footer/gradient
  // chrome and just render the page content. Otherwise (logged-out
  // visitors hitting these pages directly), render the full public chrome
  // as before.
  const isAppShellActive = getContext<() => boolean>(APP_SHELL_CONTEXT_KEY);
  const nested = $derived(isAppShellActive ? isAppShellActive() : false);
</script>

{#if nested}
  {@render children()}
{:else}
  <div class="public-shell">
    <PublicHeader />
    <main class="public-main">
      {@render children()}
    </main>
    <PublicFooter />
  </div>
{/if}

<style>
  :global(body) {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  }

  .public-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background:
      radial-gradient(ellipse 80% 60% at 15% 25%, rgba(255, 180, 150, 0.4) 0%, transparent 55%),
      radial-gradient(ellipse 70% 55% at 95% 15%, rgba(255, 200, 220, 0.3) 0%, transparent 60%),
      radial-gradient(ellipse 90% 70% at 85% 90%, rgba(180, 155, 245, 0.32) 0%, transparent 60%),
      linear-gradient(160deg, #fae2d8 0%, #f3d0e8 30%, #e0cdf5 60%, #d4d8f5 85%, #dad5f0 100%);
    background-attachment: fixed;
  }

  .public-main {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem 1.5rem;
  }
</style>
