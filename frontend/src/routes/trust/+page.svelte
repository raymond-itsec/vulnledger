<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Trust &amp; Security - VulnLedger</title>
  <meta name="description" content="How VulnLedger handles your data, security, and privacy." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Trust &amp; Security</h1>
    <p class="lead">Security is not a feature we bolt on — it shapes every decision we make.</p>

    <h2>Self-hosted by design</h2>
    <p>VulnLedger runs entirely on your own infrastructure. Your findings, client data, and session history never leave your environment unless you export them.</p>

    <h2>No telemetry</h2>
    <p>We do not collect usage analytics or send any data back to our servers. What you run is what you own.</p>

    <h2>Audit trail</h2>
    <p>Every login, finding edit, and status change is logged with a timestamp. You always know who did what and when.</p>

    <h2>Responsible disclosure</h2>
    <p>Found a vulnerability in VulnLedger itself? Please contact us via <a href="/contact">the contact page</a>. We take security reports seriously and aim to respond within 48 hours.</p>
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
  h2 { margin: 1.5rem 0 0.4rem; font-size: 1.05rem; font-weight: 700; color: #1a1d2e; }
  .lead { font-size: 1.05rem; font-weight: 500; color: #42455e; line-height: 1.7; margin: 0 0 1rem; }
  p { color: #42455e; line-height: 1.7; margin: 0 0 0.75rem; }
  a { color: #ff6a3d; text-decoration: underline; }
</style>
