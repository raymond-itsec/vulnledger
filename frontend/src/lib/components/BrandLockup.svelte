<script lang="ts">
  let {
    href = '/',
    label = 'VulnLedger',
    size = 'md',
    light = false,
    centered = false,
  }: {
    href?: string;
    label?: string;
    size?: 'sm' | 'md' | 'lg';
    light?: boolean;
    centered?: boolean;
  } = $props();
</script>

<a
  class="brand-lockup"
  class:light
  class:centered
  data-size={size}
  href={href}
  aria-label={label}
>
  <span class="mark" aria-hidden="true">
    <span class="mark-glow"></span>
    <span class="mark-letter">V</span>
  </span>
  <span class="label">{label}</span>
</a>

<style>
  .brand-lockup {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    color: #111827;
    text-decoration: none;
    font-weight: 800;
    letter-spacing: 0;
  }
  .brand-lockup.centered {
    justify-content: center;
    width: 100%;
  }
  .brand-lockup.light {
    color: rgba(255, 255, 255, 0.96);
  }
  .brand-lockup[data-size='sm'] {
    gap: 0.55rem;
    font-size: 1rem;
  }
  .brand-lockup[data-size='md'] {
    font-size: 1.05rem;
  }
  .brand-lockup[data-size='lg'] {
    gap: 0.9rem;
    font-size: 1.6rem;
  }
  .mark {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    border-radius: 0.85rem;
    background:
      radial-gradient(circle at 28% 28%, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0) 42%),
      linear-gradient(135deg, #ffbb93 2%, #ff6b3d 30%, #8cb4ff 72%, #b069ff 100%);
    box-shadow: 0 14px 32px rgba(255, 107, 61, 0.2);
    overflow: hidden;
    flex-shrink: 0;
  }
  .brand-lockup[data-size='sm'] .mark {
    width: 1.72rem;
    height: 1.72rem;
    border-radius: 0.7rem;
  }
  .brand-lockup[data-size='lg'] .mark {
    width: 2.7rem;
    height: 2.7rem;
    border-radius: 1rem;
  }
  .mark-glow {
    position: absolute;
    inset: -18%;
    background:
      radial-gradient(circle at 68% 72%, rgba(185, 128, 255, 0.42), rgba(185, 128, 255, 0) 42%),
      radial-gradient(circle at 22% 22%, rgba(255, 255, 255, 0.65), rgba(255, 255, 255, 0) 34%);
    pointer-events: none;
  }
  .mark-letter {
    position: relative;
    font-weight: 900;
    font-size: 1rem;
    color: white;
    text-shadow: 0 4px 12px rgba(61, 25, 117, 0.18);
  }
  .brand-lockup[data-size='sm'] .mark-letter {
    font-size: 0.82rem;
  }
  .brand-lockup[data-size='lg'] .mark-letter {
    font-size: 1.35rem;
  }
  .label {
    line-height: 1;
    white-space: nowrap;
  }
</style>
