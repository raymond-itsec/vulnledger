<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { appAvailability } from '$lib/stores/app-availability.svelte';
  import { clientsApi } from '$lib/api/clients';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { findingsApi, type Finding } from '$lib/api/findings';
  import { appPath } from '$lib/config/routes';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import { setCrumbs, clearCrumbs } from '$lib/stores/breadcrumb.svelte';

  // ── State ──────────────────────────────────────────────────────────
  let clientCount = $state(0);
  let sessionCount = $state(0);
  let findingCount = $state(0);
  let openFindingCount = $state(0);
  let recentSessions = $state<Session[]>([]);
  let recentFindings = $state<Finding[]>([]);
  let riskBreakdown = $state<Record<string, number>>({});
  let statusBreakdown = $state<Record<string, number>>({});
  let loading = $state(true);

  // ── Derived ────────────────────────────────────────────────────────
  const riskLevels = $derived(taxonomy.activeEntries('risk_level'));
  const remediationStatuses = $derived(taxonomy.activeEntries('remediation_status'));

  const todayLabel = $derived.by(() =>
    new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    }).format(new Date()),
  );

  const greeting = $derived.by(() => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 18) return 'Good afternoon';
    return 'Good evening';
  });

  const firstName = $derived.by(() => {
    const fullName = auth.user?.full_name?.trim();
    if (fullName) return fullName.split(/\s+/)[0];
    return auth.user?.username ?? 'there';
  });

  const criticalCount = $derived(riskBreakdown.critical ?? 0);
  const resolvedCount = $derived(statusBreakdown.resolved ?? 0);

  const queueCount = $derived(
    openFindingCount + recentSessions.filter((s) => s.status !== 'completed').length,
  );
  const queueMax = $derived(Math.max(8, queueCount + 4));
  const queueProgress = $derived(Math.min(100, Math.round((queueCount / queueMax) * 100)));

  // Critical findings list — only critical, capped to 5
  const criticalFindingsList = $derived(
    recentFindings.filter((f) => f.risk_level === 'critical').slice(0, 5),
  );
  // If there are fewer than 5 critical, fill the rest with the next most-recent regardless
  const recentFindingsList = $derived.by(() => {
    if (criticalFindingsList.length >= 5) return criticalFindingsList;
    const ids = new Set(criticalFindingsList.map((f) => f.finding_id));
    const filler = recentFindings
      .filter((f) => !ids.has(f.finding_id))
      .slice(0, 5 - criticalFindingsList.length);
    return [...criticalFindingsList, ...filler];
  });

  // Project rows for the table
  const activeProjectRows = $derived.by(() =>
    recentSessions.map((session) => {
      const related = recentFindings.filter((f) => f.session_id === session.session_id);
      const critical = related.filter((f) => f.risk_level === 'critical').length;
      return {
        id: session.session_id,
        name: session.review_name,
        type: 'Security review',
        assetCount: 1,
        findingCount: related.length,
        criticalFindings: critical,
        status: session.status,
        date: session.review_date,
      };
    }),
  );

  // ── Status / risk colour helpers (from design tokens) ──────────────
  function statusChip(status: string): { bg: string; fg: string; label: string } {
    const s = (status || '').toLowerCase();
    if (s === 'completed' || s === 'resolved')
      return { bg: '#E9F8EE', fg: '#2E8A48', label: status };
    if (s === 'in_progress' || s === 'in-progress' || s === 'active')
      return { bg: '#EBF3FD', fg: '#4A7FC4', label: status.replace('_', ' ') };
    if (s === 'wrapping_up' || s === 'wrapping-up' || s === 'wrapping up')
      return { bg: '#FEF7E8', fg: '#C48B10', label: status.replace('_', ' ') };
    if (s === 'open') return { bg: '#FDEAEA', fg: '#D93B3B', label: status };
    return { bg: '#F2EDE6', fg: '#5A5A72', label: status.replace('_', ' ') };
  }

  // ── Data loading ───────────────────────────────────────────────────
  async function loadDashboard() {
    try {
      await taxonomy.load();
      const [clients, sessions, findings, openFindings, recentF] = await Promise.all([
        clientsApi.list(1, 1),
        sessionsApi.list(undefined, 1, 5),
        findingsApi.list({ page: 1, per_page: 1 }),
        findingsApi.list({ remediation_status: 'open', page: 1, per_page: 1 }),
        findingsApi.list({ page: 1, per_page: 10 }),
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
      // Aggregate failures are non-fatal — the dashboard just shows zeros.
    } finally {
      loading = false;
    }
  }

  // ── Lifecycle ──────────────────────────────────────────────────────
  onMount(() => {
    setCrumbs([{ label: 'Dashboard' }]);
    if (auth.isAuthenticated && !appAvailability.unavailable) {
      void loadDashboard();
    }
    return clearCrumbs;
  });

  $effect(() => {
    if (auth.isAuthenticated && !appAvailability.unavailable) {
      void loadDashboard();
    }
  });
</script>

{#if loading}
  <div class="loading">Loading dashboard…</div>
{:else}
  <div class="dashboard">
    <!-- Greeting -->
    <header class="greeting">
      <p class="date">{todayLabel}</p>
      <h1>
        {greeting},
        <span class="name-gradient">{firstName}.</span>
      </h1>
    </header>

    <!-- Hero row: TODAY + Queue -->
    <section class="hero-row">
      <a class="today-card" href={appPath('/findings?remediation_status=open')}>
        <span class="eyebrow">Today</span>
        <h2 class="today-headline">
          {#if criticalCount === 0}
            No critical findings open.
          {:else}
            {criticalCount} critical finding{criticalCount > 1 ? 's' : ''} need{criticalCount === 1 ? 's' : ''} your review.
          {/if}
        </h2>
        <p class="today-sub">
          {openFindingCount} open finding{openFindingCount === 1 ? '' : 's'} across {sessionCount} active project{sessionCount === 1 ? '' : 's'}.
          Current context covers {clientCount > 0 ? `${clientCount} client${clientCount === 1 ? '' : 's'}` : 'all clients'} in your workspace.
        </p>
      </a>

      <aside class="queue-card">
        <span class="eyebrow muted">Your queue</span>
        <div class="queue-value">
          <span class="queue-number">{queueCount}</span>
          <span class="queue-unit">items</span>
        </div>
        <div class="queue-bar" aria-hidden="true">
          <span style:width="{queueProgress}%"></span>
        </div>
        <p class="queue-meta">{queueProgress}% through scoped workload</p>
      </aside>
    </section>

    <!-- Stat cards -->
    <section class="stats">
      <a class="stat-card" href={appPath('/findings')}>
        <div class="stat-head">
          <span class="stat-label">Total findings</span>
          <span class="stat-icon icon-orange" aria-hidden="true">
            <!-- Duotone: soft shield body + crisp outline + alert mark. -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" fill="currentColor" fill-opacity="0.22" stroke="none"/>
              <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
              <path d="M12 8v4"/>
              <path d="M12 16h.01"/>
            </svg>
          </span>
        </div>
        <div class="stat-value">{findingCount}</div>
        <div class="stat-meta neutral">
          {openFindingCount > 0 ? `${openFindingCount} open · ${resolvedCount} resolved` : 'Clear board today'}
        </div>
      </a>

      <a class="stat-card" href={appPath('/findings?risk_level=critical')}>
        <div class="stat-head">
          <span class="stat-label">Critical open</span>
          <span class="stat-icon icon-red" aria-hidden="true">
            <!-- Duotone: soft warning triangle body + outline + bang mark. -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" fill="currentColor" fill-opacity="0.22" stroke="none"/>
              <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
              <path d="M12 9v4"/>
              <path d="M12 17h.01"/>
            </svg>
          </span>
        </div>
        <div class="stat-value">{criticalCount}</div>
        <div class="stat-meta" class:danger={criticalCount > 0} class:positive={criticalCount === 0}>
          {criticalCount > 0 ? 'Escalate and validate remediation' : 'No critical backlog'}
        </div>
      </a>

      <a class="stat-card" href={appPath('/sessions')}>
        <div class="stat-head">
          <span class="stat-label">Active projects</span>
          <span class="stat-icon icon-amber" aria-hidden="true">
            <!-- Duotone: soft folder body + outline + tab divider line. -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" fill="currentColor" fill-opacity="0.22" stroke="none"/>
              <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
              <path d="M2 10h20" opacity="0.6"/>
            </svg>
          </span>
        </div>
        <div class="stat-value">{sessionCount}</div>
        <div class="stat-meta neutral">{recentSessions.length} recently touched</div>
      </a>

      <a class="stat-card" href={appPath('/findings?remediation_status=resolved')}>
        <div class="stat-head">
          <span class="stat-label">Resolved</span>
          <span class="stat-icon icon-green" aria-hidden="true">
            <!-- Duotone: soft circle body + outline + bold check. -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.22" stroke="none"/>
              <circle cx="12" cy="12" r="10"/>
              <path d="m8 12 3 3 5-5"/>
            </svg>
          </span>
        </div>
        <div class="stat-value">{resolvedCount}</div>
        <div class="stat-meta positive">Closed findings recorded</div>
      </a>
    </section>

    <!-- Bottom row: Projects table + Critical findings -->
    <section class="bottom-row">
      <div class="panel projects-panel">
        <div class="panel-head">
          <h3>Projects</h3>
          <a class="view-all" href={appPath('/sessions')}>View all →</a>
        </div>
        {#if activeProjectRows.length === 0}
          <p class="empty">No review projects yet.</p>
        {:else}
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Type</th>
                <th>Assets</th>
                <th>Findings</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {#each activeProjectRows as row}
                {@const chip = statusChip(row.status)}
                <tr onclick={() => (window.location.href = appPath(`/sessions/${row.id}`))} tabindex="0" role="link">
                  <td class="project-name">{row.name}</td>
                  <td class="project-type">{row.type}</td>
                  <td class="num">{row.assetCount}</td>
                  <td>
                    <span class="finding-count">{row.findingCount}</span>
                    {#if row.criticalFindings > 0}
                      <span class="crit-tag">{row.criticalFindings} crit</span>
                    {/if}
                  </td>
                  <td>
                    <span class="status-chip" style:background-color={chip.bg} style:color={chip.fg}>{chip.label}</span>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>

      <div class="panel findings-panel">
        <div class="panel-head">
          <h3>Critical findings</h3>
          <a class="view-all" href={appPath('/findings?risk_level=critical')}>View all →</a>
        </div>
        {#if recentFindingsList.length === 0}
          <p class="empty">No findings yet.</p>
        {:else}
          <ul class="finding-list">
            {#each recentFindingsList as f, i (f.finding_id)}
              {@const chip = statusChip(f.remediation_status)}
              <li class:divider={i < recentFindingsList.length - 1}>
                <a class="finding-row" href={appPath(`/findings/${f.finding_id}`)}>
                  <div class="finding-text">
                    <strong>{f.title}</strong>
                    <code class="finding-id">{f.finding_id.slice(0, 8)}</code>
                  </div>
                  <span class="status-chip" style:background-color={chip.bg} style:color={chip.fg}>{chip.label}</span>
                </a>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
    </section>
  </div>
{/if}

<style>
  .loading {
    padding: 32px 4px;
    color: var(--fg2, #5a5a72);
    font-size: var(--text-sm);
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 18px;
    font-family: var(--font-sans);
    color: var(--fg1, #1e1e2e);
  }

  /* ── Greeting ───────────────────────────────────────────── */
  .greeting {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .date {
    margin: 0;
    font-size: 12px;
    font-weight: 500;
    color: #6b6560;
  }
  .greeting h1 {
    margin: 0;
    font-size: 30px;
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -0.01em;
    color: #1e1e2e;
  }
  .name-gradient {
    background: linear-gradient(90deg, #f07340 0%, #e8a82a 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
  }

  /* ── Hero row ───────────────────────────────────────────── */
  .hero-row {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 14px;
  }
  .today-card,
  .queue-card {
    border-radius: 18px;
    padding: 22px 28px;
    text-decoration: none;
    transition: transform 200ms, box-shadow 200ms;
  }
  /* TODAY card stays dark for visual hierarchy, but becomes deep-glass
     translucent so it sits within the pastel-gradient page rather than
     punching out flatly against it. */
  .today-card {
    background: rgba(30, 30, 46, 0.92);
    backdrop-filter: blur(24px) saturate(140%);
    -webkit-backdrop-filter: blur(24px) saturate(140%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #fff;
    box-shadow: 0 18px 40px rgba(20, 12, 40, 0.28), 0 36px 70px rgba(20, 12, 40, 0.18);
    display: flex;
    flex-direction: column;
    gap: 10px;
    justify-content: center;
  }
  .today-card:hover {
    transform: translateY(-1px);
    text-decoration: none;
    box-shadow: 0 24px 48px rgba(20, 12, 40, 0.34), 0 44px 80px rgba(20, 12, 40, 0.22);
  }
  .eyebrow {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.35);
  }
  .eyebrow.muted {
    color: #9f9fb8;
  }
  .today-headline {
    margin: 0;
    font-size: 22px;
    font-weight: 800;
    line-height: 1.3;
    color: #fff;
  }
  .today-sub {
    margin: 0;
    font-size: 13px;
    line-height: 1.55;
    color: rgba(255, 255, 255, 0.55);
  }

  .queue-card {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 12px 28px rgba(80, 40, 120, 0.10), 0 24px 50px rgba(80, 40, 120, 0.12);
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 20px 22px;
  }
  .queue-value {
    display: flex;
    align-items: baseline;
    gap: 6px;
  }
  .queue-number {
    font-size: 36px;
    font-weight: 800;
    line-height: 1;
    color: #1e1e2e;
  }
  .queue-unit {
    font-size: 13px;
    color: #9f9fb8;
  }
  .queue-bar {
    height: 7px;
    border-radius: 99px;
    background: rgba(0, 0, 0, 0.08);
    overflow: hidden;
  }
  .queue-bar > span {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, #f07340, #e8a82a);
    border-radius: 99px;
    transition: width 320ms cubic-bezier(0.4, 0, 0.2, 1);
  }
  .queue-meta {
    margin: 0;
    font-size: 11px;
    color: #9f9fb8;
  }

  /* ── Stat cards ─────────────────────────────────────────── */
  .stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }
  .stat-card {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 12px 28px rgba(80, 40, 120, 0.10), 0 24px 50px rgba(80, 40, 120, 0.12);
    text-decoration: none;
    color: inherit;
    transition: transform 200ms, box-shadow 200ms;
  }
  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(80, 40, 120, 0.16), 0 32px 70px rgba(80, 40, 120, 0.18);
    text-decoration: none;
  }
  .stat-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }
  .stat-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #9f9fb8;
  }
  .stat-icon {
    width: 38px;
    height: 38px;
    border-radius: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  /* No colored pill backgrounds — let the duotone icon carry the colour
     on its own. The .stat-icon container still reserves 38px of layout
     space so the head row stays balanced across cards. */
  .icon-orange { color: #f07340; }
  .icon-red { color: #d93b3b; }
  .icon-amber { color: #e8a82a; }
  .icon-green { color: #3ba85a; }
  .stat-value {
    font-size: 36px;
    font-weight: 800;
    line-height: 1;
    color: #1e1e2e;
    margin-bottom: 6px;
  }
  .stat-meta {
    font-size: 12px;
    font-weight: 500;
  }
  .stat-meta.neutral { color: #6b6560; }
  .stat-meta.positive { color: #2e8a48; }
  .stat-meta.danger { color: #d93b3b; }

  /* ── Bottom row ─────────────────────────────────────────── */
  .bottom-row {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 16px;
  }
  .panel {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 12px 28px rgba(80, 40, 120, 0.10), 0 24px 50px rgba(80, 40, 120, 0.12);
  }
  .panel-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    border-bottom: 1px solid rgba(200, 190, 178, 0.28);
  }
  .panel-head h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 700;
    color: #1e1e2e;
  }
  .view-all {
    font-size: 12px;
    font-weight: 600;
    color: #f07340;
    text-decoration: none;
  }
  .view-all:hover {
    text-decoration: underline;
  }
  .empty {
    padding: 36px 20px;
    text-align: center;
    font-size: 13px;
    color: #9f9fb8;
    margin: 0;
  }

  /* Projects table */
  .projects-panel table {
    width: 100%;
    border-collapse: collapse;
  }
  .projects-panel thead tr {
    background: rgba(242, 237, 230, 0.5);
  }
  .projects-panel th {
    padding: 9px 20px;
    text-align: left;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9f9fb8;
    border-bottom: 1px solid rgba(200, 190, 178, 0.28);
  }
  .projects-panel tbody tr {
    border-top: 1px solid rgba(200, 190, 178, 0.2);
    cursor: pointer;
    transition: background 150ms;
  }
  .projects-panel tbody tr:hover {
    background: rgba(240, 115, 64, 0.04);
  }
  .projects-panel tbody tr:focus-visible {
    background: rgba(240, 115, 64, 0.07);
    outline: 2px solid #f07340;
    outline-offset: -2px;
  }
  .projects-panel td {
    padding: 12px 20px;
    font-size: 13px;
    color: #1e1e2e;
  }
  .project-name { font-weight: 600; }
  .project-type { font-size: 12px; color: #9f9fb8; text-transform: capitalize; }
  .num { font-weight: 700; }
  .finding-count { font-weight: 700; font-size: 14px; }
  .crit-tag {
    margin-left: 6px;
    font-size: 11px;
    font-weight: 600;
    color: #d93b3b;
  }

  /* Findings list */
  .finding-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .finding-list li.divider {
    border-bottom: 1px solid rgba(200, 190, 178, 0.2);
  }
  .finding-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 11px 18px;
    text-decoration: none;
    color: inherit;
    transition: background 150ms;
  }
  .finding-row:hover {
    background: rgba(240, 115, 64, 0.04);
    text-decoration: none;
  }
  .finding-text {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
    flex: 1;
  }
  .finding-text strong {
    font-size: 13px;
    font-weight: 600;
    color: #1e1e2e;
    line-height: 1.35;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .finding-id {
    font-family: var(--font-mono, 'JetBrains Mono', monospace);
    font-size: 11px;
    color: #9f9fb8;
    background: transparent;
    padding: 0;
  }

  /* Status chip — used in both projects table and findings list */
  .status-chip {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    text-transform: capitalize;
    white-space: nowrap;
  }

  /* ── Responsive ─────────────────────────────────────────── */
  @media (max-width: 1100px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 880px) {
    .hero-row { grid-template-columns: 1fr; }
    .bottom-row { grid-template-columns: 1fr; }
    .stats { grid-template-columns: 1fr 1fr; }
    .greeting h1 { font-size: 24px; }
  }
</style>
