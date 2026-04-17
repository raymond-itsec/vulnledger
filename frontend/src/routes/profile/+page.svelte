<script lang="ts">
  import { onMount } from 'svelte';
  import { auth, fetchMe } from '$lib/stores/auth.svelte';
  import { toast } from '$lib/stores/toast.svelte';
  import { usersApi, type User } from '$lib/api/users';
  // TODO: Add password and MFA controls once backend endpoints are available.

  let loading = $state(true);
  let saving = $state(false);

  let username = $state('');
  let role = $state('');
  let fullName = $state('');
  let companyName = $state('');
  let email = $state('');

  function fieldId(name: string): string {
    return `${name}-${crypto.randomUUID()}`;
  }

  const fullNameFieldId = fieldId('profile-full-name');
  const companyNameFieldId = fieldId('profile-company-name');
  const emailFieldId = fieldId('profile-email');
  const usernameFieldId = fieldId('profile-username');
  const roleFieldId = fieldId('profile-role');

  function applyProfile(user: User): void {
    username = user.username;
    role = user.role;
    fullName = user.full_name ?? '';
    companyName = user.company_name ?? '';
    email = user.email ?? '';
  }

  onMount(async () => {
    try {
      const me = await usersApi.getMe();
      applyProfile(me);
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
{/if}

<style>
  .settings-card {
    max-width: 760px;
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
</style>
