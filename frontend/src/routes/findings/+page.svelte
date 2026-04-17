<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page as pageState } from '$app/state';
  import { findingsApi, type Finding } from '$lib/api/findings';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { templatesApi, type Template } from '$lib/api/templates';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import Badge from '$lib/components/Badge.svelte';
  import MarkdownEditor from '$lib/components/MarkdownEditor.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import Pagination from '$lib/components/Pagination.svelte';

  let findings = $state<Finding[]>([]);
  let sessions = $state<Session[]>([]);
  let templates = $state<Template[]>([]);
  let loading = $state(true);
  let page = $state(1);
  let pages = $state(1);
  let total = $state(0);

  let filterRisk = $state('');
  let filterStatus = $state('');
  let searchText = $state('');
  let searchTimeout: ReturnType<typeof setTimeout>;

  let showModal = $state(false);
  let saving = $state(false);
  let form = $state({
    session_id: '',
    title: '',
    description: '',
    risk_level: 'medium',
    impact: '',
    recommendation: '',
    remediation_status: 'open',
    references: '',
  });

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const hasSessions = $derived(sessions.length > 0);
  const riskLevels = $derived(taxonomy.activeEntries('risk_level'));
  const remediationStatuses = $derived(taxonomy.activeEntries('remediation_status'));

  function fieldId(name: string): string {
    return `${name}-${crypto.randomUUID()}`;
  }

  const templateFieldId = fieldId('finding-template');
  const sessionFieldId = fieldId('finding-session');
  const titleFieldId = fieldId('finding-title');
  const riskLevelFieldId = fieldId('finding-risk-level');
  const remediationStatusFieldId = fieldId('finding-remediation-status');
  const referencesFieldId = fieldId('finding-references');

  async function loadFindings(p = 1) {
    const params: Record<string, any> = { page: p, per_page: 25 };
    if (filterRisk) params.risk_level = filterRisk;
    if (filterStatus) params.remediation_status = filterStatus;
    if (searchText) params.search = searchText;
    const res = await findingsApi.list(params);
    findings = res.items;
    page = res.page;
    pages = res.pages;
    total = res.total;
  }

  onMount(async () => {
    const params = pageState.url.searchParams;
    const sessionId = params.get('session_id');
    if (sessionId) form.session_id = sessionId;
    const urlRisk = params.get('risk_level');
    if (urlRisk) filterRisk = urlRisk;
    const urlStatus = params.get('remediation_status');
    if (urlStatus) filterStatus = urlStatus;

    try {
      const [, s, t] = await Promise.all([
        loadFindings(),
        sessionsApi.list(undefined, 1, 100),
        canEdit ? templatesApi.list() : Promise.resolve({ items: [], total: 0, page: 1, per_page: 100, pages: 0 }),
      ]);
      sessions = s.items;
      templates = t.items;
    } finally {
      loading = false;
    }
  });

  async function openCreateFinding() {
    if (!hasSessions) {
      toast.error('Create a review session before adding a finding.');
      await goto('/sessions?new=1', { replaceState: true });
      return;
    }
    showModal = true;
  }

  let handledNewParam = $state(false);

  $effect(() => {
    const params = pageState.url.searchParams;
    const sessionId = params.get('session_id');
    if (sessionId && form.session_id !== sessionId) {
      form.session_id = sessionId;
    }
    const wantsNew = params.get('new') === '1';
    if (!wantsNew) {
      handledNewParam = false;
      return;
    }
    if (handledNewParam || loading) return;
    handledNewParam = true;
    void openCreateFinding();
  });

  function onSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => loadFindings(1), 300);
  }

  function onFilterChange() {
    loadFindings(1);
  }

  function applyTemplate(templateId: string) {
    const t = templates.find((x) => x.template_id === templateId);
    if (!t) return;
    form.title = t.title || '';
    form.description = t.description || '';
    form.risk_level = t.risk_level || 'medium';
    form.impact = t.impact || '';
    form.recommendation = t.recommendation || '';
    form.references = (t.references || []).join('\n');
  }

  async function handleCreate() {
    if (!hasSessions) return;
    saving = true;
    try {
      const refs = form.references.split('\n').map((r) => r.trim()).filter(Boolean);
      await findingsApi.create({
        session_id: form.session_id,
        title: form.title,
        description: form.description,
        risk_level: form.risk_level,
        impact: form.impact || undefined,
        recommendation: form.recommendation || undefined,
        remediation_status: form.remediation_status,
        references: refs.length > 0 ? refs : undefined,
      });
      showModal = false;
      await loadFindings(page);
    } finally {
      saving = false;
    }
  }

  function sessionName(id: string): string {
    return sessions.find((s) => s.session_id === id)?.review_name || '--';
  }
</script>

<div class="page-header">
  <h1>Findings</h1>
  {#if canEdit}
    <button class="btn btn-primary" onclick={() => void openCreateFinding()}>New Finding</button>
  {/if}
</div>

<div class="filters">
  <input
    type="text"
    placeholder="Search title or description..."
    bind:value={searchText}
    oninput={onSearchInput}
    style="min-width:250px;"
  />
  <select bind:value={filterRisk} onchange={onFilterChange}>
    <option value="">All Risk Levels</option>
    {#each riskLevels as r}
      <option value={r.value}>{r.label}</option>
    {/each}
  </select>
  <select bind:value={filterStatus} onchange={onFilterChange}>
    <option value="">All Statuses</option>
    {#each remediationStatuses as s}
      <option value={s.value}>{s.label}</option>
    {/each}
  </select>
</div>

<div class="card">
  {#if loading}
    <p>Loading...</p>
  {:else if findings.length === 0}
    <p class="empty-state">No findings found.</p>
  {:else}
    <table>
      <thead>
        <tr><th>Title</th><th>Risk Level</th><th>Session</th><th>Status</th><th>Date</th></tr>
      </thead>
      <tbody>
        {#each findings as f}
          <tr>
            <td><a href="/findings/{f.finding_id}">{f.title}</a></td>
            <td><Badge text={f.risk_level} variant={f.risk_level} /></td>
            <td><a href="/sessions/{f.session_id}">{sessionName(f.session_id)}</a></td>
            <td><Badge text={f.remediation_status} variant={f.remediation_status} /></td>
            <td>{new Date(f.created_at).toLocaleDateString()}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    <Pagination {page} {pages} {total} onpage={loadFindings} />
  {/if}
</div>

<Modal title="New Finding" show={showModal} onclose={() => (showModal = false)}>
  {#if !hasSessions}
    <p class="empty-state" style="margin-bottom:1rem;">
      Findings must belong to a review session. Create a session first, then come back to add findings.
    </p>
    <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
      <button class="btn btn-secondary" type="button" onclick={() => (showModal = false)}>Close</button>
      <a href="/sessions?new=1" class="btn btn-primary" onclick={() => (showModal = false)}>Create Session</a>
    </div>
  {:else}
    <form onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
      {#if templates.length > 0}
        <div class="form-group">
          <label for={templateFieldId}>From Template (optional)</label>
          <select id={templateFieldId} onchange={(e) => applyTemplate(e.currentTarget.value)}>
            <option value="">-- Select a template --</option>
            {#each templates as t}
              <option value={t.template_id}>[{t.category}] {t.name}</option>
            {/each}
          </select>
        </div>
      {/if}
      <div class="form-group">
        <label for={sessionFieldId}>Session *</label>
        <select id={sessionFieldId} bind:value={form.session_id} required>
          <option value="" disabled>Select session</option>
          {#each sessions as s}
            <option value={s.session_id}>{s.review_name}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for={titleFieldId}>Title *</label>
        <input id={titleFieldId} bind:value={form.title} required />
      </div>
      <div class="form-group">
        <label for={riskLevelFieldId}>Risk Level *</label>
        <select id={riskLevelFieldId} bind:value={form.risk_level}>
          {#each riskLevels as r}
            <option value={r.value}>{r.label}</option>
          {/each}
        </select>
      </div>
      <MarkdownEditor label="Description * (Markdown)" bind:value={form.description} required />
      <MarkdownEditor label="Impact (Markdown)" bind:value={form.impact} />
      <MarkdownEditor label="Recommendation (Markdown)" bind:value={form.recommendation} />
      <div class="form-group">
        <label for={remediationStatusFieldId}>Remediation Status</label>
        <select id={remediationStatusFieldId} bind:value={form.remediation_status}>
          {#each remediationStatuses as s}
            <option value={s.value}>{s.label}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for={referencesFieldId}>References (one per line)</label>
        <textarea id={referencesFieldId} bind:value={form.references} placeholder="CWE-79&#10;https://owasp.org/..."></textarea>
      </div>
      <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
        <button class="btn btn-secondary" type="button" onclick={() => (showModal = false)}>Cancel</button>
        <button class="btn btn-primary" type="submit" disabled={saving}>
          {saving ? 'Creating...' : 'Create Finding'}
        </button>
      </div>
    </form>
  {/if}
</Modal>
