<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page as pageState } from '$app/state';
  import { assetsApi, type Asset } from '$lib/api/assets';
  import { clientsApi, type Client } from '$lib/api/clients';
  import { handleFormError } from '$lib/api/errors';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import FieldError from '$lib/components/FieldError.svelte';
  import FormActions from '$lib/components/FormActions.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import { fieldId } from '$lib/util/dom';
  import { shouldOpenFromNewParam } from '$lib/util/new-param';

  let assets = $state<Asset[]>([]);
  let clients = $state<Client[]>([]);
  let loading = $state(true);
  let page = $state(1);
  let pages = $state(1);
  let total = $state(0);
  let filterClient = $state('');
  let showModal = $state(false);
  let form = $state({ client_id: '', asset_name: '', asset_type: 'web_application', description: '' });
  let saving = $state(false);
  let fieldErrors = $state<Record<string, string>>({});
  const assetTypes = $derived(taxonomy.activeEntries('asset_type'));

  const clientFieldId = fieldId('asset-client');
  const assetNameFieldId = fieldId('asset-name');
  const assetTypeFieldId = fieldId('asset-type');
  const assetDescriptionFieldId = fieldId('asset-description');

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const hasClients = $derived(clients.length > 0);

  async function load(p = 1) {
    const res = await assetsApi.list(filterClient || undefined, p);
    assets = res.items;
    page = res.page;
    pages = res.pages;
    total = res.total;
  }

  onMount(async () => {
    try {
      const [, c] = await Promise.all([load(), clientsApi.list(1, 100)]);
      clients = c.items;
    } finally {
      loading = false;
    }
  });

  async function openCreateAsset() {
    if (!hasClients) {
      toast.error('Create a client before adding an asset.');
      await goto('/app/clients?new=1', { replaceState: true });
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
    void openCreateAsset();
  });

  function clientName(id: string): string {
    return clients.find((c) => c.client_id === id)?.company_name || '--';
  }

  async function handleCreate() {
    saving = true;
    try {
      await assetsApi.create(form);
      showModal = false;
      form = { client_id: '', asset_name: '', asset_type: 'web_application', description: '' };
      fieldErrors = {};
      await load(page);
    } catch (e) {
      handleFormError(e, {
        setFieldErrors: (m) => (fieldErrors = m),
        onToast: toast.error,
        fallback: 'Could not create asset.',
      });
    } finally {
      saving = false;
    }
  }
</script>

<div class="page-header">
  <h1>Reviewed Assets</h1>
  {#if canEdit}
    <button class="btn btn-primary" onclick={() => void openCreateAsset()}>New Asset</button>
  {/if}
</div>

<div class="filters">
  <select bind:value={filterClient} onchange={() => load(1)}>
    <option value="">All Clients</option>
    {#each clients as c}
      <option value={c.client_id}>{c.company_name}</option>
    {/each}
  </select>
</div>

<div class="card">
  {#if loading}
    <p>Loading...</p>
  {:else if assets.length === 0}
    <p class="empty-state">No assets found.</p>
  {:else}
    <table>
      <thead>
        <tr><th>Asset Name</th><th>Type</th><th>Client</th><th>Description</th></tr>
      </thead>
      <tbody>
        {#each assets as asset}
          <tr>
            <td><a href="/app/assets/{asset.asset_id}">{asset.asset_name}</a></td>
            <td>{taxonomy.label('asset_type', asset.asset_type)}</td>
            <td><a href="/app/clients/{asset.client_id}">{clientName(asset.client_id)}</a></td>
            <td>{asset.description || '--'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    <Pagination {page} {pages} {total} onpage={load} />
  {/if}
</div>

<Modal title="New Asset" show={showModal} onclose={() => (showModal = false)}>
  <form onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
    <div class="form-group">
      <label for={clientFieldId}>Client *</label>
      <select id={clientFieldId} bind:value={form.client_id} required aria-invalid={!!fieldErrors.client_id}>
        <option value="" disabled>Select client</option>
        {#each clients as c}
          <option value={c.client_id}>{c.company_name}</option>
        {/each}
      </select>
      <FieldError message={fieldErrors.client_id} />
    </div>
    <div class="form-group">
      <label for={assetNameFieldId}>Asset Name *</label>
      <input id={assetNameFieldId} bind:value={form.asset_name} required aria-invalid={!!fieldErrors.asset_name} />
      <FieldError message={fieldErrors.asset_name} />
    </div>
    <div class="form-group">
      <label for={assetTypeFieldId}>Type</label>
      <select id={assetTypeFieldId} bind:value={form.asset_type} aria-invalid={!!fieldErrors.asset_type}>
        {#each assetTypes as t}
          <option value={t.value}>{t.label}</option>
        {/each}
      </select>
      <FieldError message={fieldErrors.asset_type} />
    </div>
    <div class="form-group">
      <label for={assetDescriptionFieldId}>Description</label>
      <textarea id={assetDescriptionFieldId} bind:value={form.description} aria-invalid={!!fieldErrors.description}></textarea>
      <FieldError message={fieldErrors.description} />
    </div>
    <FormActions {saving} saveLabel="Create" savingLabel="Creating..." oncancel={() => (showModal = false)} />
  </form>
</Modal>
