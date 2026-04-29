<script lang="ts">
  import { INVITE_PATH, LOGIN_PATH } from '$lib/config/routes';

  const WAITLIST_API_BASE = 'https://waitlist-api.vulnledger.app';

  let email = $state('');
  let submitting = $state(false);
  let statusMessage = $state('');
  let statusVariant = $state<'success' | 'error' | 'info' | null>(null);

  function setStatus(message: string, variant: 'success' | 'error' | 'info') {
    statusMessage = message;
    statusVariant = variant;
  }

  async function submitWaitlist() {
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setStatus('Enter your work email address.', 'error');
      return;
    }

    submitting = true;
    setStatus('Submitting...', 'info');

    try {
      const response = await fetch(`${WAITLIST_API_BASE}/api/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: normalizedEmail,
          original_referrer: typeof document !== 'undefined' ? document.referrer || null : null,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.ok) {
        throw new Error(data.error || 'Could not join the waitlist.');
      }

      if (data.status === 'already_joined') {
        setStatus('This work email is already on the waitlist.', 'success');
      } else {
        setStatus('You are in. Check your inbox for the welcome email.', 'success');
        email = '';
      }
    } catch (error: any) {
      setStatus(error?.message || 'Something went wrong. Please try again.', 'error');
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <title>VulnLedger - Workspace for Security Professionals</title>
  <meta
    name="description"
    content="VulnLedger is the self-hosted workspace for security professionals. Join the early-access waitlist."
  />
</svelte:head>

<div class="landing-shell">
  <nav class="nav">
    <a class="nav-brand" href="/">
      <img class="brand-logo" src="/branding/vl-logo-small.png" alt="VulnLedger logo" />
    </a>
    <div class="nav-right">
      <a class="btn-ghost" href={INVITE_PATH}>Already have an invite code?</a>
      <a class="btn-ghost" href={LOGIN_PATH}>Sign in</a>
    </div>
  </nav>

  <section class="hero">
    <div class="hero-copy">
      <div class="hero-eyebrow">Now in private beta</div>
      <h1>Security reviews, finally under control.</h1>
      <p>
        VulnLedger is the workspace for security professionals. Track findings,
        manage sessions, collaborate with clients, and deliver polished reports
        without losing your mind.
      </p>
      <div class="trust">
        <span>EU-hosted option</span>
        <span>PDF / CSV / JSON export</span>
        <span>SSO / OIDC</span>
      </div>
    </div>

    <div class="hero-card-wrap">
      <img class="hero-mascot" src="/branding/vulny-clip.png" alt="VulnLedger mascot" />
      <form class="waitlist-card" onsubmit={(event) => { event.preventDefault(); submitWaitlist(); }}>
        <label for="waitlist-email">Sign up for early access</label>
        <input
          id="waitlist-email"
          class="waitlist-input"
          type="email"
          bind:value={email}
          placeholder="you@company.com"
          autocomplete="email"
          required
        />
        <button type="submit" class="btn-primary" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Get access'}
        </button>
        <a class="invite-link" href={INVITE_PATH}>Already have an invite code?</a>
        {#if statusMessage}
          <div class="status" class:is-success={statusVariant === 'success'} class:is-error={statusVariant === 'error'}>
            {statusMessage}
          </div>
        {/if}
        <p class="waitlist-note">Invite-only. No spam, just a heads-up when your spot is ready.</p>
      </form>
    </div>
  </section>

  <section class="features">
    <article class="feature-card">
      <h2>Session-driven reviews</h2>
      <p>Plan, scope, and execute security review sessions with a clear asset-to-finding chain.</p>
    </article>
    <article class="feature-card">
      <h2>Structured findings</h2>
      <p>Capture severity, status, references, and evidence attachments fast enough to keep pace with testing.</p>
    </article>
    <article class="feature-card">
      <h2>Client-ready reporting</h2>
      <p>Generate polished PDF reports with CSV and JSON exports for the teams that need raw data too.</p>
    </article>
    <article class="feature-card">
      <h2>Multi-client workspaces</h2>
      <p>Keep client data separated with role-based access and a workflow built for repeated engagements.</p>
    </article>
    <article class="feature-card">
      <h2>Self-hosted by design</h2>
      <p>Run it on your own infrastructure with Docker. Your data stays on your side of the fence.</p>
    </article>
    <article class="feature-card">
      <h2>Audit trail included</h2>
      <p>Track logins, session activity, and finding changes without asking reviewers to keep a second notebook.</p>
    </article>
  </section>
</div>

<style>
  .landing-shell {
    min-height: 100vh;
    background:
      radial-gradient(circle at top left, rgba(255, 174, 140, 0.45), transparent 32%),
      radial-gradient(circle at top right, rgba(167, 139, 250, 0.28), transparent 28%),
      radial-gradient(circle at bottom right, rgba(122, 183, 255, 0.26), transparent 34%),
      linear-gradient(160deg, #fae2d8 0%, #f3d0e8 30%, #e0cdf5 60%, #d4d8f5 85%, #dad5f0 100%);
    color: #1a1d2e;
  }
  .nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem clamp(1.25rem, 4vw, 3rem);
    background: rgba(255, 255, 255, 0.36);
    backdrop-filter: blur(18px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.45);
  }
  .nav-brand {
    display: inline-flex;
    align-items: center;
  }
  .brand-logo {
    width: min(14rem, 48vw);
    height: auto;
  }
  .nav-right {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }
  .btn-ghost {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 2.5rem;
    padding: 0.55rem 1rem;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.55);
    background: rgba(255, 255, 255, 0.42);
    color: #2a2c44;
    text-decoration: none;
    font-weight: 600;
  }
  .btn-ghost:hover {
    text-decoration: none;
    border-color: rgba(255, 106, 61, 0.45);
    color: #c94f21;
  }
  .hero {
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(340px, 460px);
    gap: clamp(2rem, 5vw, 5rem);
    align-items: center;
    padding: clamp(3rem, 8vh, 6rem) clamp(1.25rem, 6vw, 4rem);
    max-width: 1200px;
    margin: 0 auto;
  }
  .hero-copy h1 {
    font-size: clamp(2.9rem, 7vw, 5rem);
    line-height: 1.02;
    letter-spacing: 0;
    margin: 0.9rem 0 1rem;
  }
  .hero-copy p {
    font-size: 1.08rem;
    line-height: 1.7;
    color: #42455e;
    max-width: 42rem;
  }
  .hero-eyebrow {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    background: rgba(255, 106, 61, 0.12);
    border: 1px solid rgba(255, 106, 61, 0.2);
    color: #ff6a3d;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
  }
  .trust {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin-top: 1.25rem;
  }
  .trust span {
    padding: 0.4rem 0.75rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.58);
    border: 1px solid rgba(255, 255, 255, 0.72);
    color: #42455e;
    font-size: 0.82rem;
    font-weight: 600;
  }
  .hero-card-wrap {
    position: relative;
    display: flex;
    justify-content: center;
  }
  .hero-mascot {
    position: absolute;
    top: 50%;
    right: -4.75rem;
    width: clamp(6rem, 16vw, 10rem);
    transform: translateY(-50%);
    filter: drop-shadow(0 18px 28px rgba(120, 60, 180, 0.22));
  }
  .waitlist-card {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    padding: 2rem;
    border-radius: 1.5rem;
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.82);
    box-shadow: 0 22px 70px rgba(80, 40, 120, 0.22);
    backdrop-filter: blur(22px);
  }
  .waitlist-card label {
    text-align: center;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #8a8dac;
  }
  .waitlist-input {
    width: 100%;
    min-height: 3rem;
    padding: 0.85rem 1rem;
    border-radius: 0.85rem;
    border: 1px solid rgba(180, 160, 220, 0.42);
    background: rgba(255, 255, 255, 0.92);
    font: inherit;
    color: #1a1d2e;
  }
  .waitlist-input:focus {
    outline: none;
    border-color: #ff6a3d;
    box-shadow: 0 0 0 4px rgba(255, 106, 61, 0.14);
  }
  .btn-primary {
    min-height: 3rem;
    border: 0;
    border-radius: 0.85rem;
    background: linear-gradient(135deg, #ff6a3d, #ffb266);
    color: #fff;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
  }
  .btn-primary:disabled {
    opacity: 0.7;
    cursor: default;
  }
  .invite-link {
    text-align: center;
    color: #42455e;
    font-size: 0.9rem;
    font-weight: 600;
  }
  .status {
    padding: 0.75rem 0.9rem;
    border-radius: 0.85rem;
    background: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.78);
    text-align: center;
    font-size: 0.88rem;
  }
  .status.is-success {
    color: #1f6f46;
    background: rgba(93, 211, 158, 0.14);
    border-color: rgba(93, 211, 158, 0.45);
  }
  .status.is-error {
    color: #a13544;
    background: rgba(255, 150, 150, 0.14);
    border-color: rgba(255, 150, 150, 0.45);
  }
  .waitlist-note {
    text-align: center;
    font-size: 0.78rem;
    color: #8a8dac;
    line-height: 1.5;
  }
  .features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.25rem 3.5rem;
  }
  .feature-card {
    padding: 1.4rem;
    border-radius: 1.1rem;
    background: rgba(255, 255, 255, 0.62);
    border: 1px solid rgba(255, 255, 255, 0.72);
    box-shadow: 0 10px 30px rgba(80, 40, 120, 0.12);
    backdrop-filter: blur(14px);
  }
  .feature-card h2 {
    font-size: 1rem;
    margin-bottom: 0.55rem;
  }
  .feature-card p {
    font-size: 0.9rem;
    line-height: 1.6;
    color: #42455e;
  }
  @media (max-width: 960px) {
    .hero {
      grid-template-columns: 1fr;
    }
    .hero-card-wrap {
      max-width: 460px;
      width: 100%;
      margin: 0 auto;
    }
    .hero-mascot {
      display: none;
    }
  }
  @media (max-width: 640px) {
    .nav {
      flex-direction: column;
      gap: 1rem;
    }
    .nav-right {
      width: 100%;
      justify-content: center;
      flex-wrap: wrap;
    }
  }
</style>
