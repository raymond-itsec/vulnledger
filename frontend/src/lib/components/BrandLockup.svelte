<script lang="ts">
  let {
    href = '/',
    label = 'VulnLedger',
    size = 'md',
    light = false,
    centered = false,
    spin = false,
    sparkle = false,
  }: {
    href?: string;
    label?: string;
    size?: 'sm' | 'md' | 'lg';
    light?: boolean;
    centered?: boolean;
    spin?: boolean;
    sparkle?: boolean;
  } = $props();

  // Trace path tuned for the literal label "VulnLedger" — dips into the V,
  // climbs the l/L/d ascenders, glides across the x-height letters in between.
  const VULN_LEDGER_TRACE =
    'M0,1 L5,11 L10,1 L10,4 L18,4 L18,1 L22,1 L22,4 L30,4 L30,1 L30,11 L38,11 L38,4 L46,4 L51,1 L51,4 L62,4 L70,4 L76,4';
  const traceActive = $derived(sparkle && label === 'VulnLedger');
</script>

<a
  class="brand-lockup"
  class:light
  class:centered
  class:spin
  class:sparkle={traceActive}
  data-size={size}
  href={href}
  aria-label={label}
>
  <span class="mark" aria-hidden="true">
    <span class="mark-glow"></span>
    <span class="mark-letter">V</span>
  </span>
  <span class="label">
    {label}
    {#if traceActive}
      <svg class="brand-trace" viewBox="0 0 76 14" preserveAspectRatio="none" aria-hidden="true">
        <g>
          <g>
            <path
              class="spark-shape"
              d="M0,-4 L1.2,-1.2 L4,0 L1.2,1.2 L0,4 L-1.2,1.2 L-4,0 L-1.2,-1.2 Z"
            />
            <animate
              attributeName="opacity"
              values="0;0;1;1;0;0"
              keyTimes="0;0.01;0.03;0.20;0.30;1"
              dur="8.5s"
              repeatCount="indefinite"
            />
            <animateTransform
              attributeName="transform"
              type="scale"
              values="1;1;3;3"
              keyTimes="0;0.20;0.30;1"
              dur="8.5s"
              repeatCount="indefinite"
            />
          </g>
          <animateMotion
            dur="8.5s"
            repeatCount="indefinite"
            rotate="auto"
            keyPoints="0;1;1"
            keyTimes="0;0.20;1"
            calcMode="linear"
            path={VULN_LEDGER_TRACE}
          />
        </g>
      </svg>
    {/if}
  </span>
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

  /* ── Spin: animated conic-gradient mark ────────────── */
  @property --bl-mark-angle {
    syntax: '<angle>';
    initial-value: 210deg;
    inherits: false;
  }
  .brand-lockup.spin .mark {
    background: conic-gradient(
      from var(--bl-mark-angle),
      #ff6a3d,
      #ffb266,
      #7ab7ff,
      #a78bfa,
      #ff6a3d
    );
    animation: bl-mark-spin 5.5s linear infinite;
  }
  .brand-lockup.spin .mark-glow { display: none; }
  @keyframes bl-mark-spin {
    to { --bl-mark-angle: 570deg; }
  }

  /* ── Sparkle: SVG trace following letter contours ──── */
  .brand-lockup.sparkle .label {
    position: relative;
    display: inline-block;
  }
  .brand-trace {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    display: block;
    overflow: visible;
    pointer-events: none;
  }
  .spark-shape {
    fill: #fff;
    filter:
      drop-shadow(0 0 2px rgba(255, 225, 180, 1))
      drop-shadow(0 0 5px rgba(255, 180, 120, 0.9))
      drop-shadow(0 0 9px rgba(255, 150, 90, 0.55));
  }

  @media (prefers-reduced-motion: reduce) {
    .brand-lockup.spin .mark { animation: none; }
    .brand-lockup.sparkle .brand-trace { display: none; }
  }
</style>
