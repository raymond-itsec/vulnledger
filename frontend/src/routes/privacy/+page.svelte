<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Privacy Policy - VulnLedger</title>
  <meta name="description" content="VulnLedger privacy policy — how we handle your personal data." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Privacy Policy</h1>
    <p class="muted">Last updated: April 2026</p>

    <h2>What data we collect</h2>
    <p>When you join the waitlist we collect your email address and the URL you came from. We use this solely to notify you when early access opens and to understand where our visitors come from.</p>

    <h2>What we do not collect</h2>
    <p>VulnLedger the application is self-hosted. We have no access to the data you store inside your instance — findings, clients, sessions, or reports are entirely under your control.</p>

    <h2>Third parties</h2>
    <p>The waitlist form sends data to our waitlist API hosted in the EU. We do not share your email with any third party and do not use it for advertising.</p>

    <h2>Removal</h2>
    <p>To have your email removed from the waitlist, <a href="/contact">contact us</a> and we will delete it within 48 hours.</p>

    <h2>Contact</h2>
    <p>Questions about this policy? Reach us via the <a href="/contact">contact page</a>.</p>
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
  h1 { margin: 0 0 0.25rem; font-size: 1.75rem; font-weight: 800; color: #1a1d2e; letter-spacing: -0.02em; }
  h2 { margin: 1.5rem 0 0.4rem; font-size: 1.05rem; font-weight: 700; color: #1a1d2e; }
  .muted { color: #8a8dac; font-size: 0.85rem; margin: 0 0 1.25rem; }
  p { color: #42455e; line-height: 1.7; margin: 0 0 0.75rem; }
  a { color: #ff6a3d; text-decoration: underline; }
</style>
