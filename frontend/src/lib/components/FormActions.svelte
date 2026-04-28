<script lang="ts">
  let {
    saving = false,
    saveLabel = 'Save',
    savingLabel = 'Saving...',
    cancelLabel = 'Cancel',
    oncancel,
  }: {
    saving?: boolean;
    saveLabel?: string;
    savingLabel?: string;
    cancelLabel?: string;
    oncancel: () => void;
  } = $props();
</script>

<div class="form-actions">
  <button class="btn btn-secondary" type="button" onclick={oncancel}>{cancelLabel}</button>
  <button class="btn btn-primary" type="submit" disabled={saving}>
    {saving ? savingLabel : saveLabel}
  </button>
</div>

<style>
  .form-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }
</style>
