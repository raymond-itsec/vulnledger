<script lang="ts">
  import { onMount } from 'svelte';
  import { sessionsApi, type Session, SESSION_STATUSES } from '$lib/api/sessions';
  import Badge from '$lib/components/Badge.svelte';
  import Pagination from '$lib/components/Pagination.svelte';

  let sessions = $state<Session[]>([]);
  let loading = $state(true);
  let page = $state(1);
  let pages = $state(1);
  let total = $state(0);
  let filterStatus = $state('');

  async function load(p = 1) {
    const res = await sessionsApi.list(undefined, p);
    // Client-side status filter (backend doesn't have status filter param yet)
    sessions = filterStatus ? res.items.filter((s) => s.status === filterStatus) : res.items;
    page = res.page;
    pages = res.pages;
    total = res.total;
  }

  onMount(async () => {
    try {
      await load();
    } finally {
      loading = false;
    }
  });
</script>

<div class="page-header">
  <h1>Review Sessions</h1>
</div>

<div class="filters">
  <select bind:value={filterStatus} onchange={() => load(1)}>
    <option value="">All Statuses</option>
    {#each SESSION_STATUSES as s}
      <option value={s}>{s.replace('_', ' ')}</option>
    {/each}
  </select>
</div>

<div class="card">
  {#if loading}
    <p>Loading...</p>
  {:else if sessions.length === 0}
    <p class="empty-state">No sessions found.</p>
  {:else}
    <table>
      <thead>
        <tr><th>Review Name</th><th>Date</th><th>Reviewer</th><th>Status</th></tr>
      </thead>
      <tbody>
        {#each sessions as session}
          <tr>
            <td><a href="/sessions/{session.session_id}">{session.review_name}</a></td>
            <td>{session.review_date}</td>
            <td>{session.reviewer_name || '—'}</td>
            <td><Badge text={session.status} variant={session.status} /></td>
          </tr>
        {/each}
      </tbody>
    </table>
    <Pagination {page} {pages} {total} onpage={load} />
  {/if}
</div>
