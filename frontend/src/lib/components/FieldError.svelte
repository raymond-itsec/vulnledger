<!--
  Inline per-field error message. Pairs with form inputs to surface a
  validation message directly under the offending control.

  Usage:

      <input bind:value={email} aria-invalid={!!errors.email}
             aria-describedby={errors.email ? 'email-err' : undefined} />
      <FieldError id="email-err" message={errors.email} />

  Renders nothing when `message` is empty/undefined, so consumers can
  always include the component without conditional wrapping.
-->
<script lang="ts">
  let { id, message }: { id?: string; message?: string | null } = $props();
</script>

{#if message}
  <p class="field-error" id={id} role="alert">
    <span class="icon" aria-hidden="true">!</span>
    <span>{message}</span>
  </p>
{/if}

<style>
  .field-error {
    display: flex;
    align-items: flex-start;
    gap: 0.375rem;
    margin: 0.25rem 0 0 0;
    padding: 0;
    color: var(--color-error);
    font-size: 0.8125rem;
    line-height: 1.3;
  }

  .icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    background: var(--color-error);
    color: white;
    font-size: 0.6875rem;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 0.125rem;
  }
</style>
