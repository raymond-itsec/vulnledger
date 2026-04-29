<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Contact - VulnLedger</title>
  <meta name="description" content="Get in touch with the VulnLedger team." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Contact</h1>
    <p class="lead">Have a question, a feature request, or a bug to report? We read every message.</p>

    <div class="contact-item">
      <span class="label">General enquiries</span>
      <a href="mailto:hello@vulnledger.app">hello@vulnledger.app</a>
    </div>
    <div class="contact-item">
      <span class="label">Security &amp; responsible disclosure</span>
      <a href="mailto:security@vulnledger.app">security@vulnledger.app</a>
    </div>
    <div class="contact-item">
      <span class="label">Waitlist &amp; early access</span>
      <a href="/">Join the waitlist</a>
    </div>

    <p class="note">We aim to respond within 2 business days. For security disclosures we target 48 hours.</p>
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
  .lead { font-size: 1.05rem; font-weight: 500; color: #42455e; line-height: 1.7; margin: 0 0 1.5rem; }
  .contact-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin-bottom: 1.1rem;
    padding-bottom: 1.1rem;
    border-bottom: 1px solid rgba(180, 160, 220, 0.2);
  }
  .contact-item:last-of-type { border-bottom: none; }
  .label { font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #8a8dac; }
  a { color: #ff6a3d; text-decoration: none; font-weight: 600; font-size: 1rem; }
  a:hover { text-decoration: underline; }
  .note { margin-top: 1.5rem; font-size: 0.85rem; color: #8a8dac; line-height: 1.6; }
</style>
