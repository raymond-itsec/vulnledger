<script lang="ts">
  import PublicShell from '$lib/components/PublicShell.svelte';
</script>

<svelte:head>
  <title>Usage Guidelines - VulnLedger</title>
  <meta name="description" content="Usage guidelines for VulnLedger — responsible and ethical use of the platform." />
</svelte:head>

<PublicShell>
  <div class="page-card">
    <h1>Usage Guidelines</h1>
    <p class="lead">VulnLedger is built for ethical security work. These guidelines define what responsible use looks like.</p>

    <h2>Authorised testing only</h2>
    <p>Only use VulnLedger to document findings for systems and clients where you have explicit written authorisation. Unauthorised testing is illegal in most jurisdictions.</p>

    <h2>Client data</h2>
    <p>Treat all client data stored in VulnLedger with the same confidentiality you would apply to any engagement deliverable. Do not share credentials or findings with third parties without explicit client consent.</p>

    <h2>Responsible disclosure</h2>
    <p>If your work uncovers vulnerabilities, follow a responsible disclosure process. VulnLedger can help you document and track the timeline, but the ethical obligation to disclose responsibly remains yours.</p>

    <h2>Community conduct</h2>
    <p>If you use VulnLedger in a team, treat fellow team members professionally. Maintain integrity in how findings are categorised and reported.</p>
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
