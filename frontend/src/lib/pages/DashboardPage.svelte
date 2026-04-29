<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { appAvailability } from '$lib/stores/app-availability.svelte';
  import { clientsApi } from '$lib/api/clients';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { findingsApi, type Finding } from '$lib/api/findings';
  import { appPath } from '$lib/config/routes';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import Badge from '$lib/components/Badge.svelte';

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
  const riskLevels = $derived(taxonomy.activeEntries('risk_level'));
  const remediationStatuses = $derived(taxonomy.activeEntries('remediation_status'));
  const todayLabel = $derived.by(() =>
    new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    }).format(new Date())
  );
  const firstName = $derived.by(() => {
    const fullName = auth.user?.full_name?.trim();
    if (fullName) return fullName.split(/\s+/)[0];
    return auth.user?.username ?? 'there';
  });
  const criticalCount = $derived(riskBreakdown.critical ?? 0);
  const resolvedCount = $derived(statusBreakdown.resolved ?? 0);
  const queueCount = $derived(openFindingCount + recentSessions.filter((session) => session.status !== 'completed').length);
  const queueMax = $derived(Math.max(8, queueCount + 4));
  const queueProgress = $derived(Math.min(100, Math.round((queueCount / queueMax) * 100)));
  const activeProjectRows = $derived.by(() =>
    recentSessions.map((session) => {
      const relatedFindings = recentFindings.filter((finding) => finding.session_id === session.session_id);
      const criticalFindings = relatedFindings.filter((finding) => finding.risk_level === 'critical').length;
      return {
        id: session.session_id,
        name: session.review_name,
        type: 'Security Review',
        assetCount: 1,
        findingCount: relatedFindings.length,
        criticalFindings,
        status: session.status,
        date: session.review_date,
      };
    })
  );

  async function loadDashboard() {
    try {
      await taxonomy.load();
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

      const risk: Record<string, number> = {};
      const status: Record<string, number> = {};
      for (const level of riskLevels) {
        const r = await findingsApi.list({ risk_level: level.value, page: 1, per_page: 1 });
        if (r.total > 0) risk[level.value] = r.total;
      }
      for (const s of remediationStatuses) {
        const r = await findingsApi.list({ remediation_status: s.value, page: 1, per_page: 1 });
        if (r.total > 0) status[s.value] = r.total;
      }
      riskBreakdown = risk;
      statusBreakdown = status;
    } catch {
      // Ignore dashboard aggregate failures.
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    if (auth.isAuthenticated && !appAvailability.unavailable) {
      await loadDashboard();
    }
  });

  $effect(() => {
    if (auth.isAuthenticated && !appAvailability.unavailable) {
      void loadDashboard();
    }
  });
</script>

{#if loading}
  <div class="dashboard-loading">Loading dashboard…</div>
{:else}
  <section class="dashboard-shell">
    <header class="hero-head">
      <div class="hero-copy">
        <p class="hero-date">{todayLabel}</p>
        <h1>Good afternoon, <span>{firstName}.</span></h1>
      </div>
    </header>

    <section class="hero-grid">
      <a href={appPath('/findings?remediation_status=open')} class="focus-card">
        <span class="eyebrow">Today</span>
        <h2>{criticalCount > 0 ? `${criticalCount} critical findings need your review.` : 'Your security queue is under control.'}</h2>
        <p>
          {openFindingCount} open findings across {sessionCount} active review sessions.
          Current context covers all clients in your workspace.
        </p>
      </a>

      <aside class="queue-card">
        <span class="eyebrow">Your queue</span>
        <div class="queue-value">{queueCount} <span>items</span></div>
        <div class="queue-bar" aria-hidden="true">
          <span style={`width:${queueProgress}%`}></span>
        </div>
        <p>{queueProgress}% through scoped workload</p>
      </aside>
    </section>

    <section class="metric-grid">
      <a href={appPath('/findings')} class="metric-card">
        <div class="metric-top">
          <span class="metric-label">Total findings</span>
          <span class="metric-icon peach">⌖</span>
        </div>
        <div class="metric-value">{findingCount}</div>
        <div class="metric-note positive">{openFindingCount > 0 ? `${openFindingCount} still need attention` : 'Clear board today'}</div>
      </a>
      <a href={appPath('/findings?risk_level=critical')} class="metric-card">
        <div class="metric-top">
          <span class="metric-label">Critical open</span>
          <span class="metric-icon blush">△</span>
        </div>
        <div class="metric-value">{criticalCount}</div>
        <div class="metric-note danger">{criticalCount > 0 ? 'Escalate and validate remediation' : 'No critical backlog'}</div>
      </a>
      <a href={appPath('/sessions')} class="metric-card">
        <div class="metric-top">
          <span class="metric-label">Active projects</span>
          <span class="metric-icon amber">□</span>
        </div>
        <div class="metric-value">{sessionCount}</div>
        <div class="metric-note warm">{recentSessions.length} recently touched</div>
      </a>
      <a href={appPath('/findings?remediation_status=resolved')} class="metric-card">
        <div class="metric-top">
          <span class="metric-label">Resolved</span>
          <span class="metric-icon mint">✓</span>
        </div>
        <div class="metric-value">{resolvedCount}</div>
        <div class="metric-note positive">Closed findings recorded</div>
      </a>
    </section>

    <section class="dashboard-panels">
      <div class="panel panel-wide">
        <div class="panel-header">
          <h2>Projects</h2>
          <a href={appPath('/sessions')}>View all →</a>
        </div>
        {#if activeProjectRows.length === 0}
          <p class="empty-state">No review sessions yet.</p>
        {:else}
          <div class="project-table">
            <div class="project-head">
              <span>Project</span>
              <span>Type</span>
              <span>Assets</span>
              <span>Findings</span>
              <span>Status</span>
            </div>
            {#each activeProjectRows as row}
              <a class="project-row" href={appPath(`/sessions/${row.id}`)}>
                <div class="project-main">
                  <strong>{row.name}</strong>
                  <small>{row.date}</small>
                </div>
                <span class="project-type">{row.type}</span>
                <span>{row.assetCount}</span>
                <span class="finding-cell">
                  {row.findingCount}
                  {#if row.criticalFindings > 0}
                    <small>{row.criticalFindings} crit</small>
                  {/if}
                </span>
                <span><Badge text={row.status} variant={row.status} /></span>
              </a>
            {/each}
          </div>
        {/if}
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2>Critical findings</h2>
          <a href={appPath('/findings?risk_level=critical')}>View all →</a>
        </div>
        {#if recentFindings.length === 0}
          <p class="empty-state">No findings yet.</p>
        {:else}
          <div class="finding-list">
            {#each recentFindings as finding}
              <a class="finding-item" href={appPath(`/findings/${finding.finding_id}`)}>
                <div class="finding-copy">
                  <strong>{finding.title}</strong>
                  <small>{finding.stable_id || finding.finding_id}</small>
                </div>
                <Badge text={finding.remediation_status} variant={finding.remediation_status} />
              </a>
            {/each}
          </div>
        {/if}
      </div>
    </section>
  </section>
{/if}

<style>
  .dashboard-loading {
    color: var(--text-secondary);
    padding: 1rem 0;
  }
  .dashboard-shell {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }
  .hero-date {
    font-size: 0.92rem;
    color: #7d728f;
    margin-bottom: 0.35rem;
  }
  .hero-copy h1 {
    font-size: clamp(2rem, 3.8vw, 3rem);
    line-height: 1.05;
    letter-spacing: -0.04em;
    color: #26243a;
  }
  .hero-copy h1 span {
    color: #f48f33;
  }
  .hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 1rem;
    align-items: stretch;
  }
  .focus-card,
  .queue-card,
  .metric-card,
  .panel {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.85);
    border-radius: 22px;
    box-shadow: 0 18px 40px rgba(80, 40, 120, 0.12), 0 36px 70px rgba(80, 40, 120, 0.14);
    backdrop-filter: blur(24px) saturate(150%);
  }
  .focus-card {
    padding: 1.7rem 1.8rem;
    min-height: 170px;
    background: #242236;
    color: rgba(255, 255, 255, 0.95);
    text-decoration: none;
  }
  .focus-card:hover {
    text-decoration: none;
  }
  .focus-card .eyebrow,
  .queue-card .eyebrow,
  .metric-label {
    display: inline-block;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }
  .focus-card .eyebrow {
    color: rgba(198, 193, 225, 0.7);
    margin-bottom: 0.9rem;
  }
  .focus-card h2 {
    font-size: clamp(1.65rem, 2.4vw, 2.2rem);
    line-height: 1.12;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
  }
  .focus-card p {
    color: rgba(206, 204, 220, 0.72);
    line-height: 1.6;
  }
  .queue-card {
    padding: 1.3rem 1.35rem;
  }
  .queue-card .eyebrow {
    color: #a6a0c4;
    margin-bottom: 0.8rem;
  }
  .queue-value {
    font-size: 3rem;
    line-height: 1;
    font-weight: 800;
    color: #26243a;
    margin-bottom: 0.9rem;
  }
  .queue-value span {
    font-size: 1rem;
    font-weight: 500;
    color: #9a95b3;
  }
  .queue-bar {
    height: 8px;
    border-radius: 999px;
    background: rgba(170, 162, 193, 0.28);
    overflow: hidden;
    margin-bottom: 0.6rem;
  }
  .queue-bar span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(135deg, #ff8f3a 0%, #f6b248 100%);
  }
  .queue-card p {
    color: #aaa2c3;
    font-size: 0.84rem;
  }
  .metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.9rem;
  }
  .metric-card {
    padding: 1.15rem 1.25rem 1rem;
    text-decoration: none;
    color: inherit;
  }
  .metric-card:hover {
    text-decoration: none;
    transform: translateY(-1px);
  }
  .metric-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .metric-label {
    color: #9b95ba;
  }
  .metric-icon {
    width: 34px;
    height: 34px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    font-weight: 700;
  }
  .metric-icon.peach { background: rgba(255, 238, 232, 0.95); color: #f38a3a; }
  .metric-icon.blush { background: rgba(255, 236, 238, 0.95); color: #ff6e61; }
  .metric-icon.amber { background: rgba(255, 246, 223, 0.95); color: #d59a12; }
  .metric-icon.mint { background: rgba(229, 250, 238, 0.95); color: #2aa15d; }
  .metric-value {
    font-size: 3rem;
    line-height: 1;
    font-weight: 800;
    color: #26243a;
    margin-bottom: 0.45rem;
  }
  .metric-note {
    font-size: 0.88rem;
  }
  .metric-note.positive { color: #2c9b60; }
  .metric-note.danger { color: #e1564d; }
  .metric-note.warm { color: #d08922; }
  .dashboard-panels {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 315px;
    gap: 1rem;
  }
  .panel {
    padding: 0;
    overflow: hidden;
  }
  .panel-wide {
    min-width: 0;
  }
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(220, 214, 236, 0.78);
  }
  .panel-header h2 {
    font-size: 1.45rem;
    letter-spacing: -0.03em;
    color: #26243a;
  }
  .panel-header a {
    color: #ff7d35;
    font-weight: 600;
  }
  .project-table {
    display: flex;
    flex-direction: column;
  }
  .project-head,
  .project-row {
    display: grid;
    grid-template-columns: minmax(220px, 1.8fr) minmax(120px, 1fr) 88px 120px 130px;
    gap: 0.75rem;
    align-items: center;
    padding: 0.95rem 1.25rem;
  }
  .project-head {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: #aaa2c3;
  }
  .project-row {
    color: #26243a;
    text-decoration: none;
    border-top: 1px solid rgba(228, 222, 240, 0.72);
  }
  .project-row:hover {
    text-decoration: none;
    background: rgba(255, 255, 255, 0.36);
  }
  .project-main {
    display: flex;
    flex-direction: column;
    gap: 0.18rem;
  }
  .project-main strong {
    font-size: 1rem;
  }
  .project-main small,
  .project-type {
    color: #9a95b3;
  }
  .finding-cell {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-weight: 700;
  }
  .finding-cell small {
    color: #e1564d;
    font-weight: 600;
  }
  .finding-list {
    display: flex;
    flex-direction: column;
  }
  .finding-item {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.9rem;
    padding: 1rem 1.25rem;
    border-top: 1px solid rgba(228, 222, 240, 0.72);
    color: #26243a;
    text-decoration: none;
  }
  .finding-item:hover {
    text-decoration: none;
    background: rgba(255, 255, 255, 0.36);
  }
  .finding-copy {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .finding-copy strong {
    line-height: 1.35;
  }
  .finding-copy small {
    color: #9a95b3;
  }
  @media (max-width: 1280px) {
    .metric-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .dashboard-panels {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 1080px) {
    .hero-grid {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 860px) {
    .metric-grid {
      grid-template-columns: 1fr;
    }
    .project-head {
      display: none;
    }
    .project-row {
      grid-template-columns: 1fr;
      gap: 0.45rem;
    }
  }
</style>
