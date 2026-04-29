<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Terms of Service - VulnLedger</title>
  <meta name="description" content="VulnLedger terms of service." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Terms of Service</h1>
    <p class="muted">Last updated: April 2026</p>

    <h2>Use of the software</h2>
    <p>VulnLedger is provided for legitimate security review and vulnerability management purposes. You are responsible for how you deploy and use the software within your organisation.</p>

    <h2>Prohibited use</h2>
    <p>You may not use VulnLedger to track, document, or facilitate attacks on systems you are not authorised to test. Misuse voids any support entitlement.</p>

    <h2>No warranty</h2>
    <p>The software is provided "as is". We make no guarantees of uptime, fitness for a particular purpose, or freedom from bugs. Use it in production at your own risk and always keep backups.</p>

    <h2>Limitation of liability</h2>
    <p>To the maximum extent permitted by law, VulnLedger and its contributors are not liable for any damages arising from the use or inability to use the software.</p>

    <h2>Changes</h2>
    <p>These terms may be updated from time to time. Continued use of the software after changes constitutes acceptance of the new terms.</p>

    <h2>Questions</h2>
    <p><a href="/contact">Contact us</a> if you have questions about these terms.</p>
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
