<script lang="ts">
  import BrandLockup from '$lib/components/BrandLockup.svelte';
</script>

<footer class="public-footer">
  <div class="footer-brand">
    <BrandLockup href="/" spin sparkle />
  </div>
  <nav class="footer-nav" aria-label="Footer navigation">
    <a href="/about">About</a>
    <a href="/help">Help</a>
    <a href="/trust">Trust</a>
    <a href="/privacy">Privacy</a>
    <a href="/terms">Terms</a>
    <a href="/guidelines">Guidelines</a>
    <a href="/contact">Contact</a>
    <a href="/support">Support us</a>
  </nav>
  <span>Built for security professionals who take their craft seriously.</span>
  <span>© 2026 VulnLedger. All rights reserved.</span>
</footer>

<style>
  .public-footer {
    text-align: center;
    padding: 2.5rem clamp(1.25rem, 5vw, 3rem) 3rem;
    font-size: 0.8rem;
    color: #8a8dac;
    border-top: 1px solid rgba(255, 255, 255, 0.38);
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: center;
  }

  .footer-brand {
    display: flex;
    align-items: center;
    margin-bottom: 0.25rem;
  }

  .footer-nav {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.25rem 1.25rem;
    margin-bottom: 0.5rem;
  }

  .footer-nav a {
    color: #8a8dac;
    text-decoration: none;
    font-size: 0.8rem;
    transition: color 0.15s;
  }

  .footer-nav a:hover {
    color: #ff6a3d;
  }
</style>
