<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { usersApi, type User } from '$lib/api/users';
  import { invitesApi, type Invite } from '$lib/api/invites';
  import { toast } from '$lib/stores/toast.svelte';

  let loading = $state(true);
  let users = $state<User[]>([]);
  let totalUsers = $state(0);
  let invites = $state<Invite[]>([]);
  let invitesLoading = $state(true);
  let creatingInvite = $state(false);
  let revokingInviteId = $state<string | null>(null);
  let inviteEmail = $state('');

  const isAdmin = $derived(auth.user?.role === 'admin');

  function formatDateTime(value: string | null): string {
    if (!value) return 'Never';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat('en-GB', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(parsed);
  }

  function inviteStatus(invite: Invite): string {
    if (invite.revoked_at) return 'Revoked';
    if (invite.claimed_at) return 'Claimed';
    if (invite.expires_at && new Date(invite.expires_at).getTime() <= Date.now()) return 'Expired';
    return 'Active';
  }

  async function loadInvites(): Promise<void> {
    invitesLoading = true;
    try {
      const data = await invitesApi.list(1, 20);
      invites = data.items;
    } catch (error: any) {
      toast.error(error?.message || 'Could not load invites.');
    } finally {
      invitesLoading = false;
    }
  }

  onMount(async () => {
    if (!isAdmin) {
      loading = false;
      return;
    }

    try {
      const [data] = await Promise.all([
        usersApi.list(1, 10),
        loadInvites(),
      ]);
      users = data.items;
      totalUsers = data.total;
    } catch (error: any) {
      toast.error(error?.message || 'Could not load admin data.');
    } finally {
      loading = false;
    }
  });

  async function createInvite(): Promise<void> {
    const normalizedEmail = inviteEmail.trim();
    if (!normalizedEmail) {
      toast.error('Enter an email address.');
      return;
    }

    creatingInvite = true;
    try {
      const invite = await invitesApi.create({ email: normalizedEmail });
      inviteEmail = '';
      toast.success(`Invite created for ${invite.email}.`);
      await loadInvites();
    } catch (error: any) {
      toast.error(error?.message || 'Could not create invite.');
    } finally {
      creatingInvite = false;
    }
  }

  async function revokeInvite(invite: Invite): Promise<void> {
    if (!window.confirm(`Revoke invite for ${invite.email}?`)) return;
    revokingInviteId = invite.invite_id;
    try {
      await invitesApi.revoke(invite.invite_id);
      toast.success('Invite revoked.');
      await loadInvites();
    } catch (error: any) {
      toast.error(error?.message || 'Could not revoke invite.');
    } finally {
      revokingInviteId = null;
    }
  }
</script>

<div class="page-header">
  <h1>Admin</h1>
</div>

{#if loading}
  <p>Loading...</p>
{:else if !isAdmin}
  <div class="card">
    <h2>Access denied</h2>
    <p>This section is only available to administrators.</p>
  </div>
{:else}
  <div class="admin-grid">
    <div class="card">
      <h2>Overview</h2>
      <p><strong>Total users:</strong> {totalUsers}</p>
      <p><strong>Current role:</strong> {auth.user?.role}</p>
    </div>

    <div class="card">
      <h2>Issue invite</h2>
      <form class="invite-form" onsubmit={(event) => { event.preventDefault(); createInvite(); }}>
        <div class="form-group">
          <label for="invite-email">Email address</label>
          <input
            id="invite-email"
            type="email"
            bind:value={inviteEmail}
            placeholder="person@company.com"
            required
          />
        </div>
        <button class="btn btn-primary" type="submit" disabled={creatingInvite}>
          {creatingInvite ? 'Creating...' : 'Create invite'}
        </button>
      </form>
      <p class="invite-note">
        Admin-issued invites and waitlist-approved invites use the same backend invite system.
      </p>
    </div>

    <div class="card">
      <h2>Recent users</h2>
      {#if users.length === 0}
        <p>No users found.</p>
      {:else}
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {#each users as user}
              <tr>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>

    <div class="card">
      <h2>Recent invites</h2>
      {#if invitesLoading}
        <p>Loading invites...</p>
      {:else if invites.length === 0}
        <p>No invites yet.</p>
      {:else}
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Code</th>
              <th>Source</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each invites as invite}
              <tr>
                <td>{invite.email}</td>
                <td><code>{invite.code}</code></td>
                <td>{invite.source}</td>
                <td>{inviteStatus(invite)}</td>
                <td>{formatDateTime(invite.created_at)}</td>
                <td>
                  {#if inviteStatus(invite) === 'Active'}
                    <button
                      class="btn btn-secondary btn-sm"
                      onclick={() => revokeInvite(invite)}
                      disabled={revokingInviteId === invite.invite_id}
                    >
                      {revokingInviteId === invite.invite_id ? 'Revoking...' : 'Revoke'}
                    </button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  </div>
{/if}

<style>
  .admin-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .invite-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .invite-note {
    margin-top: 0.75rem;
    color: var(--text-secondary);
    font-size: 0.85rem;
  }

  @media (min-width: 1000px) {
    .admin-grid {
      grid-template-columns: 280px 1fr;
    }
  }
</style>
