<!--
  Error boundary. Catches runtime errors thrown during child rendering
  (NOT API errors - those are handled by `ApiError` + toast / inline).
  Without this, a thrown error during render crashes the whole Svelte
  tree to a blank page.

  Built on Svelte 5's native `<svelte:boundary>`. Wraps the failed
  subtree with `<ErrorState>` and exposes a `reset` callback so the
  user can retry without a full page reload.

  Two recommended use sites:

  1. **App-level** (in `src/routes/+layout.svelte`) as a safety net so
     no render error ever results in a white screen.
  2. **Opt-in** around known-risky widgets (markdown editor, third-
     party charts) so a broken widget doesn't take out the chrome
     around it.

  Props:
  - `title`     Custom panel headline.
  - `message`   Override the default user-facing message. If omitted,
                a generic phrase is shown - the raw error message is
                NOT leaked because it could contain stack-trace text
                or implementation details that confuse users.
  - `requestId` Optional ID to surface (rarely useful for render
                errors; mainly here for symmetry with API errors).
  - `onError`   Hook for logging / telemetry. Called with the caught
                error.
-->
<script lang="ts">
  import type { Snippet } from 'svelte';
  import ErrorState from './ErrorState.svelte';

  interface Props {
    children?: Snippet;
    title?: string;
    message?: string;
    requestId?: string | null;
    onError?: (error: unknown) => void;
  }

  let {
    children,
    title = 'Something went wrong',
    message = 'This part of the page failed to render. Try again, or refresh.',
    requestId = null,
    onError,
  }: Props = $props();
</script>

<svelte:boundary onerror={(error) => onError?.(error)}>
  {@render children?.()}
  {#snippet failed(_error, reset)}
    <ErrorState
      {title}
      {message}
      {requestId}
      onRetry={reset}
      retryLabel="Retry"
    />
  {/snippet}
</svelte:boundary>
