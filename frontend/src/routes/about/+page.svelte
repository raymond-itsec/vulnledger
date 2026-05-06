<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>About - VulnLedger</title>
  <meta name="description" content="Learn about VulnLedger — the self-hosted workspace built for security professionals." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>About VulnLedger</h1>
    <p class="lead">VulnLedger is a self-hosted workspace built for security professionals who want to track findings, run review sessions, and deliver polished reports — without giving up control of their data.</p>
    <p>We believe security tooling should be as rigorous as the work itself. VulnLedger runs on your own infrastructure, keeps your client data inside your perimeter, and integrates with the workflows you already use.</p>
    <p>We are currently in closed early access. <a href="/">Join the waitlist</a> to be the first to know when spots open up.</p>
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
  h1 {
    margin: 0 0 1rem;
    font-size: 1.75rem;
    font-weight: 800;
    color: #1a1d2e;
    letter-spacing: -0.02em;
  }
  .lead {
    font-size: 1.05rem;
    font-weight: 500;
    color: #42455e;
    line-height: 1.7;
    margin: 0 0 1rem;
  }
  p {
    color: #42455e;
    line-height: 1.7;
    margin: 0 0 0.75rem;
  }
  a { color: #ff6a3d; text-decoration: underline; }
</style>
