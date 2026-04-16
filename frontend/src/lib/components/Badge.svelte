<script lang="ts">
  import { taxonomy } from '$lib/stores/taxonomy.svelte';

  let { text, variant = 'default' }: { text: string; variant?: string } = $props();

  const colorMap: Record<string, string> = {
    admin: '#7c3aed',
    reviewer: '#2563eb',
    client_user: '#059669',
  };

  function taxonomyColor(key: string): string | null {
    if (taxonomy.hasEntry('risk_level', key)) return taxonomy.color('risk_level', key);
    if (taxonomy.hasEntry('remediation_status', key)) return taxonomy.color('remediation_status', key);
    if (taxonomy.hasEntry('session_status', key)) return taxonomy.color('session_status', key);
    return null;
  }

  function taxonomyLabel(key: string): string | null {
    if (taxonomy.hasEntry('risk_level', key)) return taxonomy.label('risk_level', key);
    if (taxonomy.hasEntry('remediation_status', key)) return taxonomy.label('remediation_status', key);
    if (taxonomy.hasEntry('session_status', key)) return taxonomy.label('session_status', key);
    return null;
  }

  let bg = $derived(taxonomyColor(variant) || colorMap[variant] || '#6b7280');
  let label = $derived(taxonomyLabel(text) || text.replace(/_/g, ' '));
</script>

<span class="badge" style="background: {bg}; color: white;">{label}</span>
