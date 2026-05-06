<script lang="ts" module>
  // Vulny — VulnLedger's robot mascot.
  //
  // Picks the right asset for the requested state and size automatically:
  //  - "head" states use the head-only crops (smaller, fit avatars/inline)
  //  - "full" states use the full-body PNGs (hero placements, empty states)
  //  - sm/md sizes load the 50% -small.png variant by default to keep the
  //    bundle light; lg/xl reach for the full-resolution file.

  export type VulnyState =
    | 'neutral'        // head — default
    | 'happy'          // full body
    | 'thinking'       // head
    | 'excited'        // head
    | 'hello-wave'     // full — onboarding / first-run greeting
    | 'explaining'     // full — tooltips / help
    | 'scanning'       // full — active loading
    | 'analyzing'      // full — long ops / processing
    | 'success'        // full — all-clear, with shield
    | 'failed';        // full — error, with shield

  export type VulnySize = 'sm' | 'md' | 'lg' | 'xl';

  interface AssetSpec {
    /** filename without "-small" suffix and ".png" extension */
    base: string;
    /** intrinsic aspect ratio width/height (head crops are square-ish, full bodies are 2:3) */
    aspect: 'head' | 'full';
  }

  // State → asset basename mapping. Keep in sync with files in /branding/vulny/.
  const ASSETS: Record<VulnyState, AssetSpec> = {
    neutral:       { base: 'neutral-head',     aspect: 'head' },
    happy:         { base: 'happy',            aspect: 'full' },
    thinking:      { base: 'thinking-head',    aspect: 'head' },
    excited:       { base: 'excited-head',     aspect: 'head' },
    'hello-wave':  { base: 'hello-wave',       aspect: 'full' },
    explaining:    { base: 'explaining',       aspect: 'full' },
    scanning:      { base: 'scanning',         aspect: 'full' },
    analyzing:     { base: 'analyzing-chart',  aspect: 'full' },
    success:       { base: 'success-shield',   aspect: 'full' },
    failed:        { base: 'failed-shield',    aspect: 'full' },
  };

  // Pixel heights per size step. Width is computed from the aspect ratio
  // (1:1 for head crops, 2:3 for full body) so the layout never warps.
  const HEIGHT_PX: Record<VulnySize, number> = {
    sm: 48,
    md: 96,
    lg: 192,
    xl: 320,
  };

  function widthForHeight(height: number, aspect: AssetSpec['aspect']): number {
    if (aspect === 'head') return height;          // 1:1 for head crops
    return Math.round((height * 2) / 3);            // 2:3 for full body (1024×1536 → 512×768)
  }

  // Use the half-resolution -small.png for sm/md; reach for full-res only at lg+.
  function fileFor(spec: AssetSpec, size: VulnySize): string {
    const useSmall = size === 'sm' || size === 'md';
    const suffix = useSmall ? '-small' : '';
    return `/branding/vulny/${spec.base}${suffix}.png`;
  }
</script>

<script lang="ts">
  let {
    state = 'neutral',
    size = 'md',
    alt,
  }: {
    state?: VulnyState;
    size?: VulnySize;
    alt?: string;
  } = $props();

  const spec = $derived(ASSETS[state] ?? ASSETS.neutral);
  const height = $derived(HEIGHT_PX[size]);
  const width = $derived(widthForHeight(height, spec.aspect));
  const src = $derived(fileFor(spec, size));
  const altText = $derived(alt ?? `Vulny — ${state}`);
</script>

<img class="vulny" {src} alt={altText} {width} {height} loading="lazy" decoding="async" />

<style>
  .vulny {
    display: inline-block;
    user-select: none;
    -webkit-user-drag: none;
  }
</style>
