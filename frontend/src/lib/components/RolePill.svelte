<script lang="ts">
  // Compact role badge per the design system.
  //   admin    → purple tint
  //   reviewer → blue tint  (between admin and customer in privilege)
  //   customer → orange tint
  //   user     → orange tint (treated like customer for display)

  type RoleVariant = 'admin' | 'reviewer' | 'customer' | 'user' | string;

  let {
    role,
    label,
  }: {
    role: RoleVariant | null | undefined;
    /** Optional custom display label. Defaults to a humanised role string. */
    label?: string;
  } = $props();

  const normalized = $derived(String(role || '').toLowerCase());

  const display = $derived(
    label ??
      (normalized === 'admin'
        ? 'Global Admin'
        : normalized === 'reviewer'
          ? 'Reviewer'
          : normalized === 'customer' || normalized === 'user'
            ? 'Customer'
            : normalized.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) || 'Member'),
  );
</script>

<span
  class="role-pill"
  class:admin={normalized === 'admin'}
  class:reviewer={normalized === 'reviewer'}
  class:customer={normalized === 'customer' || normalized === 'user'}
>
  {display}
</span>

<style>
  .role-pill {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 5px;
    line-height: 1.4;
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.7);
    white-space: nowrap;
  }
  .role-pill.admin {
    background: rgba(139, 114, 224, 0.18);
    color: #a692e8;
  }
  .role-pill.reviewer {
    background: rgba(107, 155, 232, 0.18);
    color: #8bb3ee;
  }
  .role-pill.customer {
    background: rgba(240, 115, 64, 0.18);
    color: #f5905d;
  }
</style>
