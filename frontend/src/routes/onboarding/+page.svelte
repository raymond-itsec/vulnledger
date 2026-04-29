  <script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import BrandLockup from '$lib/components/BrandLockup.svelte';
  import { INVITE_PATH, LOGIN_PATH } from '$lib/config/routes';
  import { onboardingApi } from '$lib/api/onboarding';
  import { toast } from '$lib/stores/toast.svelte';

  let loading = $state(true);
  let submitting = $state(false);
  let inviteEmail = $state('');
  let username = $state('');
  let password = $state('');
  let confirmPassword = $state('');
  let fullName = $state('');
  let companyName = $state('');

  onMount(async () => {
    try {
      const state = await onboardingApi.getState();
      inviteEmail = state.email;
    } catch {
      await goto(INVITE_PATH, { replaceState: true });
      return;
    } finally {
      loading = false;
    }
  });

  async function completeOnboarding() {
    if (password !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }

    submitting = true;
    try {
      const result = await onboardingApi.complete({
        username,
        password,
        full_name: fullName || null,
        company_name: companyName || null,
      });
      const loginUrl = new URL(LOGIN_PATH, page.url.origin);
      loginUrl.searchParams.set('username', result.username);
      loginUrl.searchParams.set('welcome', '1');
      await goto(`${loginUrl.pathname}${loginUrl.search}`, { replaceState: true });
    } catch (error: any) {
      toast.error(error?.message || 'Could not complete onboarding.');
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <title>Onboarding - VulnLedger</title>
</svelte:head>

<div class="public-shell">
  <div class="public-card">
    <BrandLockup href="/" size="lg" centered={true} spin sparkle />
    <h1>Complete your account</h1>
    {#if loading}
      <p class="intro">Checking your invite…</p>
    {:else}
      <p class="intro">
        This invite is reserved for <strong>{inviteEmail}</strong>.
      </p>
      <form onsubmit={(event) => { event.preventDefault(); completeOnboarding(); }}>
        <div class="form-group">
          <label for="invite-email">Invited email</label>
          <input id="invite-email" type="email" value={inviteEmail} disabled />
        </div>
        <div class="form-group">
          <label for="onboarding-username">Username</label>
          <input id="onboarding-username" type="text" bind:value={username} minlength="3" maxlength="100" required />
        </div>
        <div class="form-group">
          <label for="onboarding-password">Password</label>
          <input id="onboarding-password" type="password" bind:value={password} minlength="12" autocomplete="new-password" required />
        </div>
        <div class="form-group">
          <label for="onboarding-password-confirm">Confirm password</label>
          <input id="onboarding-password-confirm" type="password" bind:value={confirmPassword} minlength="12" autocomplete="new-password" required />
        </div>
        <div class="form-group">
          <label for="onboarding-full-name">Full name</label>
          <input id="onboarding-full-name" type="text" bind:value={fullName} maxlength="255" />
        </div>
        <div class="form-group">
          <label for="onboarding-company">Company</label>
          <input id="onboarding-company" type="text" bind:value={companyName} maxlength="255" />
        </div>
        <button class="btn btn-primary full-width" type="submit" disabled={submitting}>
          {submitting ? 'Creating account...' : 'Create account'}
        </button>
      </form>
    {/if}
  </div>
</div>

<style>
  .public-shell {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    background:
      radial-gradient(ellipse 80% 60% at 15% 25%, rgba(255, 180, 150, 0.4) 0%, transparent 55%),
      radial-gradient(ellipse 70% 55% at 95% 15%, rgba(255, 200, 220, 0.3) 0%, transparent 60%),
      radial-gradient(ellipse 90% 70% at 85% 90%, rgba(180, 155, 245, 0.32) 0%, transparent 60%),
      linear-gradient(160deg, #fae2d8 0%, #f3d0e8 30%, #e0cdf5 60%, #d4d8f5 85%, #dad5f0 100%);
  }
  .public-card {
    width: 100%;
    max-width: 520px;
    padding: 2rem;
    border-radius: 1.25rem;
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.78);
    box-shadow: 0 18px 40px rgba(80, 40, 120, 0.16), 0 36px 70px rgba(80, 40, 120, 0.18);
  }
  .public-card :global(.brand-lockup) {
    margin-bottom: 1rem;
  }
  h1 {
    margin: 0 0 0.5rem;
    text-align: center;
  }
  .intro {
    margin: 0 0 1.25rem;
    text-align: center;
    color: var(--text-secondary);
    line-height: 1.6;
  }
  .full-width {
    width: 100%;
    justify-content: center;
  }
</style>
