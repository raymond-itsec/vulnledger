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

<div class="page-header">
  <h1>Dashboard</h1>
  {#if canEdit}
    <div style="display:flex;gap:0.5rem;">
      <a href={appPath('/clients?new=1')} class="btn btn-secondary btn-sm">New Client</a>
      <a href={appPath('/findings?new=1')} class="btn btn-primary btn-sm">New Finding</a>
    </div>
  {/if}
</div>

{#if loading}
  <p>Loading...</p>
{:else}
  <div class="stat-cards">
    <a href={appPath('/clients')} class="stat-card clickable">
      <div class="label">Clients</div>
      <div class="value">{clientCount}</div>
    </a>
    <a href={appPath('/sessions')} class="stat-card clickable">
      <div class="label">Sessions</div>
      <div class="value">{sessionCount}</div>
    </a>
    <a href={appPath('/findings')} class="stat-card clickable">
      <div class="label">Total Findings</div>
      <div class="value">{findingCount}</div>
    </a>
    <a href={appPath('/findings?remediation_status=open')} class="stat-card clickable highlight">
      <div class="label">Open Findings</div>
      <div class="value">{openFindingCount}</div>
    </a>
  </div>

  <div class="breakdown-row">
    {#if Object.keys(riskBreakdown).length > 0}
      <div class="card breakdown-card">
        <h2>Findings by Risk Level</h2>
        <div class="bar-chart">
          {#each riskLevels as level}
            {#if riskBreakdown[level.value]}
              {@const count = riskBreakdown[level.value]}
              {@const pct = Math.max(8, (count / findingCount) * 100)}
              <div class="bar-row">
                <span class="bar-label">{level.label}</span>
                <div class="bar-track">
                  <div class="bar-fill" style="width:{pct}%;background:{level.color || '#6b7280'}"></div>
                </div>
                <span class="bar-value">{count}</span>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {/if}

    {#if Object.keys(statusBreakdown).length > 0}
      <div class="card breakdown-card">
        <h2>Findings by Status</h2>
        <div class="bar-chart">
          {#each remediationStatuses as s}
            {#if statusBreakdown[s.value]}
              {@const count = statusBreakdown[s.value]}
              {@const pct = Math.max(8, (count / findingCount) * 100)}
              <div class="bar-row">
                <span class="bar-label">{s.label}</span>
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
                <td><a href={appPath(`/sessions/${session.session_id}`)}>{session.review_name}</a></td>
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
                <td><a href={appPath(`/findings/${f.finding_id}`)}>{f.title}</a></td>
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
