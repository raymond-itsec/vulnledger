<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Support Us - VulnLedger</title>
  <meta name="description" content="Ways to support VulnLedger and help keep it free and open." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Support Us</h1>
    <p class="lead">VulnLedger is built by a small team that genuinely cares about the security community. Here is how you can help.</p>

    <div class="support-item">
      <h2>⭐ Spread the word</h2>
      <p>Tell your colleagues and your network about VulnLedger. Word of mouth from practitioners carries more weight than any ad.</p>
    </div>

    <div class="support-item">
      <h2>🐛 Report bugs &amp; ideas</h2>
      <p>Found something broken or have a feature you need? <a href="/contact">Drop us a message</a> — every report directly improves the product.</p>
    </div>

    <div class="support-item">
      <h2>📬 Join the waitlist</h2>
      <p>Early access signups help us gauge demand and plan capacity. <a href="/">Sign up</a> if you have not already.</p>
    </div>

    <div class="support-item">
      <h2>💬 Give feedback</h2>
      <p>Once you are in early access, honest feedback about what works and what does not shapes every release.</p>
    </div>
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
  h2 { margin: 0 0 0.4rem; font-size: 1rem; font-weight: 700; color: #1a1d2e; }
  .lead { font-size: 1.05rem; font-weight: 500; color: #42455e; line-height: 1.7; margin: 0 0 1.25rem; }
  .support-item {
    padding: 1rem 0;
    border-bottom: 1px solid rgba(180, 160, 220, 0.2);
  }
  .support-item:last-child { border-bottom: none; padding-bottom: 0; }
  p { color: #42455e; line-height: 1.7; margin: 0; }
  a { color: #ff6a3d; text-decoration: underline; }
</style>
