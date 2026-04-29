<script lang="ts">
  import { goto } from '$app/navigation';
  import BrandLockup from '$lib/components/BrandLockup.svelte';
  import { LOGIN_PATH, ONBOARDING_PATH } from '$lib/config/routes';
  import { onboardingApi } from '$lib/api/onboarding';
  import { toast } from '$lib/stores/toast.svelte';

  let inviteCode = $state('');
  let verifying = $state(false);

  async function verifyInvite() {
    const normalizedCode = inviteCode.trim();
    if (!normalizedCode) {
      toast.error('Enter your invite code.');
      return;
    }

    verifying = true;
    try {
      await onboardingApi.verifyInvite(normalizedCode);
      await goto(ONBOARDING_PATH, { replaceState: true });
    } catch (error: any) {
      toast.error(error?.message || 'Could not verify invite code.');
    } finally {
      verifying = false;
    }
  }
</script>

<svelte:head>
  <title>Invite Code - VulnLedger</title>
</svelte:head>

<div class="public-shell">
  <div class="public-card">
    <BrandLockup href="/" size="lg" centered={true} />
    <h1>Enter your invite code</h1>
    <p class="intro">
      Your invite code unlocks onboarding for the email address attached to the invite.
    </p>
    <form onsubmit={(event) => { event.preventDefault(); verifyInvite(); }}>
      <div class="form-group">
        <label for="invite-code">Invite code</label>
        <input
          id="invite-code"
          type="text"
          bind:value={inviteCode}
          placeholder="Paste your invite code"
          autocomplete="one-time-code"
          required
        />
      </div>
      <button class="btn btn-primary full-width" type="submit" disabled={verifying}>
        {verifying ? 'Checking...' : 'Continue to onboarding'}
      </button>
    </form>
    <div class="public-links">
      <a href={LOGIN_PATH}>Already have an account? Sign in</a>
      <a href="/">Back to waitlist</a>
    </div>
  </div>
</div>

<style>
  .public-shell {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    background: linear-gradient(180deg, #f7f1fb 0%, #eef4ff 100%);
  }
  .public-card {
    width: 100%;
    max-width: 460px;
    padding: 2rem;
    border-radius: 1rem;
    background: white;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
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
  .public-links {
    margin-top: 1rem;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    font-size: 0.9rem;
  }
  @media (max-width: 520px) {
    .public-links {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
  }
</style>
