<script lang="ts">
  import { onMount } from 'svelte';
  import { templatesApi, type Template } from '$lib/api/templates';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import Badge from '$lib/components/Badge.svelte';
  import MarkdownView from '$lib/components/MarkdownView.svelte';
  import MarkdownEditor from '$lib/components/MarkdownEditor.svelte';
  import Modal from '$lib/components/Modal.svelte';

  let templates = $state<Template[]>([]);
  let loading = $state(true);
  let selected = $state<Template | null>(null);
  let showModal = $state(false);
  let editingTemplate = $state<Template | null>(null);
  let saving = $state(false);
  let deleteConfirm = $state('');

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const isAdmin = $derived(auth.user?.role === 'admin');
  const riskLevels = $derived(taxonomy.activeEntries('risk_level'));

  function fieldId(name: string): string {
    return `${name}-${crypto.randomUUID()}`;
  }

  const stableIdFieldId = fieldId('template-stable-id');
  const nameFieldId = fieldId('template-name');
  const categoryFieldId = fieldId('template-category');
  const titleFieldId = fieldId('template-title');
  const riskLevelFieldId = fieldId('template-risk-level');
  const referencesFieldId = fieldId('template-references');

  let form = $state({
    stable_id: '',
    name: '',
    category: '',
    title: '',
    description: '',
    risk_level: 'medium',
    impact: '',
    recommendation: '',
    references: '',
  });

  let grouped = $derived(() => {
    const groups: Record<string, Template[]> = {};
    for (const t of templates) {
      const cat = t.category || 'Uncategorized';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(t);
    }
    return groups;
  });

  onMount(async () => {
    try {
      templates = (await templatesApi.list()).items;
    } finally {
      loading = false;
    }
  });

  function resetForm() {
    form = {
      stable_id: '',
      name: '',
      category: '',
      title: '',
      description: '',
      risk_level: 'medium',
      impact: '',
      recommendation: '',
      references: '',
    };
  }

  function openCreate() {
    editingTemplate = null;
    resetForm();
    showModal = true;
  }

  function openEdit(t: Template) {
    editingTemplate = t;
    form = {
      stable_id: t.stable_id,
      name: t.name,
      category: t.category || '',
      title: t.title || '',
      description: t.description || '',
      risk_level: t.risk_level || 'medium',
      impact: t.impact || '',
      recommendation: t.recommendation || '',
      references: (t.references || []).join('\n'),
    };
    showModal = true;
  }

  async function handleSave() {
    saving = true;
    try {
      const refs = form.references.split('\n').map((r) => r.trim()).filter(Boolean);
      const payload = {
        name: form.name,
        category: form.category || undefined,
        title: form.title || undefined,
        description: form.description || undefined,
        risk_level: form.risk_level || undefined,
        impact: form.impact || undefined,
        recommendation: form.recommendation || undefined,
        references: refs.length > 0 ? refs : undefined,
      };

      if (editingTemplate) {
        const updated = await templatesApi.update(editingTemplate.template_id, payload);
        templates = templates.map((t) =>
          t.template_id === updated.template_id ? updated : t
        );
        selected = updated;
      } else {
        const created = await templatesApi.create({
          ...payload,
          stable_id: form.stable_id,
        });
        templates = [...templates, created];
        selected = created;
      }
      showModal = false;
    } finally {
      saving = false;
    }
  }

  async function handleDelete(t: Template) {
    if (deleteConfirm !== t.template_id) {
      deleteConfirm = t.template_id;
      return;
    }
    try {
      await templatesApi.delete(t.template_id);
      templates = templates.filter((x) => x.template_id !== t.template_id);
      if (selected?.template_id === t.template_id) selected = null;
      deleteConfirm = '';
    } catch {
      // ignore
    }
  }
</script>

<div class="page-header">
  <h1>Finding Templates</h1>
  {#if canEdit}
    <button class="btn btn-primary" onclick={openCreate}>New Template</button>
  {/if}
</div>

{#if loading}
  <p>Loading...</p>
{:else if templates.length === 0}
  <p class="empty-state">No templates available.</p>
{:else}
  <div class="templates-layout">
    <div class="templates-list">
      {#each Object.entries(grouped()) as [category, items]}
        <div class="category-group">
          <h3 class="category-title">{category}</h3>
          {#each items as t}
            <button
              class="template-item"
              class:active={selected?.template_id === t.template_id}
              onclick={() => (selected = t)}
            >
              <span class="template-name">{t.name}</span>
              {#if t.risk_level}
                <Badge text={t.risk_level} variant={t.risk_level} />
              {/if}
              {#if t.is_builtin}
                <span class="builtin-tag">built-in</span>
              {:else}
                <span class="custom-tag">custom</span>
              {/if}
            </button>
          {/each}
        </div>
      {/each}
    </div>

    <div class="template-detail">
      {#if selected}
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">
            <h2>{selected.name}</h2>
            {#if canEdit && (!selected.is_builtin || isAdmin)}
              <div style="display:flex;gap:0.5rem;">
                <button class="btn btn-sm btn-secondary" onclick={() => openEdit(selected!)}>Edit</button>
                {#if !selected.is_builtin}
                  <button
                    class="btn btn-sm btn-danger"
                    onclick={() => handleDelete(selected!)}
                  >
                    {deleteConfirm === selected.template_id ? 'Confirm Delete' : 'Delete'}
                  </button>
                {/if}
              </div>
            {/if}
          </div>
          {#if selected.title}
            <p style="color:var(--text-secondary);margin-bottom:1rem;font-size:0.9rem;">
              Title: <strong>{selected.title}</strong>
            </p>
          {/if}
          {#if selected.description}
            <div class="detail-section">
              <h3>Description</h3>
              <MarkdownView content={selected.description} />
            </div>
          {/if}
          {#if selected.impact}
            <div class="detail-section">
              <h3>Impact</h3>
              <MarkdownView content={selected.impact} />
            </div>
          {/if}
          {#if selected.recommendation}
            <div class="detail-section">
              <h3>Recommendation</h3>
              <MarkdownView content={selected.recommendation} />
            </div>
          {/if}
          {#if selected.references && selected.references.length > 0}
            <div class="detail-section">
              <h3>References</h3>
              <ul>
                {#each selected.references as ref}
                  <li>
                    {#if ref.startsWith('http')}
                      <a href={ref} target="_blank" rel="noopener">{ref}</a>
                    {:else}
                      {ref}
                    {/if}
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      {:else}
        <div class="card empty-state">
          Select a template to view its details.
        </div>
      {/if}
    </div>
  </div>
{/if}

<Modal title={editingTemplate ? 'Edit Template' : 'New Template'} show={showModal} onclose={() => (showModal = false)}>
  <form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
    {#if !editingTemplate}
      <div class="form-group">
        <label for={stableIdFieldId}>Stable ID *</label>
        <input id={stableIdFieldId} bind:value={form.stable_id} required placeholder="e.g. custom/my-finding-type" />
      </div>
    {/if}
    <div class="form-group">
      <label for={nameFieldId}>Name *</label>
      <input id={nameFieldId} bind:value={form.name} required placeholder="e.g. My Custom Finding" />
    </div>
    <div class="form-group">
      <label for={categoryFieldId}>Category</label>
      <input id={categoryFieldId} bind:value={form.category} placeholder="e.g. custom, injection, authentication" />
    </div>
    <div class="form-group">
      <label for={titleFieldId}>Finding Title</label>
      <input id={titleFieldId} bind:value={form.title} placeholder="Default title when applied" />
    </div>
    <div class="form-group">
      <label for={riskLevelFieldId}>Risk Level</label>
      <select id={riskLevelFieldId} bind:value={form.risk_level}>
        {#each riskLevels as r}
          <option value={r.value}>{r.label}</option>
        {/each}
      </select>
    </div>
    <MarkdownEditor label="Description (Markdown)" bind:value={form.description} />
    <MarkdownEditor label="Impact (Markdown)" bind:value={form.impact} />
    <MarkdownEditor label="Recommendation (Markdown)" bind:value={form.recommendation} />
    <div class="form-group">
      <label for={referencesFieldId}>References (one per line)</label>
      <textarea id={referencesFieldId} bind:value={form.references} placeholder="CWE-79&#10;https://owasp.org/..."></textarea>
    </div>
    <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
      <button class="btn btn-secondary" type="button" onclick={() => (showModal = false)}>Cancel</button>
      <button class="btn btn-primary" type="submit" disabled={saving}>
        {saving ? 'Saving...' : editingTemplate ? 'Save Changes' : 'Create Template'}
      </button>
    </div>
  </form>
</Modal>

<style>
  .templates-layout { display: grid; grid-template-columns: 340px 1fr; gap: 1.5rem; }
  .templates-list {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    overflow-y: auto;
    max-height: calc(100vh - 180px);
  }
  .category-group { padding: 0.5rem 0; }
  .category-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
    padding: 0.5rem 1rem;
    font-weight: 700;
  }
  .template-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 1rem;
    border: none;
    background: none;
    text-align: left;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.1s;
  }
  .template-item:hover { background: #f1f5f9; }
  .template-item.active { background: #e0e7ff; }
  .template-name { flex: 1; }
  .builtin-tag, .custom-tag {
    font-size: 0.65rem;
    padding: 0.05rem 0.35rem;
    border-radius: 0.25rem;
  }
  .builtin-tag {
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }
  .custom-tag {
    color: #2563eb;
    border: 1px solid #93c5fd;
    background: #eff6ff;
  }
  .detail-section { margin-bottom: 1.25rem; }
  .detail-section h3 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    font-weight: 600;
  }
  .template-detail h2 { font-size: 1.25rem; margin-bottom: 0; }
  .template-detail ul { padding-left: 1.5rem; font-size: 0.875rem; }
  .template-detail li { margin-bottom: 0.25rem; }
</style>
