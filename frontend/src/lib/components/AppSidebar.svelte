<script lang="ts" module>
  // AppSidebar — VulnLedger's dark, collapsible left rail.
  //
  // Visual spec follows /design-system/project/ui_kits/app/Sidebar.jsx:
  //  - 224px expanded / 64px collapsed
  //  - Dark charcoal #12121E with backdrop blur
  //  - Active item: warm orange tint (rgba(240,115,64,0.18))
  //  - Hover: subtle white tint
  //  - Logo: V mark with purple→coral→orange gradient
  //  - User row pinned bottom: avatar + name + role pill
  //  - Toggle button (chevrons-left/right) above user row
  //
  // Auth, role filtering, and the actual nav data are owned by +layout.svelte;
  // this component is purely presentational.

  export interface NavItem {
    href: string;
    label: string;
    icon: 'dashboard' | 'clients' | 'assets' | 'sessions' | 'findings' | 'admin' | 'templates';
    section?: string;
  }
</script>

<script lang="ts">
  import { sidebar } from '$lib/stores/sidebar.svelte';
  import RolePill from '$lib/components/RolePill.svelte';

  let {
    items,
    activeHref,
    user,
    role,
    version,
    onLogout,
    profileHref,
    adminHref,
  }: {
    items: NavItem[];
    activeHref: string;
    user: { full_name?: string | null; username?: string | null } | null;
    role: string | null | undefined;
    version: string;
    onLogout: () => void | Promise<void>;
    profileHref: string;
    adminHref: string;
  } = $props();

  let userMenuOpen = $state(false);
  let userMenuRoot = $state<HTMLDivElement | null>(null);

  const collapsed = $derived(sidebar.collapsed);

  const displayName = $derived(
    user?.full_name?.trim() || user?.username?.trim() || 'Member',
  );
  const initials = $derived(
    displayName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]!.toUpperCase())
      .join(''),
  );

  function isActive(href: string): boolean {
    if (href === activeHref) return true;
    return activeHref.startsWith(href + '/');
  }

  function toggleUserMenu(event: MouseEvent) {
    event.stopPropagation();
    userMenuOpen = !userMenuOpen;
  }
  function closeUserMenu() {
    userMenuOpen = false;
  }
  function handleDocumentClick(event: MouseEvent) {
    if (!userMenuOpen || !userMenuRoot) return;
    const target = event.target as Node | null;
    if (target && !userMenuRoot.contains(target)) userMenuOpen = false;
  }
  function handleWindowKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') userMenuOpen = false;
  }

  $effect(() => {
    document.addEventListener('click', handleDocumentClick);
    return () => document.removeEventListener('click', handleDocumentClick);
  });
</script>

<svelte:window onkeydown={handleWindowKeydown} />

<aside class="sidebar" class:collapsed aria-label="Primary navigation">
  <!-- Logo -->
  <a class="brand" href="/app" aria-label="VulnLedger dashboard">
    <span class="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 48 48" width="17" height="17" fill="none">
        <path d="M13 14 L24 34 L35 14" stroke="white" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>
    {#if !collapsed}
      <span class="brand-label">
        <span class="brand-name">VulnLedger</span>
        <span class="brand-version">{version}</span>
      </span>
    {/if}
  </a>

  <!-- Nav -->
  <nav class="nav">
    {#each items as item, i}
      {@const showSection = item.section && (i === 0 || items[i - 1].section !== item.section)}
      {#if showSection && !collapsed}
        <div class="section-label">{item.section}</div>
      {:else if showSection && collapsed}
        <div class="section-spacer"></div>
      {/if}
      <a
        href={item.href}
        class="nav-item"
        class:active={isActive(item.href)}
        title={collapsed ? item.label : undefined}
      >
        <span class="nav-icon" aria-hidden="true">
          {#if item.icon === 'dashboard'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
          {:else if item.icon === 'clients'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>
          {:else if item.icon === 'assets'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 7.7 4.5 7.7-4.5"/><path d="m7.5 4.27 9 5.15"/></svg>
          {:else if item.icon === 'sessions'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>
          {:else if item.icon === 'findings'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
          {:else if item.icon === 'admin'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          {:else if item.icon === 'templates'}
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
          {/if}
        </span>
        {#if !collapsed}
          <span class="nav-label">{item.label}</span>
        {/if}
      </a>
    {/each}
  </nav>

  <div class="spacer"></div>

  <!-- Toggle -->
  <button
    type="button"
    class="toggle"
    class:floats={collapsed}
    onclick={() => sidebar.toggle()}
    aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
  >
    {#if collapsed}
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m6 17 5-5-5-5"/><path d="m13 17 5-5-5-5"/></svg>
    {:else}
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m11 17-5-5 5-5"/><path d="m18 17-5-5 5-5"/></svg>
    {/if}
  </button>

  <!-- User row -->
  <div class="user" bind:this={userMenuRoot}>
    <button type="button" class="user-trigger" onclick={toggleUserMenu} aria-haspopup="menu" aria-expanded={userMenuOpen}>
      <span
        class="avatar"
        class:admin={role === 'admin'}
        class:reviewer={role === 'reviewer'}
        aria-hidden="true"
      >
        {initials || '·'}
      </span>
      {#if !collapsed}
        <span class="user-text">
          <span class="user-name">{displayName}</span>
          <RolePill {role} />
        </span>
      {/if}
    </button>
    {#if userMenuOpen}
      <div class="user-menu" role="menu">
        <a class="user-menu-item" href={profileHref} onclick={closeUserMenu} role="menuitem">Profile settings</a>
        {#if role === 'admin'}
          <a class="user-menu-item" href={adminHref} onclick={closeUserMenu} role="menuitem">Admin</a>
        {/if}
        <button type="button" class="user-menu-item danger" onclick={() => { closeUserMenu(); void onLogout(); }} role="menuitem">
          Log out
        </button>
      </div>
    {/if}
  </div>
</aside>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 100;
    width: 224px;
    display: flex;
    flex-direction: column;
    padding: 16px 12px;
    background: rgba(18, 18, 30, 0.94);
    backdrop-filter: blur(28px) saturate(160%);
    -webkit-backdrop-filter: blur(28px) saturate(160%);
    border-right: 1px solid rgba(255, 255, 255, 0.07);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.18);
    color: rgba(255, 255, 255, 0.7);
    font-family: var(--font-sans);
    transition:
      width 240ms cubic-bezier(0.4, 0, 0.2, 1),
      padding 240ms;
    overflow: hidden;
  }
  .sidebar.collapsed {
    width: 64px;
    padding: 16px 10px;
  }

  /* Brand */
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 8px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    margin-bottom: 10px;
    text-decoration: none;
    color: inherit;
  }
  .sidebar.collapsed .brand {
    justify-content: center;
    padding: 4px 0 14px;
    gap: 0;
  }
  .brand-mark {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #9b7fe8 0%, #e87b5a 60%, #f0a060 100%);
    box-shadow: 0 2px 10px rgba(155, 127, 232, 0.4);
  }
  .brand-label {
    display: flex;
    flex-direction: column;
    line-height: 1.1;
    white-space: nowrap;
    overflow: hidden;
  }
  .brand-name {
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.01em;
  }
  .brand-version {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.35);
    margin-top: 2px;
  }

  /* Nav */
  .nav {
    display: flex;
    flex-direction: column;
    gap: 0;
  }
  .section-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: rgba(255, 255, 255, 0.18);
    padding: 10px 10px 4px;
    text-transform: uppercase;
  }
  .section-spacer {
    height: 8px;
  }
  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid transparent;
    margin-bottom: 2px;
    color: rgba(255, 255, 255, 0.62);
    background: transparent;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    line-height: 1;
    transition:
      background 150ms,
      color 150ms,
      border-color 150ms;
    overflow: hidden;
    white-space: nowrap;
    user-select: none;
  }
  .sidebar.collapsed .nav-item {
    justify-content: center;
    gap: 0;
    padding: 9px 0;
  }
  .nav-item:hover {
    background: rgba(255, 255, 255, 0.07);
    color: #c4c4d8;
    text-decoration: none;
  }
  .nav-item.active {
    background: rgba(240, 115, 64, 0.18);
    border-color: rgba(240, 115, 64, 0.22);
    color: #f5905d;
  }
  .nav-icon {
    display: inline-flex;
    flex-shrink: 0;
  }
  .nav-label {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .spacer {
    flex: 1;
  }

  /* Toggle */
  .toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.09);
    background: rgba(255, 255, 255, 0.06);
    color: #9f9fb8;
    cursor: pointer;
    margin: 0 0 10px;
    transition: background 150ms, color 150ms;
  }
  .toggle.floats {
    align-self: center;
  }
  .toggle:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #fff;
  }
  .toggle:focus-visible {
    outline: 2px solid #f07340;
    outline-offset: 2px;
  }

  /* User row */
  .user {
    position: relative;
    padding: 10px 0 4px;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
  }
  .user-trigger {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 4px 8px;
    background: transparent;
    border: none;
    color: inherit;
    cursor: pointer;
    text-align: left;
    border-radius: 8px;
    transition: background 150ms;
  }
  .user-trigger:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  .sidebar.collapsed .user-trigger {
    justify-content: center;
    gap: 0;
    padding: 4px 0;
  }
  .avatar {
    flex-shrink: 0;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #f07340, #f5905d);
  }
  .avatar.admin {
    background: linear-gradient(135deg, #8b72e0, #6b9be8);
  }
  .avatar.reviewer {
    background: linear-gradient(135deg, #6b9be8, #8bb3ee);
  }
  .user-text {
    display: flex;
    flex-direction: column;
    gap: 3px;
    overflow: hidden;
    min-width: 0;
  }
  .user-name {
    font-size: 12px;
    font-weight: 600;
    color: #c4c4d8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .user-menu {
    position: absolute;
    left: 0;
    right: 0;
    bottom: calc(100% + 6px);
    background: rgba(28, 28, 44, 0.98);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.32);
    z-index: 1;
  }
  .user-menu-item {
    display: block;
    width: 100%;
    padding: 9px 12px;
    background: transparent;
    border: none;
    text-align: left;
    color: rgba(255, 255, 255, 0.85);
    font-size: 12px;
    font-family: inherit;
    text-decoration: none;
    cursor: pointer;
  }
  .user-menu-item:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
    text-decoration: none;
  }
  .user-menu-item.danger {
    color: #fecaca;
  }
  .user-menu-item.danger:hover {
    background: rgba(217, 59, 59, 0.18);
    color: #ffd0d0;
  }
</style>
