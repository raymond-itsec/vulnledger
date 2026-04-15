<script lang="ts">
  import { onMount } from 'svelte';
  import { auth, login as doLogin, setToken } from '$lib/stores/auth.svelte';
  import { clientsApi } from '$lib/api/clients';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { findingsApi, type Finding, RISK_LEVELS, REMEDIATION_STATUSES } from '$lib/api/findings';
  import Badge from '$lib/components/Badge.svelte';

  let username = $state('');
  let password = $state('');
  let loginError = $state('');
  let loggingIn = $state(false);
  let oidcAvailable = $state(false);

  let clientCount = $state(0);
  let sessionCount = $state(0);
  let findingCount = $state(0);
  let openFindingCount = $state(0);
  let recentSessions = $state<Session[]>([]);
  let recentFindings = $state<Finding[]>([]);
  let riskBreakdown = $state<Record<string, number>>({});
  let statusBreakdown = $state<Record<string, number>>({});
  let loading = $state(true);

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');

  async function handleLogin() {
    loginError = '';
    loggingIn = true;
    try {
      await doLogin(username, password);
    } catch (e: any) {
      loginError = e.message;
    } finally {
      loggingIn = false;
    }
  }

  async function loadDashboard() {
    try {
      const [clients, sessions, findings, openFindings, recentF] = await Promise.all([
        clientsApi.list(1, 1),
        sessionsApi.list(undefined, 1, 5),
        findingsApi.list({ page: 1, per_page: 1 }),
        findingsApi.list({ remediation_status: 'open', page: 1, per_page: 1 }),
        findingsApi.list({ page: 1, per_page: 5 }),
      ]);
      clientCount = clients.total;
      sessionCount = sessions.total;
      findingCount = findings.total;
      openFindingCount = openFindings.total;
      recentSessions = sessions.items;
      recentFindings = recentF.items;

      // Load risk and status breakdowns
      const risk: Record<string, number> = {};
      const status: Record<string, number> = {};
      for (const level of RISK_LEVELS) {
        const r = await findingsApi.list({ risk_level: level, page: 1, per_page: 1 });
        if (r.total > 0) risk[level] = r.total;
      }
      for (const s of REMEDIATION_STATUSES) {
        const r = await findingsApi.list({ remediation_status: s, page: 1, per_page: 1 });
        if (r.total > 0) status[s] = r.total;
      }
      riskBreakdown = risk;
      statusBreakdown = status;
    } catch {
      // ignore
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    // Handle OIDC callback token in URL
    const params = new URLSearchParams(window.location.search);
    const oidcToken = params.get('oidc_token');
    if (oidcToken) {
      await setToken(oidcToken);
      window.history.replaceState({}, '', '/');
    }
    // Check if OIDC is available
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      // We'll check for OIDC route availability
      const oidcRes = await fetch('/api/auth/oidc/login', { method: 'HEAD', redirect: 'manual' });
      oidcAvailable = oidcRes.status !== 404;
    } catch {
      oidcAvailable = false;
    }
  });

  $effect(() => {
    if (auth.isAuthenticated) {
      loadDashboard();
    }
  });

  const riskColors: Record<string, string> = {
    critical: 'var(--critical)',
    high: 'var(--high)',
    medium: 'var(--medium)',
    low: 'var(--low)',
    informational: 'var(--informational)',
  };
</script>

{#if !auth.isAuthenticated}
  <div class="login-page">
    <div class="login-card">
      <h1>Security Findings Manager</h1>
      <p class="subtitle">Sign in to continue</p>
      {#if loginError}
        <div class="error">{loginError}</div>
      {/if}
      <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }}>
        <div class="form-group">
          <label for="username">Username</label>
          <input id="username" type="text" bind:value={username} required autocomplete="username" />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input id="password" type="password" bind:value={password} required autocomplete="current-password" />
        </div>
        <button class="btn btn-primary login-btn" type="submit" disabled={loggingIn}>
          {loggingIn ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
      {#if oidcAvailable}
        <div class="sso-divider">
          <span>or</span>
        </div>
        <a href="/api/auth/oidc/login" class="btn btn-secondary login-btn sso-btn">
          Sign in with SSO
        </a>
      {/if}
    </div>
  </div>
{:else}
  <div class="page-header">
    <h1>Dashboard</h1>
    {#if canEdit}
      <div style="display:flex;gap:0.5rem;">
        <a href="/clients" class="btn btn-secondary btn-sm">New Client</a>
        <a href="/findings?new=1" class="btn btn-primary btn-sm">New Finding</a>
      </div>
    {/if}
  </div>

  {#if loading}
    <p>Loading...</p>
  {:else}
    <!-- Top-level stats -->
    <div class="stat-cards">
      <a href="/clients" class="stat-card clickable">
        <div class="label">Clients</div>
        <div class="value">{clientCount}</div>
      </a>
      <a href="/sessions" class="stat-card clickable">
        <div class="label">Sessions</div>
        <div class="value">{sessionCount}</div>
      </a>
      <a href="/findings" class="stat-card clickable">
        <div class="label">Total Findings</div>
        <div class="value">{findingCount}</div>
      </a>
      <a href="/findings?remediation_status=open" class="stat-card clickable highlight">
        <div class="label">Open Findings</div>
        <div class="value">{openFindingCount}</div>
      </a>
    </div>

    <!-- Breakdown row -->
    <div class="breakdown-row">
      <!-- Risk Level Breakdown -->
      {#if Object.keys(riskBreakdown).length > 0}
        <div class="card breakdown-card">
          <h2>Findings by Risk Level</h2>
          <div class="bar-chart">
            {#each RISK_LEVELS as level}
              {#if riskBreakdown[level]}
                {@const count = riskBreakdown[level]}
                {@const pct = Math.max(8, (count / findingCount) * 100)}
                <div class="bar-row">
                  <span class="bar-label">{level}</span>
                  <div class="bar-track">
                    <div class="bar-fill" style="width:{pct}%;background:{riskColors[level]}"></div>
                  </div>
                  <span class="bar-value">{count}</span>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      {/if}

      <!-- Status Breakdown -->
      {#if Object.keys(statusBreakdown).length > 0}
        <div class="card breakdown-card">
          <h2>Findings by Status</h2>
          <div class="bar-chart">
            {#each REMEDIATION_STATUSES as s}
              {#if statusBreakdown[s]}
                {@const count = statusBreakdown[s]}
                {@const pct = Math.max(8, (count / findingCount) * 100)}
                <div class="bar-row">
                  <span class="bar-label">{s.replace('_', ' ')}</span>
                  <div class="bar-track">
                    <div class="bar-fill" style="width:{pct}%;background:var(--accent)"></div>
                  </div>
                  <span class="bar-value">{count}</span>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      {/if}
    </div>

    <!-- Two-column: Recent Sessions + Recent Findings -->
    <div class="two-col">
      <div class="card">
        <h2 style="margin-bottom:1rem;font-size:1.1rem;">Recent Sessions</h2>
        {#if recentSessions.length === 0}
          <p class="empty-state">No review sessions yet.</p>
        {:else}
          <table>
            <thead>
              <tr><th>Review Name</th><th>Date</th><th>Status</th></tr>
            </thead>
            <tbody>
              {#each recentSessions as session}
                <tr>
                  <td><a href="/sessions/{session.session_id}">{session.review_name}</a></td>
                  <td>{session.review_date}</td>
                  <td><Badge text={session.status} variant={session.status} /></td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>

      <div class="card">
        <h2 style="margin-bottom:1rem;font-size:1.1rem;">Recent Findings</h2>
        {#if recentFindings.length === 0}
          <p class="empty-state">No findings yet.</p>
        {:else}
          <table>
            <thead>
              <tr><th>Title</th><th>Risk</th><th>Status</th></tr>
            </thead>
            <tbody>
              {#each recentFindings as f}
                <tr>
                  <td><a href="/findings/{f.finding_id}">{f.title}</a></td>
                  <td><Badge text={f.risk_level} variant={f.risk_level} /></td>
                  <td><Badge text={f.remediation_status} variant={f.remediation_status} /></td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    </div>
  {/if}
{/if}

<style>
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  }
  .login-card {
    background: white;
    padding: 2.5rem;
    border-radius: 0.75rem;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }
  .login-card h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .subtitle { color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.9rem; }
  .error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: var(--critical);
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }
  .login-btn { width: 100%; justify-content: center; padding: 0.625rem; text-align: center; text-decoration: none; display: block; }
  .sso-divider {
    text-align: center;
    margin: 1rem 0;
    position: relative;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }
  .sso-divider::before, .sso-divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: var(--border-color);
  }
  .sso-divider::before { left: 0; }
  .sso-divider::after { right: 0; }
  .sso-btn { margin-top: 0; }

  .stat-card.clickable {
    text-decoration: none;
    color: inherit;
    transition: transform 0.1s, box-shadow 0.1s;
  }
  .stat-card.clickable:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  .stat-card.highlight {
    border-left: 3px solid var(--critical);
  }

  .breakdown-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }
  .breakdown-card h2 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }
  .bar-chart { display: flex; flex-direction: column; gap: 0.6rem; }
  .bar-row {
    display: grid;
    grid-template-columns: 110px 1fr 40px;
    align-items: center;
    gap: 0.75rem;
  }
  .bar-label {
    font-size: 0.8rem;
    text-transform: capitalize;
    color: var(--text-secondary);
    font-weight: 500;
    text-align: right;
  }
  .bar-track {
    height: 20px;
    background: #f1f5f9;
    border-radius: 4px;
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s;
  }
  .bar-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  @media (max-width: 900px) {
    .breakdown-row, .two-col {
      grid-template-columns: 1fr;
    }
  }
</style>
