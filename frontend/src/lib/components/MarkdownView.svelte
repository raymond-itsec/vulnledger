<script lang="ts">
  let { content = '' }: { content: string } = $props();

  function renderMarkdown(md: string): string {
    if (!md) return '';
    let html = md
      // code blocks
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      // inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // headers
      .replace(/^### (.+)$/gm, '<h4>$1</h4>')
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      .replace(/^# (.+)$/gm, '<h2>$1</h2>')
      // bold and italic
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // unordered lists
      .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
      // paragraphs
      .replace(/\n\n/g, '</p><p>')
      // line breaks
      .replace(/\n/g, '<br>');

    // Wrap loose <li> in <ul>
    html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul>$1</ul>');
    return `<p>${html}</p>`;
  }

  let rendered = $derived(renderMarkdown(content));
</script>

<div class="markdown-content">{@html rendered}</div>

<style>
  .markdown-content :global(h2) { font-size: 1.25rem; margin: 1rem 0 0.5rem; font-weight: 600; }
  .markdown-content :global(h3) { font-size: 1.1rem; margin: 0.75rem 0 0.5rem; font-weight: 600; }
  .markdown-content :global(h4) { font-size: 1rem; margin: 0.5rem 0 0.25rem; font-weight: 600; }
  .markdown-content :global(p) { margin-bottom: 0.5rem; }
  .markdown-content :global(pre) {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 0.375rem;
    padding: 0.75rem;
    overflow-x: auto;
    font-size: 0.85rem;
    margin: 0.5rem 0;
  }
  .markdown-content :global(code) {
    background: #f1f5f9;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-size: 0.85em;
  }
  .markdown-content :global(pre code) { background: none; padding: 0; }
  .markdown-content :global(ul) { padding-left: 1.5rem; margin: 0.5rem 0; }
  .markdown-content :global(li) { margin-bottom: 0.25rem; }
  .markdown-content :global(a) { color: var(--accent); }
  .markdown-content :global(strong) { font-weight: 600; }
</style>
