<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { usersApi, type User } from '$lib/api/users';
  import { toast } from '$lib/stores/toast.svelte';
  // TODO: Extend this page with real admin controls (role changes, activation, audit view).

  let loading = $state(true);
  let users = $state<User[]>([]);
  let totalUsers = $state(0);

  const isAdmin = $derived(auth.user?.role === 'admin');

  onMount(async () => {
    if (!isAdmin) {
      loading = false;
      return;
    }

    try {
      const data = await usersApi.list(1, 10);
      users = data.items;
      totalUsers = data.total;
    } catch (error: any) {
      toast.error(error?.message || 'Could not load admin data.');
    } finally {
      loading = false;
    }
  });
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
  </div>
{/if}

<style>
  .admin-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  @media (min-width: 1000px) {
    .admin-grid {
      grid-template-columns: 280px 1fr;
    }
  }
</style>
