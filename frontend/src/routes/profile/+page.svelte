<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { logout, fetchMe } from '$lib/stores/auth.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import { usersApi, type User } from '$lib/api/users';
  import { authApi, type SecurityEventInfo, type SessionInfo } from '$lib/api/auth';
  // TODO: Add password and MFA controls once backend endpoints are available.

  let loading = $state(true);
  let saving = $state(false);
  let sessionsLoading = $state(true);
  let eventsLoading = $state(true);
  let revokingSessionId = $state<string | null>(null);
  let revokingAll = $state(false);

  let sessions = $state<SessionInfo[]>([]);
  let securityEvents = $state<SecurityEventInfo[]>([]);

  let username = $state('');
  let role = $state('');
  let fullName = $state('');
  let companyName = $state('');
  let email = $state('');

  function buildFieldId(name: string): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return `${name}-${crypto.randomUUID()}`;
    }
    return `${name}-${Math.random().toString(36).slice(2, 10)}`;
  }

  const fullNameFieldId = buildFieldId('profile-full-name');
  const companyNameFieldId = buildFieldId('profile-company-name');
  const emailFieldId = buildFieldId('profile-email');
  const usernameFieldId = buildFieldId('profile-username');
  const roleFieldId = buildFieldId('profile-role');

  function applyProfile(user: User): void {
    username = user.username;
    role = user.role;
    fullName = user.full_name ?? '';
    companyName = user.company_name ?? '';
    email = user.email ?? '';
  }

  function formatDateTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat('en-GB', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  }

  function timeSince(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'unknown';
    const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  function eventLabel(type: string): string {
    switch (type) {
      case 'refresh_token_reuse_detected':
        return 'Refresh token reuse detected';
      case 'refresh_session_revoked':
        return 'Session revoked';
      case 'all_refresh_sessions_revoked':
        return 'All sessions revoked';
      case 'refresh_session_family_revoked':
        return 'Session family revoked';
      default:
        return type.replaceAll('_', ' ');
    }
  }

  async function loadAuthSecurityData(): Promise<void> {
    sessionsLoading = true;
    eventsLoading = true;
    try {
      const [sessionResponse, eventResponse] = await Promise.all([
        authApi.listSessions(),
        authApi.listSecurityEvents(20),
      ]);
      sessions = sessionResponse.items;
      securityEvents = eventResponse.items;
    } catch (error: any) {
      toast.error(error?.message || 'Could not load session security data.');
    } finally {
      sessionsLoading = false;
      eventsLoading = false;
    }
  }

  onMount(async () => {
    try {
      const me = await usersApi.getMe();
      applyProfile(me);
      await loadAuthSecurityData();
    } catch (error: any) {
      toast.error(error?.message || 'Could not load profile settings.');
    } finally {
      loading = false;
    }
  });

  async function saveProfile(): Promise<void> {
    saving = true;
    try {
      const updated = await usersApi.updateMe({
        full_name: fullName.trim() || null,
        company_name: companyName.trim() || null,
        email: email.trim() || null,
      });
      applyProfile(updated);
      await fetchMe();
      toast.success('Profile updated.');
    } catch (error: any) {
      toast.error(error?.message || 'Could not save profile settings.');
    } finally {
      saving = false;
    }
  }

  async function revokeSession(session: SessionInfo): Promise<void> {
    const isCurrent = session.is_current;
    const confirmMessage = isCurrent
      ? 'Revoke the current session? You will be logged out.'
      : 'Revoke this session?';
    if (!window.confirm(confirmMessage)) return;

    revokingSessionId = session.refresh_session_id;
    try {
      await authApi.revokeSession(session.refresh_session_id);
      if (isCurrent) {
        toast.success('Current session revoked. Signing out...');
        await logout();
        await goto('/', { replaceState: true });
        return;
      }
      toast.success('Session revoked.');
      await loadAuthSecurityData();
    } catch (error: any) {
      toast.error(error?.message || 'Could not revoke session.');
    } finally {
      revokingSessionId = null;
    }
  }

  async function revokeAllSessions(): Promise<void> {
    if (!window.confirm('Log out all sessions now? This signs you out everywhere.')) return;
    revokingAll = true;
    try {
      const result = await authApi.revokeAllSessions();
      toast.success(`Revoked ${result.revoked_count} session(s). Signing out...`);
      await logout();
      await goto('/', { replaceState: true });
    } catch (error: any) {
      toast.error(error?.message || 'Could not revoke all sessions.');
    } finally {
      revokingAll = false;
    }
  }
</script>

<div class="page-header">
  <h1>Profile Settings</h1>
</div>

{#if loading}
  <p>Loading...</p>
{:else}
  <div class="card settings-card">
    <form onsubmit={(e) => { e.preventDefault(); saveProfile(); }}>
      <div class="field-grid readonly-grid">
        <div class="form-group">
          <label for={usernameFieldId}>Username</label>
          <input id={usernameFieldId} type="text" value={username} disabled />
        </div>
        <div class="form-group">
          <label for={roleFieldId}>Role</label>
          <input id={roleFieldId} type="text" value={role.replace('_', ' ')} disabled />
        </div>
      </div>

      <div class="field-grid">
        <div class="form-group">
          <label for={fullNameFieldId}>Full name</label>
          <input id={fullNameFieldId} type="text" bind:value={fullName} placeholder="Your name" />
        </div>
        <div class="form-group">
          <label for={companyNameFieldId}>Company</label>
          <input id={companyNameFieldId} type="text" bind:value={companyName} placeholder="Your company" />
        </div>
      </div>

      <div class="form-group">
        <label for={emailFieldId}>Email</label>
        <input id={emailFieldId} type="email" bind:value={email} required />
      </div>

      <div class="actions">
        <button class="btn btn-primary" type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save profile'}
        </button>
      </div>
    </form>
  </div>

  <div class="card sessions-card">
    <div class="card-header">
      <h2>Current Known Sessions</h2>
      <button class="btn btn-danger btn-sm" onclick={revokeAllSessions} disabled={revokingAll}>
        {revokingAll ? 'Revoking...' : 'Log out all sessions'}
      </button>
    </div>
    {#if sessionsLoading}
      <p>Loading sessions...</p>
    {:else if sessions.length === 0}
      <p class="empty-inline">No active refresh sessions found.</p>
    {:else}
      <div class="session-list">
        {#each sessions as session}
          <article class="session-item" class:current-session={session.is_current}>
            <div class="session-main">
              <div class="session-title-row">
                <strong>{session.is_current ? 'Current session' : 'Session'}</strong>
                {#if session.is_current}
                  <span class="badge current-pill">Current</span>
                {/if}
              </div>
              <div class="session-line">
                <span><strong>IP:</strong> {session.ip_address ?? 'Unknown'}</span>
                <span><strong>Country:</strong> {session.country}</span>
              </div>
              <div class="session-line session-user-agent">
                <strong>User-Agent:</strong> {session.user_agent ?? 'Unknown'}
              </div>
              <div class="session-line">
                <span><strong>Last seen:</strong> {timeSince(session.last_seen_at)}</span>
                <span class="session-secondary">{formatDateTime(session.last_seen_at)}</span>
              </div>
            </div>
            <div class="session-actions">
              <button
                class="btn btn-secondary btn-sm"
                onclick={() => revokeSession(session)}
                disabled={revokingAll || revokingSessionId === session.refresh_session_id}
              >
                {revokingSessionId === session.refresh_session_id ? 'Revoking...' : 'Revoke session'}
              </button>
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </div>

  <div class="card sessions-card">
    <div class="card-header">
      <h2>Security Activity</h2>
    </div>
    {#if eventsLoading}
      <p>Loading security events...</p>
    {:else if securityEvents.length === 0}
      <p class="empty-inline">No security events found.</p>
    {:else}
      <div class="event-list">
        {#each securityEvents as event}
          <article class="event-item">
            <div class="event-title">{eventLabel(event.event_type)}</div>
            <div class="event-line">
              <span><strong>When:</strong> {timeSince(event.occurred_at)}</span>
              <span class="session-secondary">{formatDateTime(event.occurred_at)}</span>
            </div>
            <div class="event-line">
              <span><strong>IP:</strong> {event.ip_address ?? 'Unknown'}</span>
              <span><strong>Session:</strong> {event.refresh_session_id ?? 'n/a'}</span>
            </div>
            <div class="event-line event-user-agent">
              <strong>User-Agent:</strong> {event.user_agent ?? 'Unknown'}
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .settings-card {
    max-width: 760px;
    margin-bottom: 1.25rem;
  }

  .sessions-card {
    max-width: 980px;
    margin-bottom: 1.25rem;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .card-header h2 {
    font-size: 1.1rem;
  }

  .field-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
  }

  .readonly-grid {
    margin-bottom: 1rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    margin-bottom: 1rem;
  }

  .form-group label {
    font-weight: 600;
    font-size: 0.875rem;
  }

  .form-group input {
    width: 100%;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }

  .empty-inline {
    color: var(--text-secondary);
  }

  .session-list,
  .event-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .session-item,
  .event-item {
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 0.875rem;
    display: flex;
    justify-content: space-between;
    gap: 0.875rem;
    flex-wrap: wrap;
  }

  .current-session {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.18);
  }

  .session-main {
    flex: 1;
    min-width: 280px;
  }

  .session-actions {
    display: flex;
    align-items: flex-start;
  }

  .session-title-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.375rem;
  }

  .session-line,
  .event-line {
    display: flex;
    gap: 0.875rem;
    flex-wrap: wrap;
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin-bottom: 0.2rem;
  }

  .session-user-agent,
  .event-user-agent {
    word-break: break-word;
  }

  .session-secondary {
    color: var(--text-secondary);
  }

  .event-title {
    font-weight: 600;
    margin-bottom: 0.25rem;
  }

  .current-pill {
    background: rgba(59, 130, 246, 0.14);
    color: var(--accent);
  }
</style>
