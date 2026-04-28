<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { sessionsApi, type Session } from '$lib/api/sessions';
  import { findingsApi, type Finding } from '$lib/api/findings';
  import { reportsApi, type ReportExport } from '$lib/api/reports';
  import { authorizedFetch } from '$lib/api/client';
  import { auth } from '$lib/stores/auth.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import Badge from '$lib/components/Badge.svelte';
  import MarkdownView from '$lib/components/MarkdownView.svelte';
  import { fieldId, downloadResponseAsFile } from '$lib/util/dom';

  let session = $state<Session | null>(null);
  let findings = $state<Finding[]>([]);
  let loading = $state(true);
  let editing = $state(false);
  let saving = $state(false);
  let exporting = $state('');
  let storedExports = $state<ReportExport[]>([]);
  let form = $state({ review_name: '', status: 'planned', notes: '' });

  const reviewNameFieldId = fieldId('session-review-name');
  const sessionStatusFieldId = fieldId('session-status');
  const sessionNotesFieldId = fieldId('session-notes');

  const canEdit = $derived(auth.user?.role === 'admin' || auth.user?.role === 'reviewer');
  const riskLevels = $derived(taxonomy.activeEntries('risk_level'));
  const sessionStatuses = $derived(taxonomy.activeEntries('session_status'));

  let riskCounts = $derived.by(() => {
    const counts: Record<string, number> = {};
    for (const f of findings) {
      counts[f.risk_level] = (counts[f.risk_level] || 0) + 1;
    }
    return counts;
  });

  onMount(async () => {
    const id = page.params.id!;
    try {
      const [s, fRes] = await Promise.all([
        sessionsApi.get(id),
        findingsApi.list({ session_id: id, per_page: 100 }),
      ]);
      session = s;
      findings = fRes.items;
      form = { review_name: s.review_name, status: s.status, notes: s.notes || '' };
      storedExports = await reportsApi.list(id);
    } catch {
      toast.error('Could not load this review session.');
    } finally {
      loading = false;
    }
  });

  async function downloadReport(format: string) {
    if (!session) return;
    exporting = format;
    try {
      const res = await authorizedFetch(`/api/reports/sessions/${session.session_id}/${format}`);
      if (!res.ok) throw new Error('Export failed');
      await downloadResponseAsFile(res, `report.${format}`);
      storedExports = await reportsApi.list(session.session_id);
    } catch {
      toast.error('Could not export this report.');
    } finally {
      exporting = '';
    }
  }

  async function downloadStoredExport(exportId: string) {
    try {
      const res = await reportsApi.downloadStored(exportId);
      if (!res.ok) throw new Error('Download failed');
      await downloadResponseAsFile(res, 'report-export');
    } catch {
      toast.error('Could not download this stored export.');
    }
  }

  function formatFileSize(sizeBytes: number) {
    if (sizeBytes < 1024) return `${sizeBytes} B`;
    if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatDateTime(value?: string | null) {
    return value ? new Date(value).toLocaleString() : '--';
  }

  function shortSha256(value?: string | null) {
    return value ? `${value.slice(0, 12)}...${value.slice(-8)}` : '--';
  }

  async function handleSave() {
    if (!session) return;
    saving = true;
    try {
      session = await sessionsApi.update(session.session_id, form);
      editing = false;
    } catch (e: any) {
      toast.error(e.message || 'Could not save session changes.');
    } finally {
      saving = false;
    }
  }
</script>

{#if loading}
  <p>Loading...</p>
{:else if !session}
  <p>Session not found.</p>
{:else}
  <div class="page-header">
    <h1>{session.review_name}</h1>
    <div style="display:flex;gap:0.5rem;">
      {#if canEdit && !editing}
        <button class="btn btn-secondary" onclick={() => (editing = true)}>Edit</button>
      {/if}
      {#if canEdit}
        <a href="/findings?new=1&session_id={session.session_id}" class="btn btn-primary">Add Finding</a>
      {/if}
    </div>
  </div>

  <div class="card" style="margin-bottom:1.5rem;">
    {#if editing}
      <form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
        <div class="form-group">
          <label for={reviewNameFieldId}>Review Name</label>
          <input id={reviewNameFieldId} bind:value={form.review_name} required />
        </div>
        <div class="form-group">
          <label for={sessionStatusFieldId}>Status</label>
          <select id={sessionStatusFieldId} bind:value={form.status}>
            {#each sessionStatuses as s}
              <option value={s.value}>{s.label}</option>
            {/each}
          </select>
        </div>
        <div class="form-group">
          <label for={sessionNotesFieldId}>Notes (Markdown)</label>
          <textarea id={sessionNotesFieldId} bind:value={form.notes}></textarea>
        </div>
        <div style="display:flex;gap:0.5rem;">
          <button class="btn btn-primary" type="submit" disabled={saving}>Save</button>
          <button class="btn btn-secondary" type="button" onclick={() => (editing = false)}>Cancel</button>
        </div>
      </form>
    {:else}
      <dl class="detail-grid">
        <dt>Date</dt><dd>{session.review_date}</dd>
        <dt>Reviewer</dt><dd>{session.reviewer_name || '--'}</dd>
        <dt>Status</dt><dd><Badge text={session.status} variant={session.status} /></dd>
        <dt>Asset</dt><dd><a href="/assets/{session.asset_id}">View Asset</a></dd>
      </dl>
      {#if session.notes}
        <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border-color);">
          <h3 style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:0.5rem;">Notes</h3>
          <MarkdownView content={session.notes} />
        </div>
      {/if}
    {/if}
  </div>

  <div class="stat-cards">
    {#each riskLevels as level}
      {@const count = riskCounts[level.value] || 0}
      {#if count > 0}
        <div class="stat-card">
          <div class="label">{level.label}</div>
          <div class="value" style="color: {level.color || '#6b7280'}">{count}</div>
        </div>
      {/if}
    {/each}
  </div>

  <div class="card" style="margin-bottom:1.5rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
      <h2 style="font-size:1.1rem;margin:0;">Export Report</h2>
    </div>
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
      <button class="btn btn-primary btn-sm" onclick={() => downloadReport('pdf')} disabled={!!exporting}>
        {exporting === 'pdf' ? 'Generating...' : 'PDF Report'}
      </button>
      <button class="btn btn-secondary btn-sm" onclick={() => downloadReport('csv')} disabled={!!exporting}>
        {exporting === 'csv' ? 'Generating...' : 'CSV Export'}
      </button>
      <button class="btn btn-secondary btn-sm" onclick={() => downloadReport('json')} disabled={!!exporting}>
        {exporting === 'json' ? 'Generating...' : 'JSON Export'}
      </button>
    </div>
    <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border-color);">
      <h3 style="font-size:0.95rem;margin:0 0 0.75rem 0;">Stored Exports</h3>
      {#if storedExports.length === 0}
        <p class="empty-state">No exports have been generated for this session yet.</p>
      {:else}
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Name</th>
              <th>Created By</th>
              <th>Size</th>
              <th>SHA256</th>
              <th>Locked Until</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each storedExports as exportItem}
              <tr>
                <td>{new Date(exportItem.exported_at).toLocaleString()}</td>
                <td>{exportItem.file_name}</td>
                <td>{exportItem.created_by_name || exportItem.created_by}</td>
                <td>{formatFileSize(exportItem.size_bytes)}</td>
                <td><code title={exportItem.sha256 || ''}>{shortSha256(exportItem.sha256)}</code></td>
                <td>{formatDateTime(exportItem.locked_until)}</td>
                <td>
                  <button
                    class="btn btn-secondary btn-sm"
                    onclick={() => downloadStoredExport(exportItem.export_id)}
                  >
                    Download
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  </div>

  <div class="card">
    <h2 style="margin-bottom:1rem;font-size:1.1rem;">Findings ({findings.length})</h2>
    {#if findings.length === 0}
      <p class="empty-state">No findings for this session yet.</p>
    {:else}
      <table>
        <thead>
          <tr><th>Title</th><th>Risk Level</th><th>Status</th></tr>
        </thead>
        <tbody>
          {#each findings as f}
            <tr>
              <td><a href="/findings/{f.finding_id}">{f.title}</a></td>
              <td><Badge text={f.risk_level} variant={f.risk_level} /></td>
              <td><Badge text={f.remediation_status} variant={f.remediation_status} /></td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
{/if}
