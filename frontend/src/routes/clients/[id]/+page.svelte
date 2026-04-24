<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { clientsApi, type Client } from '$lib/api/clients';
  import { assetsApi, type Asset } from '$lib/api/assets';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { fieldId } from '$lib/util/dom';

  let client = $state<Client | null>(null);
  let assets = $state<Asset[]>([]);
  let loading = $state(true);
  let editing = $state(false);
  let form = $state({ company_name: '', primary_contact_name: '', primary_contact_email: '' });
  let saving = $state(false);

  let showAssetModal = $state(false);
  let assetForm = $state({ asset_name: '', asset_type: 'web_application', description: '' });

  const companyNameFieldId = fieldId('client-company-name');
  const primaryContactFieldId = fieldId('client-primary-contact');
  const emailFieldId = fieldId('client-email');
  const assetNameFieldId = fieldId('client-asset-name');
  const assetTypeFieldId = fieldId('client-asset-type');
  const assetDescriptionFieldId = fieldId('client-asset-description');

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const assetTypes = $derived(taxonomy.activeEntries('asset_type'));

  onMount(async () => {
    const id = page.params.id!;
    try {
      const [c, aRes] = await Promise.all([clientsApi.get(id), assetsApi.list(id, 1, 100)]);
      client = c;
      assets = aRes.items;
      form = {
        company_name: c.company_name,
        primary_contact_name: c.primary_contact_name || '',
        primary_contact_email: c.primary_contact_email || '',
      };
    } finally {
      loading = false;
    }
  });

  async function handleSave() {
    if (!client) return;
    saving = true;
    try {
      client = await clientsApi.update(client.client_id, form);
      editing = false;
    } finally {
      saving = false;
    }
  }

  async function handleCreateAsset() {
    if (!client) return;
    saving = true;
    try {
      const a = await assetsApi.create({ ...assetForm, client_id: client.client_id });
      assets = [...assets, a];
      showAssetModal = false;
      assetForm = { asset_name: '', asset_type: 'web_application', description: '' };
    } finally {
      saving = false;
    }
  }
</script>

{#if loading}
  <p>Loading...</p>
{:else if !client}
  <p>Client not found.</p>
{:else}
  <div class="page-header">
    <h1>{client.company_name}</h1>
    {#if canEdit && !editing}
      <button class="btn btn-secondary" onclick={() => (editing = true)}>Edit</button>
    {/if}
  </div>

  <div class="card" style="margin-bottom:1.5rem;">
    {#if editing}
      <form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
        <div class="form-group">
          <label for={companyNameFieldId}>Company Name</label>
          <input id={companyNameFieldId} bind:value={form.company_name} required />
        </div>
        <div class="form-group">
          <label for={primaryContactFieldId}>Primary Contact</label>
          <input id={primaryContactFieldId} bind:value={form.primary_contact_name} />
        </div>
        <div class="form-group">
          <label for={emailFieldId}>Email</label>
          <input id={emailFieldId} type="email" bind:value={form.primary_contact_email} />
        </div>
        <div style="display:flex;gap:0.5rem;">
          <button class="btn btn-primary" type="submit" disabled={saving}>Save</button>
          <button class="btn btn-secondary" type="button" onclick={() => (editing = false)}>Cancel</button>
        </div>
      </form>
    {:else}
      <dl class="detail-grid">
        <dt>Primary Contact</dt>
        <dd>{client.primary_contact_name || '--'}</dd>
        <dt>Email</dt>
        <dd>{client.primary_contact_email || '--'}</dd>
        <dt>Created</dt>
        <dd>{new Date(client.created_at).toLocaleDateString()}</dd>
      </dl>
    {/if}
  </div>

  <div class="page-header">
    <h2 style="font-size:1.2rem;">Reviewed Assets</h2>
    {#if canEdit}
      <button class="btn btn-primary btn-sm" onclick={() => (showAssetModal = true)}>Add Asset</button>
    {/if}
  </div>

  <div class="card">
    {#if assets.length === 0}
      <p class="empty-state">No assets for this client yet.</p>
    {:else}
      <table>
        <thead><tr><th>Asset Name</th><th>Type</th><th>Description</th></tr></thead>
        <tbody>
          {#each assets as asset}
            <tr>
              <td><a href="/assets/{asset.asset_id}">{asset.asset_name}</a></td>
              <td>{taxonomy.label('asset_type', asset.asset_type)}</td>
              <td>{asset.description || '--'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  <Modal title="New Asset" show={showAssetModal} onclose={() => (showAssetModal = false)}>
    <form onsubmit={(e) => { e.preventDefault(); handleCreateAsset(); }}>
      <div class="form-group">
        <label for={assetNameFieldId}>Asset Name *</label>
        <input id={assetNameFieldId} bind:value={assetForm.asset_name} required />
      </div>
      <div class="form-group">
        <label for={assetTypeFieldId}>Type</label>
        <select id={assetTypeFieldId} bind:value={assetForm.asset_type}>
          {#each assetTypes as t}
            <option value={t.value}>{t.label}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for={assetDescriptionFieldId}>Description</label>
        <textarea id={assetDescriptionFieldId} bind:value={assetForm.description}></textarea>
      </div>
      <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
        <button class="btn btn-secondary" type="button" onclick={() => (showAssetModal = false)}>Cancel</button>
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
