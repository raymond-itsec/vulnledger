<script lang="ts">
  import MarkdownView from './MarkdownView.svelte';

  let {
    value = $bindable(''),
    label = '',
    required = false,
    minHeight = '120px',
  }: {
    value: string;
    label?: string;
    required?: boolean;
    minHeight?: string;
  } = $props();

  let showPreview = $state(false);
</script>

<div class="md-editor">
  {#if label}
    <div class="md-header">
      <label>{label}</label>
      <div class="md-tabs">
        <button
          type="button"
          class="tab"
          class:active={!showPreview}
          onclick={() => (showPreview = false)}
        >
          Write
        </button>
        <button
          type="button"
          class="tab"
          class:active={showPreview}
          onclick={() => (showPreview = true)}
        >
          Preview
        </button>
      </div>
    </div>
  {/if}

  {#if showPreview}
    <div class="preview-pane" style="min-height: {minHeight};">
      {#if value.trim()}
        <MarkdownView content={value} />
      {:else}
        <p class="placeholder">Nothing to preview.</p>
      {/if}
    </div>
  {:else}
    <textarea
      bind:value
      {required}
      style="min-height: {minHeight};"
      placeholder="Supports Markdown: **bold**, *italic*, `code`, [links](url), lists..."
    ></textarea>
  {/if}
</div>

<style>
  .md-editor { margin-bottom: 1rem; }
  .md-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
  }
  .md-header label {
    font-weight: 500;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  .md-tabs {
    display: flex;
    gap: 0;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    overflow: hidden;
  }
  .tab {
    padding: 0.2rem 0.6rem;
    border: none;
    background: white;
    font-size: 0.75rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.1s;
  }
  .tab:not(:last-child) { border-right: 1px solid var(--border-color); }
  .tab.active {
    background: var(--accent);
    color: white;
  }
  .md-editor textarea {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: white;
    font-family: inherit;
    font-size: 0.875rem;
    resize: vertical;
    line-height: 1.5;
  }
  .md-editor textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  }
  .preview-pane {
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: #fafafa;
    font-size: 0.875rem;
    overflow-y: auto;
  }
  .placeholder { color: var(--text-secondary); font-style: italic; }
</style>
