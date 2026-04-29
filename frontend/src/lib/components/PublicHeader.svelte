<script lang="ts">
  import BrandLockup from '$lib/components/BrandLockup.svelte';
  import { LOGIN_PATH } from '$lib/config/routes';
</script>

<nav class="public-header" aria-label="Site navigation">
  <BrandLockup href="/" />
  <div class="header-right">
    <a class="btn-ghost" href={LOGIN_PATH}>Sign in →</a>
  </div>
</nav>

<style>
  .public-header {
    position: sticky;
    top: 0;
    z-index: 60;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.9rem clamp(1.25rem, 5vw, 3rem);
    background: rgba(250, 228, 220, 0.62);
    backdrop-filter: blur(24px) saturate(170%);
    border-bottom: 1px solid rgba(255, 255, 255, 0.42);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .btn-ghost {
    font: inherit;
    font-size: 0.88rem;
    font-weight: 600;
    padding: 0.45rem 0.9rem;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.55);
    background: rgba(255, 255, 255, 0.32);
    color: #42455e;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    backdrop-filter: blur(8px);
    transition: border-color 0.15s, color 0.15s, background 0.15s;
  }

  .btn-ghost:hover {
    border-color: #ff6a3d;
    color: #ff6a3d;
    background: rgba(255, 106, 61, 0.08);
    text-decoration: none;
  }

  @media (max-width: 520px) {
    .btn-ghost {
      display: none;
    }
  }
</style>
