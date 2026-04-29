<script lang="ts">
  import BrandLockup from '$lib/components/BrandLockup.svelte';
  import { INVITE_PATH, LOGIN_PATH } from '$lib/config/routes';

  const WAITLIST_API_BASE = 'https://waitlist-api.vulnledger.app';
  const OG_IMAGE_PATH = '/branding/android-chrome-512x512.png';

  let email = $state('');
  let submitting = $state(false);
  let statusMessage = $state('');
  let statusVariant = $state<'success' | 'error' | 'info' | null>(null);

  function showStatus(text: string, variant: 'success' | 'error' | 'info') {
    statusMessage = text;
    statusVariant = variant;
  }

  async function submitWaitlist() {
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      showStatus('Enter your work email address.', 'error');
      return;
    }

    submitting = true;
    showStatus('Submitting…', 'info');

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
        showStatus('This work email is already on the waitlist.', 'success');
      } else {
        showStatus('You are in. Check your inbox for the welcome email.', 'success');
        email = '';
      }
    } catch (error: any) {
      showStatus(error?.message || 'Something went wrong. Please try again.', 'error');
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <title>VulnLedger — Workspace for Security Professionals</title>
  <meta name="description" content="VulnLedger is the self-hosted workspace for security professionals — track findings, run review sessions, collaborate with clients, and deliver polished PDF, CSV, and JSON reports. Join the early-access waitlist." />
  <meta name="keywords" content="security review platform, vulnerability tracking, pentest report tool, finding management, self-hosted security tool, OWASP review, security audit workflow, security reviewer software" />
  <meta name="author" content="VulnLedger" />
  <meta name="application-name" content="VulnLedger" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="googlebot" content="index, follow" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <meta name="color-scheme" content="light" />
  <meta name="theme-color" content="#fae2d8" />
  <meta name="format-detection" content="telephone=no" />

  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="VulnLedger" />
  <meta property="og:title" content="VulnLedger — Workspace for Security Professionals" />
  <meta property="og:description" content="Self-hosted workspace for security professionals. Track findings, run sessions, deliver client reports — without losing your mind." />
  <meta property="og:url" content="/" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:image" content={OG_IMAGE_PATH} />
  <meta property="og:image:type" content="image/png" />
  <meta property="og:image:width" content="512" />
  <meta property="og:image:height" content="512" />
  <meta property="og:image:alt" content="VulnLedger — Security reviews, finally under control." />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="VulnLedger — Workspace for Security Professionals" />
  <meta name="twitter:description" content="Self-hosted workspace for security professionals. Track findings, run sessions, deliver client reports." />
  <meta name="twitter:image" content={OG_IMAGE_PATH} />
  <meta name="twitter:image:alt" content="VulnLedger — Security reviews, finally under control." />

  <link rel="icon" href="/branding/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="16x16" href="/branding/favicon-16x16.png" />
  <link rel="icon" type="image/png" sizes="32x32" href="/branding/favicon-32x32.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="/branding/apple-touch-icon.png" />
  <link rel="manifest" href="/branding/site.webmanifest" />
  <meta name="msapplication-TileColor" content="#ff6a3d" />
  <meta name="msapplication-TileImage" content="/branding/android-chrome-192x192.png" />

  <link rel="preconnect" href="https://waitlist-api.vulnledger.app" />
  <link rel="dns-prefetch" href="https://waitlist-api.vulnledger.app" />

  <script type="application/ld+json">
    {JSON.stringify({
      '@context': 'https://schema.org',
      '@graph': [
        {
          '@type': 'Organization',
          '@id': 'https://waitlist.vulnledger.app/#organization',
          name: 'VulnLedger',
          url: 'https://waitlist.vulnledger.app/',
          logo: {
            '@type': 'ImageObject',
            url: 'https://waitlist.vulnledger.app/branding/android-chrome-512x512.png',
            width: 512,
            height: 512,
          },
        },
        {
          '@type': 'WebSite',
          '@id': 'https://waitlist.vulnledger.app/#website',
          url: 'https://waitlist.vulnledger.app/',
          name: 'VulnLedger',
          description: 'Self-hosted workspace for security professionals.',
          publisher: { '@id': 'https://waitlist.vulnledger.app/#organization' },
          inLanguage: 'en',
        },
        {
          '@type': 'SoftwareApplication',
          name: 'VulnLedger',
          applicationCategory: 'SecurityApplication',
          operatingSystem: 'Web, Linux (Docker)',
          description: 'Track security findings, manage review sessions, collaborate with clients, and deliver polished PDF / CSV / JSON reports.',
          url: 'https://waitlist.vulnledger.app/',
          offers: {
            '@type': 'Offer',
            price: '0',
            priceCurrency: 'USD',
            availability: 'https://schema.org/PreOrder',
          },
        },
      ],
    })}
  </script>
</svelte:head>

<div class="landing-shell">
  <nav class="nav">
    <BrandLockup href="/" />
    <div class="nav-right">
      <a class="btn-ghost" href={LOGIN_PATH}>Already invited? Sign in →</a>
    </div>
  </nav>

  <section class="hero">
    <div class="hero-sparks" aria-hidden="true">
      {#each Array.from({ length: 24 }, (_, i) => i) as index}
        <span class="spark spark-{index % 6}"></span>
      {/each}
    </div>

    <div class="hero-eyebrow">
      <span class="dot"></span>
      Now in private beta
    </div>

    <h1 class="hero-heading">
      Security reviews,<br />
      <span class="accent">finally</span> under<br />
      <span class="accent-2">control.</span>
    </h1>

    <p class="hero-sub">
      VulnLedger is the workspace for security professionals — track findings,
      manage sessions, collaborate with clients, and deliver reports
      without losing your mind.
    </p>

    <div class="waitlist-wrap">
      <img class="hero-mascot" src="/branding/vulny/happy-small.png" alt="VulnLedger mascot" />
      <form class="waitlist-card" onsubmit={(event) => { event.preventDefault(); submitWaitlist(); }}>
        <div>
          <label for="emailInput">Sign up for early access</label>
          <div class="waitlist-row">
            <input
              id="emailInput"
              class="waitlist-input"
              type="email"
              bind:value={email}
              placeholder="you@company.com"
              autocomplete="email"
              spellcheck="false"
              required
              aria-label="Email address"
            />
            <button type="submit" class="btn-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Get access'}
            </button>
          </div>
        </div>
        <a class="secondary-cta" href={INVITE_PATH}>Already have an invite code?</a>
        {#if statusMessage}
          <div class="waitlist-status show" class:is-success={statusVariant === 'success'} class:is-error={statusVariant === 'error'}>
            {statusMessage}
          </div>
        {/if}
        <p class="waitlist-note">
          Invite-only. No spam — just a heads-up when your spot is ready.
        </p>
      </form>
    </div>

    <div class="trust">
      <span class="trust-chip">EU-hosted option</span>
      <span class="trust-chip">PDF &amp; CSV export</span>
      <span class="trust-chip">SSO / OIDC</span>
    </div>
  </section>

  <p class="section-label">What you get</p>
  <div class="features">
    <div class="feature-card">
      <div class="feature-icon orange">◫</div>
      <h3>Session-driven reviews</h3>
      <p>Plan, scope, and execute security review sessions with a clear asset-to-finding chain. Every engagement lives in one place.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon purple">◎</div>
      <h3>Structured finding capture</h3>
      <p>Record vulnerabilities with severity, status, evidence attachments, and taxonomy tags — fast enough to keep pace with testing.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon green">↗</div>
      <h3>Polished PDF reports</h3>
      <p>Generate client-ready PDF reports in seconds — with CSV and JSON exports on the side for spreadsheets and downstream tooling.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon blue">◌</div>
      <h3>Multi-client workspaces</h3>
      <p>Manage dozens of clients without context bleed. Role-based access keeps each client&apos;s data exactly where it belongs.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon rose">▤</div>
      <h3>Self-hosted, data stays put</h3>
      <p>Runs on your own infrastructure with Docker — no third-party SaaS and no client data crossing your perimeter. Built for EU and regulated environments.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon teal">⋮</div>
      <h3>Full audit trail</h3>
      <p>Every login, finding edit, and session change is timestamped and recorded. Forensic-grade history without anyone having to remember to log it.</p>
    </div>
  </div>

  <footer class="footer">
    <div class="footer-brand">
      <BrandLockup href="/" />
    </div>
    <span>Built for security professionals who take their craft seriously.</span>
    <span>© 2026 VulnLedger. All rights reserved.</span>
  </footer>
</div>

<style>
  :global(body) {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  }

  .landing-shell {
    --accent-a: #ff6a3d;
    --accent-b: #ffb266;
    --accent-c: #7ab7ff;
    --accent-d: #a78bfa;
    --accent-e: #5dd39e;
    --ink: #1a1d2e;
    --ink-soft: #42455e;
    --muted: #8a8dac;
    --shadow-sm: 0 2px 4px rgba(80, 40, 120, 0.08), 0 6px 20px rgba(80, 40, 120, 0.1);
    --shadow-md: 0 4px 12px rgba(80, 40, 120, 0.1), 0 20px 50px rgba(80, 40, 120, 0.18);
    --shadow-lg: 0 12px 32px rgba(80, 40, 120, 0.18), 0 44px 88px rgba(80, 40, 120, 0.28);

    min-height: 100vh;
    color: var(--ink);
    background:
      radial-gradient(ellipse 80% 60% at 15% 25%, rgba(255, 180, 150, 0.55) 0%, transparent 55%),
      radial-gradient(ellipse 70% 55% at 95% 15%, rgba(255, 200, 220, 0.4) 0%, transparent 60%),
      radial-gradient(ellipse 90% 70% at 85% 90%, rgba(180, 155, 245, 0.45) 0%, transparent 60%),
      radial-gradient(ellipse 70% 60% at 10% 95%, rgba(160, 180, 255, 0.35) 0%, transparent 55%),
      linear-gradient(160deg, #fae2d8 0%, #f3d0e8 30%, #e0cdf5 60%, #d4d8f5 85%, #dad5f0 100%);
    background-attachment: fixed;
  }

  .nav {
    position: sticky;
    top: 0;
    z-index: 60;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.9rem clamp(1.25rem, 5vw, 3rem);
    background: rgba(250, 228, 220, 0.62);
    backdrop-filter: blur(24px) saturate(170%);
    border-bottom: 1px solid rgba(255, 255, 255, 0.42);
  }

  .nav-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .btn-ghost {
    font: inherit;
    font-size: 0.88rem;
    font-weight: 600;
    padding: 0.45rem 0.9rem;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.55);
    background: rgba(255,255,255,0.32);
    color: var(--ink-soft);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    backdrop-filter: blur(8px);
    transition: border-color 0.15s, color 0.15s, background 0.15s;
  }

  .btn-ghost:hover {
    border-color: var(--accent-a);
    color: var(--accent-a);
    background: rgba(255,106,61,0.08);
    text-decoration: none;
  }

  .hero {
    position: relative;
    overflow: hidden;
    min-height: calc(100vh - 62px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: clamp(3rem, 8vh, 6rem) clamp(1.25rem, 6vw, 4rem);
    gap: 1.85rem;
  }

  .hero > *:not(.hero-sparks) {
    position: relative;
    z-index: 3;
  }

  .hero-sparks {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 1;
  }

  .spark {
    position: absolute;
    border-radius: 999px;
    opacity: 0.4;
    animation: sparkle 4s ease-in-out infinite;
  }
  .spark-0 { width: 4px; height: 4px; left: 12%; top: 18%; background: rgba(255,245,215,1); box-shadow: 0 0 14px rgba(255,200,140,0.9); }
  .spark-1 { width: 3px; height: 3px; left: 76%; top: 22%; background: rgba(255,240,255,1); box-shadow: 0 0 10px rgba(220,185,255,0.9); animation-delay: -1s; }
  .spark-2 { width: 5px; height: 5px; left: 84%; top: 58%; background: rgba(240,245,255,1); box-shadow: 0 0 12px rgba(180,210,255,0.9); animation-delay: -2s; }
  .spark-3 { width: 4px; height: 4px; left: 22%; top: 78%; background: rgba(255,235,245,1); box-shadow: 0 0 12px rgba(255,175,210,0.9); animation-delay: -0.5s; }
  .spark-4 { width: 3px; height: 3px; left: 56%; top: 16%; background: rgba(255,245,220,1); box-shadow: 0 0 10px rgba(255,215,160,0.9); animation-delay: -2.5s; }
  .spark-5 { width: 5px; height: 5px; left: 64%; top: 82%; background: rgba(255,240,255,1); box-shadow: 0 0 14px rgba(220,185,255,0.9); animation-delay: -1.6s; }

  @keyframes sparkle {
    0%,100% { opacity: 0.15; transform: scale(0.5); }
    50% { opacity: 1; transform: scale(1.15); }
  }

  .hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--accent-a);
    padding: 0.28rem 0.75rem;
    border-radius: 999px;
    background: rgba(255,106,61,0.12);
    border: 1px solid rgba(255,106,61,0.25);
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-a);
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.75); }
  }

  .hero-heading {
    font-size: clamp(2.6rem, 6.5vw, 5rem);
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 1.05;
    color: var(--ink);
    max-width: 18ch;
  }

  .accent {
    background: linear-gradient(120deg, var(--accent-a), var(--accent-b));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .accent-2 {
    background: linear-gradient(120deg, var(--accent-d), var(--accent-c));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-sub {
    font-size: clamp(1rem, 2.2vw, 1.18rem);
    color: var(--ink-soft);
    line-height: 1.65;
    max-width: 50ch;
    font-weight: 400;
  }

  .waitlist-wrap {
    position: relative;
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .hero-mascot {
    position: absolute;
    top: 50%;
    left: 50%;
    margin-left: 244px;
    width: clamp(120px, 14vw, 180px);
    height: auto;
    user-select: none;
    filter: drop-shadow(0 18px 28px rgba(120,60,180,0.28));
    animation: mascot-float 6s ease-in-out infinite;
    transform-origin: center center;
  }

  @keyframes mascot-float {
    0%,100% { transform: translateY(-50%) rotate(-1.5deg); }
    50% { transform: translate(0, calc(-50% - 10px)) rotate(1.5deg); }
  }

  .waitlist-card {
    background: rgba(255,255,255,0.82);
    backdrop-filter: blur(28px) saturate(180%);
    border: 1px solid rgba(255,255,255,0.82);
    border-radius: 22px;
    padding: 2rem 2rem 1.75rem;
    box-shadow: var(--shadow-lg);
    width: 100%;
    max-width: 460px;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .waitlist-card label {
    font-size: 0.77rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--muted);
    display: block;
    margin-bottom: 0.55rem;
    text-align: center;
  }

  .waitlist-row {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .waitlist-input {
    width: 100%;
    font: inherit;
    font-size: 0.95rem;
    padding: 0.78rem 1rem;
    border-radius: 12px;
    border: 1.5px solid rgba(180,160,220,0.42);
    background: rgba(255,255,255,0.85);
    color: var(--ink);
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
  }

  .waitlist-input:hover { border-color: rgba(255,106,61,0.45); }

  .waitlist-input:focus {
    border-color: var(--accent-a);
    background: #fff;
    box-shadow: 0 0 0 4px rgba(255,106,61,0.15);
  }

  .btn-primary {
    font: inherit;
    font-size: 0.95rem;
    font-weight: 700;
    padding: 0.82rem 1.35rem;
    border-radius: 12px;
    border: 0;
    width: 100%;
    background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(255,106,61,0.28), var(--shadow-sm);
    transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(255,106,61,0.38), var(--shadow-md);
    filter: brightness(1.04);
  }

  .btn-primary:disabled {
    cursor: default;
    opacity: 0.8;
  }

  .secondary-cta {
    text-align: center;
    font-size: 0.84rem;
    font-weight: 600;
    color: var(--ink-soft);
    text-decoration: none;
  }

  .secondary-cta:hover {
    color: var(--accent-a);
    text-decoration: underline;
  }

  .waitlist-note {
    font-size: 0.76rem;
    color: var(--muted);
    text-align: center;
    line-height: 1.55;
  }

  .waitlist-status {
    display: none;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--ink-soft);
    text-align: center;
    padding: 0.6rem 0.9rem;
    border-radius: 10px;
    background: rgba(255,255,255,0.62);
    border: 1px solid rgba(255,255,255,0.78);
    box-shadow: var(--shadow-sm);
  }

  .waitlist-status.show {
    display: block;
    animation: status-in 0.28s ease both;
  }

  .waitlist-status.is-success {
    color: #1f6f46;
    border-color: rgba(93,211,158,0.55);
    background: rgba(93,211,158,0.14);
  }

  .waitlist-status.is-error {
    color: #a13544;
    border-color: rgba(255,150,150,0.55);
    background: rgba(255,150,150,0.14);
  }

  @keyframes status-in {
    from { opacity: 0; transform: translateY(-3px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .trust {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    justify-content: center;
  }

  .trust-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.77rem;
    font-weight: 600;
    color: var(--ink-soft);
    padding: 0.22rem 0.7rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.58);
    border: 1px solid rgba(255,255,255,0.75);
  }

  .section-label {
    text-align: center;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--muted);
    padding-top: clamp(1rem, 4vh, 2.5rem);
  }

  .features {
    padding: clamp(3rem, 7vh, 5rem) clamp(1.25rem, 6vw, 4rem);
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1.1rem;
    max-width: 1100px;
    margin: 0 auto;
  }

  .feature-card {
    background: rgba(255,255,255,0.62);
    backdrop-filter: blur(18px) saturate(160%);
    border: 1px solid rgba(255,255,255,0.72);
    border-radius: 18px;
    padding: 1.5rem 1.5rem 1.6rem;
    box-shadow: var(--shadow-sm);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
  }

  .feature-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
  }

  .feature-icon {
    width: 44px;
    height: 44px;
    border-radius: 13px;
    display: grid;
    place-items: center;
    margin-bottom: 1rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
    font-weight: 800;
  }
  .orange { background: linear-gradient(135deg, rgba(255,106,61,0.14), rgba(255,106,61,0.30)); color: #d4521f; }
  .purple { background: linear-gradient(135deg, rgba(167,139,250,0.16), rgba(167,139,250,0.34)); color: #7e57e0; }
  .green { background: linear-gradient(135deg, rgba(93,211,158,0.18), rgba(93,211,158,0.36)); color: #2fa46f; }
  .blue { background: linear-gradient(135deg, rgba(122,183,255,0.18), rgba(122,183,255,0.36)); color: #3878d6; }
  .rose { background: linear-gradient(135deg, rgba(232,90,140,0.16), rgba(232,90,140,0.34)); color: #d6427a; }
  .teal { background: linear-gradient(135deg, rgba(20,184,166,0.16), rgba(20,184,166,0.34)); color: #0d9488; }

  .feature-card h3 {
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.45rem;
    color: var(--ink);
  }

  .feature-card p {
    font-size: 0.88rem;
    color: var(--ink-soft);
    line-height: 1.6;
  }

  .footer {
    text-align: center;
    padding: 2.5rem clamp(1.25rem, 5vw, 3rem) 3rem;
    font-size: 0.8rem;
    color: var(--muted);
    border-top: 1px solid rgba(255,255,255,0.38);
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: center;
  }

  .footer-brand {
    display: flex;
    align-items: center;
    margin-bottom: 0.25rem;
  }

  .footer-brand :global(.label) {
    background: linear-gradient(135deg, #ff6b3d 0%, #7b78f2 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }

  @media (prefers-reduced-motion: reduce) {
    .hero-mascot,
    .spark,
    .dot {
      animation: none;
    }
  }

  @media (max-width: 880px) {
    .hero-mascot { display: none; }
  }

  @media (max-width: 520px) {
    .nav-right .btn-ghost { display: none; }
  }
</style>
