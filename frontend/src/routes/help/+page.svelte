<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Help - VulnLedger</title>
  <meta name="description" content="Help and documentation for VulnLedger." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Help &amp; Documentation</h1>
    <p class="lead">Full documentation is coming soon alongside the public release.</p>
    <p>In the meantime, if you have a question or run into an issue, reach us via <a href="/contact">the contact page</a> and we will get back to you as soon as possible.</p>
  </div>
</PublicShell>

<style>
  .page-card {
    width: 100%;
    max-width: 640px;
    padding: 2.5rem;
    border-radius: 1.25rem;
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.78);
    box-shadow: 0 18px 40px rgba(80, 40, 120, 0.16), 0 36px 70px rgba(80, 40, 120, 0.18);
  }
  h1 { margin: 0 0 1rem; font-size: 1.75rem; font-weight: 800; color: #1a1d2e; letter-spacing: -0.02em; }
  .lead { font-size: 1.05rem; font-weight: 500; color: #42455e; line-height: 1.7; margin: 0 0 1rem; }
  p { color: #42455e; line-height: 1.7; margin: 0 0 0.75rem; }
  a { color: #ff6a3d; text-decoration: underline; }
</style>
