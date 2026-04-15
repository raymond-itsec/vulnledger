<script lang="ts">
  let { text, variant = 'default' }: { text: string; variant?: string } = $props();

  const colorMap: Record<string, string> = {
    critical: 'var(--critical)',
    high: 'var(--high)',
    medium: 'var(--medium)',
    low: 'var(--low)',
    informational: 'var(--informational)',
    open: 'var(--status-open)',
    in_progress: 'var(--status-in-progress)',
    resolved: 'var(--status-resolved)',
    accepted_risk: 'var(--status-accepted-risk)',
    false_positive: 'var(--status-false-positive)',
    planned: 'var(--session-planned)',
    completed: 'var(--session-completed)',
    cancelled: 'var(--session-cancelled)',
    admin: '#7c3aed',
    reviewer: '#2563eb',
    client_user: '#059669',
  };

  let bg = $derived(colorMap[variant] || '#6b7280');
  let label = $derived(text.replace(/_/g, ' '));
</script>

<span class="badge" style="background: {bg}; color: white;">{label}</span>
