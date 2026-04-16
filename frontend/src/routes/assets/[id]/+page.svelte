<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { assetsApi, type Asset } from '$lib/api/assets';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { usersApi, type User } from '$lib/api/users';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import Badge from '$lib/components/Badge.svelte';
  import Modal from '$lib/components/Modal.svelte';

  let asset = $state<Asset | null>(null);
  let sessions = $state<Session[]>([]);
  let reviewers = $state<User[]>([]);
  let loading = $state(true);
  let editing = $state(false);
  let form = $state({ asset_name: '', asset_type: 'web_application', description: '' });
  let saving = $state(false);

  let showSessionModal = $state(false);
  let sessionForm = $state({
    review_name: '',
    review_date: new Date().toISOString().split('T')[0],
    reviewer_id: '',
    status: 'planned',
    notes: '',
  });

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const assetTypes = $derived(taxonomy.activeEntries('asset_type'));
  const sessionStatuses = $derived(taxonomy.activeEntries('session_status'));

  onMount(async () => {
    const id = page.params.id!;
    try {
      const [a, sRes] = await Promise.all([assetsApi.get(id), sessionsApi.list(id, 1, 100)]);
      asset = a;
      sessions = sRes.items;
      form = { asset_name: a.asset_name, asset_type: a.asset_type, description: a.description || '' };
      if (canEdit) {
        try { reviewers = await usersApi.listReviewers(); } catch { /* ignore */ }
      }
    } finally {
      loading = false;
    }
  });

  async function handleSave() {
    if (!asset) return;
    saving = true;
    try {
      asset = await assetsApi.update(asset.asset_id, form);
      editing = false;
    } finally {
      saving = false;
    }
  }

  async function handleCreateSession() {
    if (!asset) return;
    saving = true;
    try {
      const s = await sessionsApi.create({ ...sessionForm, asset_id: asset.asset_id });
      sessions = [s, ...sessions];
      showSessionModal = false;
    } finally {
      saving = false;
    }
  }
</script>

{#if loading}
  <p>Loading...</p>
{:else if !asset}
  <p>Asset not found.</p>
{:else}
  <div class="page-header">
    <h1>{asset.asset_name}</h1>
    {#if canEdit && !editing}
      <button class="btn btn-secondary" onclick={() => (editing = true)}>Edit</button>
    {/if}
  </div>

  <div class="card" style="margin-bottom:1.5rem;">
    {#if editing}
      <form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
        <div class="form-group">
          <label>Asset Name</label>
          <input bind:value={form.asset_name} required />
        </div>
        <div class="form-group">
          <label>Type</label>
          <select bind:value={form.asset_type}>
            {#each assetTypes as t}
              <option value={t.value}>{t.label}</option>
            {/each}
          </select>
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea bind:value={form.description}></textarea>
        </div>
        <div style="display:flex;gap:0.5rem;">
          <button class="btn btn-primary" type="submit" disabled={saving}>Save</button>
          <button class="btn btn-secondary" type="button" onclick={() => (editing = false)}>Cancel</button>
        </div>
      </form>
    {:else}
      <dl class="detail-grid">
        <dt>Type</dt>
        <dd>{taxonomy.label('asset_type', asset!.asset_type)}</dd>
        <dt>Description</dt>
        <dd>{asset.description || '—'}</dd>
        <dt>Client</dt>
        <dd><a href="/clients/{asset.client_id}">View Client</a></dd>
      </dl>
    {/if}
  </div>

  <div class="page-header">
    <h2 style="font-size:1.2rem;">Review Sessions</h2>
    {#if canEdit}
      <button class="btn btn-primary btn-sm" onclick={() => (showSessionModal = true)}>New Session</button>
    {/if}
  </div>

  <div class="card">
    {#if sessions.length === 0}
      <p class="empty-state">No sessions for this asset yet.</p>
    {:else}
      <table>
        <thead><tr><th>Review Name</th><th>Date</th><th>Reviewer</th><th>Status</th></tr></thead>
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
    {/if}
  </div>

  <Modal title="New Review Session" show={showSessionModal} onclose={() => (showSessionModal = false)}>
    <form onsubmit={(e) => { e.preventDefault(); handleCreateSession(); }}>
      <div class="form-group">
        <label>Review Name *</label>
        <input bind:value={sessionForm.review_name} required />
      </div>
      <div class="form-group">
        <label>Date *</label>
        <input type="date" bind:value={sessionForm.review_date} required />
      </div>
      <div class="form-group">
        <label>Reviewer *</label>
        {#if reviewers.length > 0}
          <select bind:value={sessionForm.reviewer_id} required>
            <option value="" disabled>Select reviewer</option>
            {#each reviewers.filter((u) => u.role !== 'client_user') as u}
              <option value={u.user_id}>{u.full_name || u.username}</option>
            {/each}
          </select>
        {:else}
          <input bind:value={sessionForm.reviewer_id} placeholder="Reviewer user ID" required />
        {/if}
      </div>
      <div class="form-group">
        <label>Status</label>
        <select bind:value={sessionForm.status}>
          {#each sessionStatuses as s}
            <option value={s.value}>{s.label}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label>Notes</label>
        <textarea bind:value={sessionForm.notes}></textarea>
      </div>
      <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
        <button class="btn btn-secondary" type="button" onclick={() => (showSessionModal = false)}>Cancel</button>
        <button class="btn btn-primary" type="submit" disabled={saving}>Create</button>
      </div>
    </form>
  </Modal>
{/if}

<style>
  .detail-grid { display: grid; grid-template-columns: 150px 1fr; gap: 0.5rem 1rem; }
  .detail-grid dt { font-weight: 600; font-size: 0.875rem; color: var(--text-secondary); }
  .detail-grid dd { font-size: 0.875rem; }
</style>
