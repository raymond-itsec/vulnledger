<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import {
    findingsApi,
    type Finding,
    type FindingHistory,
    RISK_LEVELS,
    REMEDIATION_STATUSES,
  } from '$lib/api/findings';
  import { attachmentsApi, formatFileSize, type Attachment } from '$lib/api/attachments';
  import { auth } from '$lib/stores/auth.svelte';
  import Badge from '$lib/components/Badge.svelte';
  import MarkdownEditor from '$lib/components/MarkdownEditor.svelte';
  import MarkdownView from '$lib/components/MarkdownView.svelte';

  let finding = $state<Finding | null>(null);
  let history = $state<FindingHistory[]>([]);
  let attachments = $state<Attachment[]>([]);
  let loading = $state(true);
  let editing = $state(false);
  let saving = $state(false);
  let showHistory = $state(false);
  let uploading = $state(false);
  let uploadError = $state('');

  let form = $state({
    title: '',
    description: '',
    risk_level: 'medium',
    impact: '',
    recommendation: '',
    remediation_status: 'open',
    references: '',
  });

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');

  onMount(async () => {
    const id = page.params.id!;
    try {
      const [f, h, a] = await Promise.all([
        findingsApi.get(id),
        findingsApi.history(id),
        attachmentsApi.list(id),
      ]);
      finding = f;
      history = h;
      attachments = a;
      populateForm(f);
    } finally {
      loading = false;
    }
  });

  function populateForm(f: Finding) {
    form = {
      title: f.title,
      description: f.description,
      risk_level: f.risk_level,
      impact: f.impact || '',
      recommendation: f.recommendation || '',
      remediation_status: f.remediation_status,
      references: (f.references || []).join('\n'),
    };
  }

  async function handleSave() {
    if (!finding) return;
    saving = true;
    try {
      const refs = form.references.split('\n').map((r) => r.trim()).filter(Boolean);
      finding = await findingsApi.update(finding.finding_id, {
        title: form.title,
        description: form.description,
        risk_level: form.risk_level,
        impact: form.impact || undefined,
        recommendation: form.recommendation || undefined,
        remediation_status: form.remediation_status,
        references: refs.length > 0 ? refs : undefined,
      });
      history = await findingsApi.history(finding.finding_id);
      editing = false;
    } finally {
      saving = false;
    }
  }

  async function handleFileUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !finding) return;
    uploading = true;
    uploadError = '';
    try {
      const a = await attachmentsApi.upload(finding.finding_id, file);
      attachments = [a, ...attachments];
    } catch (err: any) {
      uploadError = err.message;
    } finally {
      uploading = false;
      input.value = '';
    }
  }

  async function handleDeleteAttachment(id: string) {
    try {
      await attachmentsApi.delete(id);
      attachments = attachments.filter((a) => a.attachment_id !== id);
    } catch {
      // ignore
    }
  }

  async function handleDownloadAttachment(att: Attachment) {
    try {
      await attachmentsApi.download(att.attachment_id, att.file_name);
    } catch (err: any) {
      uploadError = err.message;
    }
  }
</script>

{#if loading}
  <p>Loading...</p>
{:else if !finding}
  <p>Finding not found.</p>
{:else}
  <div class="page-header">
    <div>
      <h1>{finding.title}</h1>
      <div style="display:flex;gap:0.5rem;margin-top:0.5rem;">
        <Badge text={finding.risk_level} variant={finding.risk_level} />
        <Badge text={finding.remediation_status} variant={finding.remediation_status} />
      </div>
    </div>
    {#if canEdit && !editing}
      <button class="btn btn-secondary" onclick={() => (editing = true)}>Edit</button>
    {/if}
  </div>

  {#if editing}
    <div class="card">
      <form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
        <div class="form-group">
          <label>Title *</label>
          <input bind:value={form.title} required />
        </div>
        <div class="form-group">
          <label>Risk Level *</label>
          <select bind:value={form.risk_level}>
            {#each RISK_LEVELS as r}
              <option value={r}>{r}</option>
            {/each}
          </select>
        </div>
        <MarkdownEditor label="Description * (Markdown)" bind:value={form.description} required minHeight="150px" />
        <MarkdownEditor label="Impact (Markdown)" bind:value={form.impact} />
        <MarkdownEditor label="Recommendation (Markdown)" bind:value={form.recommendation} />
        <div class="form-group">
          <label>Remediation Status</label>
          <select bind:value={form.remediation_status}>
            {#each REMEDIATION_STATUSES as s}
              <option value={s}>{s.replace('_', ' ')}</option>
            {/each}
          </select>
        </div>
        <div class="form-group">
          <label>References (one per line)</label>
          <textarea bind:value={form.references}></textarea>
        </div>
        <div style="display:flex;gap:0.5rem;">
          <button class="btn btn-primary" type="submit" disabled={saving}>Save</button>
          <button class="btn btn-secondary" type="button" onclick={() => { editing = false; populateForm(finding!); }}>Cancel</button>
        </div>
      </form>
    </div>
  {:else}
    <div class="card section">
      <h2>Description</h2>
      <MarkdownView content={finding.description} />
    </div>

    {#if finding.impact}
      <div class="card section">
        <h2>Impact</h2>
        <MarkdownView content={finding.impact} />
      </div>
    {/if}

    {#if finding.recommendation}
      <div class="card section">
        <h2>Recommendation</h2>
        <MarkdownView content={finding.recommendation} />
      </div>
    {/if}

    {#if finding.references && finding.references.length > 0}
      <div class="card section">
        <h2>References</h2>
        <ul class="ref-list">
          {#each finding.references as ref}
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

    <!-- Attachments -->
    <div class="card section">
      <div class="section-header">
        <h2>Attachments ({attachments.length})</h2>
        {#if canEdit}
          <label class="btn btn-sm btn-secondary upload-label">
            {uploading ? 'Uploading...' : 'Upload File'}
            <input
              type="file"
              style="display:none;"
              onchange={handleFileUpload}
              disabled={uploading}
              accept="image/*,.pdf,.txt,.md,.csv,.json,.zip"
            />
          </label>
        {/if}
      </div>
      {#if uploadError}
        <p style="color:var(--critical);font-size:0.85rem;margin-bottom:0.5rem;">{uploadError}</p>
      {/if}
      {#if attachments.length === 0}
        <p class="empty-state" style="padding:1rem;">No attachments.</p>
      {:else}
        <table>
          <thead>
            <tr><th>File Name</th><th>Type</th><th>Size</th><th>Uploaded</th><th></th></tr>
          </thead>
          <tbody>
            {#each attachments as att}
              <tr>
                <td>
                  <button
                    class="link-button"
                    type="button"
                    onclick={() => handleDownloadAttachment(att)}
                  >
                    {att.file_name}
                  </button>
                </td>
                <td>{att.content_type || '—'}</td>
                <td>{formatFileSize(att.size_bytes)}</td>
                <td>{new Date(att.uploaded_at).toLocaleString()}</td>
                <td>
                  {#if canEdit}
                    <button
                      class="btn btn-sm btn-danger"
                      onclick={() => handleDeleteAttachment(att.attachment_id)}
                    >
                      Delete
                    </button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>

    <!-- History -->
    <div class="card section">
      <h2>
        <button
          class="history-toggle"
          onclick={() => (showHistory = !showHistory)}
        >
          Change History ({history.length}) {showHistory ? '▾' : '▸'}
        </button>
      </h2>
      {#if showHistory}
        {#if history.length === 0}
          <p class="empty-state">No changes recorded yet.</p>
        {:else}
          <table>
            <thead>
              <tr><th>Date</th><th>User</th><th>Field</th><th>Old Value</th><th>New Value</th></tr>
            </thead>
            <tbody>
              {#each history as h}
                <tr>
                  <td>{new Date(h.changed_at).toLocaleString()}</td>
                  <td>{h.changed_by_name || h.changed_by}</td>
                  <td><code>{h.field_name}</code></td>
                  <td class="val-cell">{h.old_value || '—'}</td>
                  <td class="val-cell">{h.new_value || '—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      {/if}
    </div>

    <div style="margin-top:1rem;font-size:0.8rem;color:var(--text-secondary);">
      Session: <a href="/sessions/{finding.session_id}">View Session</a> &middot;
      Created: {new Date(finding.created_at).toLocaleString()} &middot;
      Updated: {new Date(finding.updated_at).toLocaleString()}
    </div>
  {/if}
{/if}

<style>
  .section { margin-bottom: 1rem; }
  .section h2 { font-size: 1rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--text-secondary); }
  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
  .section-header h2 { margin-bottom: 0; }
  .upload-label { cursor: pointer; }
  .ref-list { padding-left: 1.5rem; }
  .ref-list li { margin-bottom: 0.25rem; font-size: 0.875rem; }
  .history-toggle {
    background: none;
    border: none;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0;
  }
  .history-toggle:hover { color: var(--text-primary); }
  .val-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.8rem; }
  .link-button {
    background: none;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font: inherit;
    padding: 0;
    text-align: left;
    text-decoration: underline;
  }
</style>
