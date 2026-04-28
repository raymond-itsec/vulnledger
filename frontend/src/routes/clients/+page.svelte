<script lang="ts">
  import { onMount } from 'svelte';
  import { page as pageState } from '$app/state';
  import { clientsApi, type Client } from '$lib/api/clients';
  import { auth } from '$lib/stores/auth.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import FormActions from '$lib/components/FormActions.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import { fieldId } from '$lib/util/dom';
  import { shouldOpenFromNewParam } from '$lib/util/new-param';

  let clients = $state<Client[]>([]);
  let loading = $state(true);
  let page = $state(1);
  let pages = $state(1);
  let total = $state(0);
  let showModal = $state(false);
  let form = $state({ company_name: '', primary_contact_name: '', primary_contact_email: '' });
  let saving = $state(false);

  const companyNameFieldId = fieldId('client-company-name');
  const contactNameFieldId = fieldId('client-contact-name');
  const contactEmailFieldId = fieldId('client-contact-email');

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');

  async function load(p = 1) {
    loading = true;
    try {
      const res = await clientsApi.list(p);
      clients = res.items;
      page = res.page;
      pages = res.pages;
      total = res.total;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    if (shouldOpenFromNewParam(pageState.url.searchParams)) {
      showModal = true;
    }
    load();
  });

  async function handleCreate() {
    saving = true;
    try {
      await clientsApi.create(form);
      showModal = false;
      form = { company_name: '', primary_contact_name: '', primary_contact_email: '' };
      await load(page);
    } catch (e: any) {
      toast.error(e.message || 'Could not create client.');
    } finally {
      saving = false;
    }
  }
</script>

<div class="page-header">
  <h1>Clients</h1>
  {#if canEdit}
    <button class="btn btn-primary" onclick={() => (showModal = true)}>New Client</button>
  {/if}
</div>

<div class="card">
  {#if loading}
    <p>Loading...</p>
  {:else if clients.length === 0}
    <p class="empty-state">No clients yet. Create one to get started.</p>
  {:else}
    <table>
      <thead>
        <tr>
          <th>Company Name</th>
          <th>Primary Contact</th>
          <th>Email</th>
        </tr>
      </thead>
      <tbody>
        {#each clients as client}
          <tr>
            <td><a href="/clients/{client.client_id}">{client.company_name}</a></td>
            <td>{client.primary_contact_name || '--'}</td>
            <td>{client.primary_contact_email || '--'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    <Pagination {page} {pages} {total} onpage={load} />
  {/if}
</div>

<Modal title="New Client" show={showModal} onclose={() => (showModal = false)}>
  <form onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
    <div class="form-group">
      <label for={companyNameFieldId}>Company Name *</label>
      <input id={companyNameFieldId} bind:value={form.company_name} required />
    </div>
    <div class="form-group">
      <label for={contactNameFieldId}>Primary Contact Name</label>
      <input id={contactNameFieldId} bind:value={form.primary_contact_name} />
    </div>
    <div class="form-group">
      <label for={contactEmailFieldId}>Primary Contact Email</label>
      <input id={contactEmailFieldId} type="email" bind:value={form.primary_contact_email} />
    </div>
    <FormActions
      {saving}
      saveLabel="Create Client"
      savingLabel="Creating..."
      oncancel={() => (showModal = false)}
    />
  </form>
</Modal>
