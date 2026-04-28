<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page as pageState } from '$app/state';
  import { assetsApi, type Asset } from '$lib/api/assets';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { usersApi, type User } from '$lib/api/users';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import Badge from '$lib/components/Badge.svelte';
  import FormActions from '$lib/components/FormActions.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import { fieldId } from '$lib/util/dom';
  import { shouldOpenFromNewParam } from '$lib/util/new-param';

  let sessions = $state<Session[]>([]);
  let assets = $state<Asset[]>([]);
  let reviewers = $state<User[]>([]);
  let loading = $state(true);
  let page = $state(1);
  let pages = $state(1);
  let total = $state(0);
  let filterStatus = $state('');
  let showModal = $state(false);
  let saving = $state(false);
  let form = $state({
    asset_id: '',
    review_name: '',
    review_date: new Date().toISOString().split('T')[0],
    reviewer_id: '',
    status: 'planned',
    notes: '',
  });

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const hasAssets = $derived(assets.length > 0);
  const sessionStatuses = $derived(taxonomy.activeEntries('session_status'));

  const assetFieldId = fieldId('session-asset');
  const reviewNameFieldId = fieldId('session-review-name');
  const reviewDateFieldId = fieldId('session-review-date');
  const reviewerFieldId = fieldId('session-reviewer');
  const statusFieldId = fieldId('session-status');
  const notesFieldId = fieldId('session-notes');

  async function load(p = 1) {
    const res = await sessionsApi.list(undefined, p);
    // Client-side status filter (backend doesn't have status filter param yet)
    sessions = filterStatus ? res.items.filter((s) => s.status === filterStatus) : res.items;
    page = res.page;
    pages = res.pages;
    total = res.total;
  }

  async function loadPage() {
    loading = true;
    try {
      await load();

      if (canEdit) {
        const [assetsResult, reviewersResult] = await Promise.allSettled([
          assetsApi.list(undefined, 1, 100),
          usersApi.listReviewers(),
        ]);

        if (assetsResult.status === 'fulfilled') {
          assets = assetsResult.value.items;
        } else {
          toast.error('Could not load assets for new session creation.');
        }

        if (reviewersResult.status === 'fulfilled') {
          reviewers = reviewersResult.value.filter((u) => u.role !== 'client_user');
        } else {
          toast.error('Could not load reviewers for new session creation.');
        }
      }
    } catch {
      toast.error('Could not load review sessions.');
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    void loadPage();
  });

  async function openCreateSession() {
    if (!hasAssets) {
      toast.error('Create an asset before starting a review session.');
      await goto('/assets?new=1', { replaceState: true });
      return;
    }
    showModal = true;
  }

  let handledNewParam = $state(false);

  $effect(() => {
    const wantsNew = shouldOpenFromNewParam(pageState.url.searchParams);
    if (!wantsNew) {
      handledNewParam = false;
      return;
    }
    if (handledNewParam || loading) return;
    handledNewParam = true;
    void openCreateSession();
  });

  async function handleCreate() {
    if (!hasAssets) return;
    saving = true;
    try {
      const session = await sessionsApi.create(form);
      sessions = [session, ...sessions];
      total += 1;
      showModal = false;
      form = {
        asset_id: '',
        review_name: '',
        review_date: new Date().toISOString().split('T')[0],
        reviewer_id: '',
        status: 'planned',
        notes: '',
      };
    } catch (e: any) {
      toast.error(e.message || 'Could not create session.');
    } finally {
      saving = false;
    }
  }
</script>

<div class="page-header">
  <h1>Review Sessions</h1>
  {#if canEdit}
    <button class="btn btn-primary" onclick={() => void openCreateSession()}>New Session</button>
  {/if}
</div>

<div class="filters">
  <select bind:value={filterStatus} onchange={() => load(1)}>
    <option value="">All Statuses</option>
    {#each sessionStatuses as s}
      <option value={s.value}>{s.label}</option>
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
            <td>{session.reviewer_name || '--'}</td>
            <td><Badge text={session.status} variant={session.status} /></td>
          </tr>
        {/each}
      </tbody>
    </table>
    <Pagination {page} {pages} {total} onpage={load} />
  {/if}
</div>

<Modal title="New Review Session" show={showModal} onclose={() => (showModal = false)}>
  {#if !hasAssets}
    <p class="empty-state" style="margin-bottom:1rem;">
      Review sessions must belong to an asset. Create an asset first, then start the session from here or from that asset page.
    </p>
    <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
      <button class="btn btn-secondary" type="button" onclick={() => (showModal = false)}>Close</button>
      <a href="/assets?new=1" class="btn btn-primary" onclick={() => (showModal = false)}>Create Asset</a>
    </div>
  {:else}
    <form onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
      <div class="form-group">
        <label for={assetFieldId}>Asset *</label>
        <select id={assetFieldId} bind:value={form.asset_id} required>
          <option value="" disabled>Select asset</option>
          {#each assets as asset}
            <option value={asset.asset_id}>{asset.asset_name}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for={reviewNameFieldId}>Review Name *</label>
        <input id={reviewNameFieldId} bind:value={form.review_name} required />
      </div>
      <div class="form-group">
        <label for={reviewDateFieldId}>Date *</label>
        <input id={reviewDateFieldId} type="date" bind:value={form.review_date} required />
      </div>
      <div class="form-group">
        <label for={reviewerFieldId}>Reviewer *</label>
        <select id={reviewerFieldId} bind:value={form.reviewer_id} required>
          <option value="" disabled>Select reviewer</option>
          {#each reviewers as reviewer}
            <option value={reviewer.user_id}>{reviewer.full_name || reviewer.username}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for={statusFieldId}>Status</label>
        <select id={statusFieldId} bind:value={form.status}>
          {#each sessionStatuses as s}
            <option value={s.value}>{s.label}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for={notesFieldId}>Notes</label>
        <textarea id={notesFieldId} bind:value={form.notes}></textarea>
      </div>
      <FormActions
        {saving}
        saveLabel="Create Session"
        savingLabel="Creating..."
        oncancel={() => (showModal = false)}
      />
    </form>
  {/if}
</Modal>
