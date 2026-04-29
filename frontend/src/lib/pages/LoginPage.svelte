<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import BrandLockup from '$lib/components/BrandLockup.svelte';
  import { login as doLogin } from '$lib/stores/auth.svelte';
  import { appAvailability } from '$lib/stores/app-availability.svelte';
  import { APP_BASE_PATH, INVITE_PATH } from '$lib/config/routes';
  import { toast } from '$lib/stores/toast.svelte';
  import { fieldId } from '$lib/util/dom';

  let username = $state('');
  let password = $state('');
  let loggingIn = $state(false);
  let oidcAvailable = $state(false);

  const usernameFieldId = fieldId('login-username');
  const passwordFieldId = fieldId('login-password');

  async function handleLogin() {
    loggingIn = true;
    try {
      await doLogin(username, password);
      await goto(APP_BASE_PATH, { replaceState: true });
    } catch (e: any) {
      if (!appAvailability.unavailable) {
        toast.error(e.message || 'Login failed. Please try again later.');
      }
    } finally {
      loggingIn = false;
    }
  }

  onMount(async () => {
    const invitedUsername = page.url.searchParams.get('username');
    if (invitedUsername) {
      username = invitedUsername;
    }
    if (page.url.searchParams.get('welcome') === '1') {
      toast.success('Account created. Sign in to continue.');
    }
    await appAvailability.checkLoginPageAppAvailabilityOnce();
    oidcAvailable = await appAvailability.checkLoginPageOidcAvailabilityOnce();
  });
</script>

<svelte:head>
  <title>Sign In - VulnLedger</title>
</svelte:head>

<div class="login-page">
  <div class="login-card">
    <div class="login-brand">
      <BrandLockup href="/" size="lg" centered={true} />
    </div>
    <p class="subtitle">Sign in to continue</p>
    <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }}>
      <div class="form-group">
        <label for={usernameFieldId}>Username</label>
        <input id={usernameFieldId} type="text" bind:value={username} required autocomplete="username" />
      </div>
      <div class="form-group">
        <label for={passwordFieldId}>Password</label>
        <input id={passwordFieldId} type="password" bind:value={password} required autocomplete="current-password" />
      </div>
      <button class="btn btn-primary login-btn" type="submit" disabled={loggingIn}>
        {loggingIn ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
    {#if oidcAvailable}
      <div class="sso-divider">
        <span>or</span>
      </div>
      <a href="/api/auth/oidc/login" class="btn btn-secondary login-btn sso-btn">
        Sign in with SSO
      </a>
    {/if}
    <div class="login-links">
      <a href={INVITE_PATH}>Already have an invite code?</a>
      <a href="/">Back to waitlist</a>
    </div>
  </div>
</div>

<style>
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 1.5rem;
  }
  .login-card {
    background: white;
    padding: 2.5rem;
    border-radius: 0.75rem;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }
  .login-brand {
    display: flex;
    justify-content: center;
    margin-bottom: 0.25rem;
  }
  .login-brand :global(.brand-lockup) {
    margin-bottom: 0.25rem;
  }
  .subtitle { color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.9rem; text-align: center; }
  .login-btn { width: 100%; justify-content: center; padding: 0.625rem; text-align: center; text-decoration: none; display: block; }
  .login-card .form-group input {
    background: #f8fafc;
    border-color: #cbd5e1;
    color: #111827;
  }
  .login-card .form-group input::placeholder { color: #6b7280; }
  .login-card .form-group input:focus {
    border-color: #64748b;
    box-shadow: 0 0 0 2px rgba(100, 116, 139, 0.18);
  }
  .sso-divider {
    text-align: center;
    margin: 1rem 0;
    position: relative;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }
  .sso-divider::before, .sso-divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: var(--border-color);
  }
  .sso-divider::before { left: 0; }
  .sso-divider::after { right: 0; }
  .sso-btn { margin-top: 0; }
  .login-links {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    margin-top: 1rem;
    font-size: 0.85rem;
  }
  .login-links a {
    color: var(--text-secondary);
    text-decoration: none;
  }
  .login-links a:hover {
    color: var(--accent);
    text-decoration: underline;
  }
  @media (max-width: 520px) {
    .login-links {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
  }
</style>
