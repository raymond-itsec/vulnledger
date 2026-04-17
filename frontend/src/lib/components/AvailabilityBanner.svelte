<script lang="ts">
  import { appAvailability } from '$lib/stores/app-availability.svelte';
</script>

<div
  class="availability-banner"
  class:visible={appAvailability.unavailable}
  role="alert"
  aria-live="assertive"
  aria-hidden={!appAvailability.unavailable}
>
  <span>{appAvailability.message}</span>
</div>

<style>
  .availability-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1400;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 3rem;
    padding: 0.75rem 1rem;
    background: rgba(153, 27, 27, 0.98);
    color: white;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    box-shadow: 0 14px 32px rgba(127, 29, 29, 0.28);
    transform: translateY(-110%);
    opacity: 0;
    pointer-events: none;
    transition:
      transform 0.22s ease,
      opacity 0.22s ease;
  }

  .availability-banner.visible {
    transform: translateY(0);
    opacity: 1;
  }
</style>
