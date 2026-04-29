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
    background:
      radial-gradient(ellipse 80% 60% at 15% 25%, rgba(255, 180, 150, 0.4) 0%, transparent 55%),
      radial-gradient(ellipse 70% 55% at 95% 15%, rgba(255, 200, 220, 0.3) 0%, transparent 60%),
      radial-gradient(ellipse 90% 70% at 85% 90%, rgba(180, 155, 245, 0.32) 0%, transparent 60%),
      linear-gradient(160deg, #fae2d8 0%, #f3d0e8 30%, #e0cdf5 60%, #d4d8f5 85%, #dad5f0 100%);
    padding: 1.5rem;
  }
  .login-card {
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.78);
    padding: 2.5rem;
    border-radius: 1.25rem;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 18px 40px rgba(80, 40, 120, 0.16), 0 36px 70px rgba(80, 40, 120, 0.18);
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
    background: rgba(255, 255, 255, 0.92);
    border-color: rgba(203, 187, 229, 0.72);
    color: var(--text-primary);
  }
  .login-card .form-group input::placeholder { color: #8a8dac; }
  .login-card .form-group input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(255, 106, 61, 0.14);
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
