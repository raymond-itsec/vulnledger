<script lang="ts">
  import { sanitizeUrl } from '$lib/util/url';

  type InlineToken =
    | { type: 'text'; value: string }
    | { type: 'code'; value: string }
    | { type: 'strong'; value: string }
    | { type: 'em'; value: string }
    | { type: 'link'; value: string; href: string };

  type BlockToken =
    | { type: 'h2'; tokens: InlineToken[] }
    | { type: 'h3'; tokens: InlineToken[] }
    | { type: 'h4'; tokens: InlineToken[] }
    | { type: 'p'; tokens: InlineToken[] }
    | { type: 'ul'; items: InlineToken[][] }
    | { type: 'pre'; value: string };

  let { content = '' }: { content: string } = $props();

  function parseInline(value: string): InlineToken[] {
    const tokens: InlineToken[] = [];
    const pattern = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[[^\]]+\]\([^)]+\))/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = pattern.exec(value)) !== null) {
      if (match.index > lastIndex) {
        tokens.push({ type: 'text', value: value.slice(lastIndex, match.index) });
      }

      const raw = match[0];
      if (raw.startsWith('`') && raw.endsWith('`')) {
        tokens.push({ type: 'code', value: raw.slice(1, -1) });
      } else if (raw.startsWith('**') && raw.endsWith('**')) {
        tokens.push({ type: 'strong', value: raw.slice(2, -2) });
      } else if (raw.startsWith('*') && raw.endsWith('*')) {
        tokens.push({ type: 'em', value: raw.slice(1, -1) });
      } else if (raw.startsWith('[')) {
        const linkMatch = raw.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (linkMatch) {
          const safeHref = sanitizeUrl(linkMatch[2]);
          if (safeHref) {
            tokens.push({ type: 'link', value: linkMatch[1], href: safeHref });
          } else {
            tokens.push({ type: 'text', value: linkMatch[1] });
          }
        } else {
          tokens.push({ type: 'text', value: raw });
        }
      } else {
        tokens.push({ type: 'text', value: raw });
      }

      lastIndex = pattern.lastIndex;
    }

    if (lastIndex < value.length) {
      tokens.push({ type: 'text', value: value.slice(lastIndex) });
    }
    return tokens;
  }

  function parseBlocks(md: string): BlockToken[] {
    const text = md.replaceAll('\r\n', '\n').trim();
    if (!text) return [];

    const lines = text.split('\n');
    const blocks: BlockToken[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i].trimEnd();
      if (!line.trim()) {
        i += 1;
        continue;
      }

      if (line.startsWith('```')) {
        i += 1;
        const codeLines: string[] = [];
        while (i < lines.length && !lines[i].startsWith('```')) {
          codeLines.push(lines[i]);
          i += 1;
        }
        blocks.push({ type: 'pre', value: codeLines.join('\n') });
        if (i < lines.length && lines[i].startsWith('```')) i += 1;
        continue;
      }

      if (line.startsWith('### ')) {
        blocks.push({ type: 'h4', tokens: parseInline(line.slice(4).trim()) });
        i += 1;
        continue;
      }
      if (line.startsWith('## ')) {
        blocks.push({ type: 'h3', tokens: parseInline(line.slice(3).trim()) });
        i += 1;
        continue;
      }
      if (line.startsWith('# ')) {
        blocks.push({ type: 'h2', tokens: parseInline(line.slice(2).trim()) });
        i += 1;
        continue;
      }

      if (/^[-*]\s+/.test(line)) {
        const items: InlineToken[][] = [];
        while (i < lines.length && /^[-*]\s+/.test(lines[i].trimStart())) {
          const item = lines[i].trimStart().replace(/^[-*]\s+/, '');
          items.push(parseInline(item));
          i += 1;
        }
        blocks.push({ type: 'ul', items });
        continue;
      }

      const paragraphLines: string[] = [line];
      i += 1;
      while (i < lines.length) {
        const next = lines[i].trimEnd();
        if (!next.trim()) {
          i += 1;
          break;
        }
        if (
          next.startsWith('# ')
          || next.startsWith('## ')
          || next.startsWith('### ')
          || next.startsWith('```')
          || /^[-*]\s+/.test(next.trimStart())
        ) {
          break;
        }
        paragraphLines.push(next);
        i += 1;
      }
      blocks.push({ type: 'p', tokens: parseInline(paragraphLines.join(' ')) });
    }

    return blocks;
  }

  let blocks = $derived(parseBlocks(content));
</script>

{#snippet renderInline(tokens: InlineToken[])}
  {#each tokens as token}
    {#if token.type === 'text'}{token.value}{/if}
    {#if token.type === 'code'}<code>{token.value}</code>{/if}
    {#if token.type === 'strong'}<strong>{token.value}</strong>{/if}
    {#if token.type === 'em'}<em>{token.value}</em>{/if}
    {#if token.type === 'link'}<a href={token.href} target="_blank" rel="noopener noreferrer">{token.value}</a>{/if}
  {/each}
{/snippet}

<div class="markdown-content">
  {#if blocks.length === 0}
    <p class="muted">No content.</p>
  {:else}
    {#each blocks as block}
      {#if block.type === 'h2'}
        <h2>
          {@render renderInline(block.tokens)}
        </h2>
      {:else if block.type === 'h3'}
        <h3>
          {@render renderInline(block.tokens)}
        </h3>
      {:else if block.type === 'h4'}
        <h4>
          {@render renderInline(block.tokens)}
        </h4>
      {:else if block.type === 'p'}
        <p>
          {@render renderInline(block.tokens)}
        </p>
      {:else if block.type === 'ul'}
        <ul>
          {#each block.items as itemTokens}
            <li>
              {@render renderInline(itemTokens)}
            </li>
          {/each}
        </ul>
      {:else if block.type === 'pre'}
        <pre><code>{block.value}</code></pre>
      {/if}
    {/each}
  {/if}
</div>

<style>
  .markdown-content h2 { font-size: 1.25rem; margin: 1rem 0 0.5rem; font-weight: 600; }
  .markdown-content h3 { font-size: 1.1rem; margin: 0.75rem 0 0.5rem; font-weight: 600; }
  .markdown-content h4 { font-size: 1rem; margin: 0.5rem 0 0.25rem; font-weight: 600; }
  .markdown-content p { margin-bottom: 0.5rem; white-space: pre-wrap; }
  .markdown-content pre {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 0.375rem;
    padding: 0.75rem;
    overflow-x: auto;
    font-size: 0.85rem;
    margin: 0.5rem 0;
  }
  .markdown-content code {
    background: #f1f5f9;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-size: 0.85em;
  }
  .markdown-content pre code { background: none; padding: 0; }
  .markdown-content ul { padding-left: 1.5rem; margin: 0.5rem 0; }
  .markdown-content li { margin-bottom: 0.25rem; }
  .markdown-content a { color: var(--accent); }
  .markdown-content strong { font-weight: 600; }
  .muted { color: var(--text-secondary); font-style: italic; }
</style>
