<script lang="ts">
 // Branded fallback for any error SvelteKit raises that isn't caught
 // inside a route component - most commonly:
 // - URL doesn't match any route (e.g. an injected payload with extra
 // slashes that creates more path segments than a dynamic [id] route
 // can absorb)
 // - A load() function threw (we don't use load() much; mostly onMount)
 // - Anything else SvelteKit decides is fatal at the framework level
 //
 // Because PublicShell is context-aware (downgrades when nested inside
 // /app), we can render this inside it whether the user is logged in
 // or not - it just becomes the right chrome for the situation.

 import { page } from '$app/state';
 import PublicShell from '$lib/components/PublicShell.svelte';
 import { APP_BASE_PATH } from '$lib/config/routes';

 // Whatever SvelteKit captured. We deliberately do NOT echo error.message
 // unsafely - Svelte's text interpolation already escapes, but we still
 // want to be conservative about reflecting attacker-controlled URLs and
 // error strings, so we show a generic message.
 const status = $derived(page.status ?? 404);
 const isNotFound = $derived(status === 404);
</script>

<svelte:head>
 <title>{isNotFound ? 'Page not found' : 'Something went wrong'} - VulnLedger</title>
</svelte:head>

<PublicShell>
 <div class="error-card">
 <p class="status">{status}</p>
 <h1>{isNotFound ? 'Page not found' : 'Something went wrong'}</h1>
 <p class="copy">
 {#if isNotFound}
 The URL you followed doesn't match any page on this site.
 {:else}
 The application hit an unexpected error. Try again in a moment, or
 head back to a known starting point below.
 {/if}
 </p>
 <div class="actions">
 <a class="btn primary" href={APP_BASE_PATH}>Go to dashboard</a>
 <a class="btn secondary" href="/">Back to home</a>
 </div>
 </div>
</PublicShell>

<style>
 .error-card {
 width: 100%;
 max-width: 480px;
 padding: 2.5rem;
 border-radius: 1.25rem;
 background: rgba(255, 255, 255, 0.82);
 backdrop-filter: blur(24px) saturate(160%);
 -webkit-backdrop-filter: blur(24px) saturate(160%);
 border: 1px solid rgba(255, 255, 255, 0.78);
 box-shadow: 0 18px 40px rgba(80, 40, 120, 0.16),
 0 36px 70px rgba(80, 40, 120, 0.18);
 text-align: center;
 font-family: var(--font-sans);
 }
 .status {
 margin: 0 0 0.5rem;
 font-family: var(--font-mono, 'JetBrains Mono', monospace);
 font-size: 0.85rem;
 font-weight: 600;
 letter-spacing: 0.18em;
 color: #d05a28;
 text-transform: uppercase;
 }
 h1 {
 margin: 0 0 0.75rem;
 font-size: 1.75rem;
 font-weight: 800;
 color: #1e1e2e;
 letter-spacing: -0.01em;
 }
 .copy {
 margin: 0 0 1.5rem;
 color: #5a5a72;
 line-height: 1.6;
 font-size: 0.95rem;
 }
 .actions {
 display: flex;
 gap: 0.6rem;
 justify-content: center;
 flex-wrap: wrap;
 }
 .btn {
 display: inline-flex;
 align-items: center;
 justify-content: center;
 padding: 0.55rem 1rem;
 border-radius: 10px;
 font-size: 0.9rem;
 font-weight: 600;
 text-decoration: none;
 transition: all 150ms;
 }
 .btn.primary {
 background: #f07340;
 color: #fff;
 box-shadow: 0 2px 8px rgba(240, 115, 64, 0.3);
 }
 .btn.primary:hover {
 background: #d96530;
 text-decoration: none;
 }
 .btn.secondary {
 background: rgba(255, 255, 255, 0.55);
 color: #42455e;
 border: 1px solid rgba(200, 190, 178, 0.5);
 }
 .btn.secondary:hover {
 color: #f07340;
 border-color: #f07340;
 background: rgba(255, 106, 61, 0.06);
 text-decoration: none;
 }
</style>
