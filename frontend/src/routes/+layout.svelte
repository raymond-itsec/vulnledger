<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';
  import { auth, bootstrapAuth, logout } from '$lib/stores/auth.svelte';
  import { page } from '$app/state';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
  let authReady = $state(false);

  const navItems = [
    { href: '/', label: 'Dashboard', icon: '⊞' },
    { href: '/clients', label: 'Clients', icon: '⊟' },
    { href: '/assets', label: 'Assets', icon: '⊠' },
    { href: '/sessions', label: 'Sessions', icon: '⊡' },
    { href: '/findings', label: 'Findings', icon: '⊘' },
    { href: '/templates', label: 'Templates', icon: '⊙', roles: ['admin', 'reviewer'] },
  ];

  let visibleNav = $derived(
    navItems.filter((item) => {
      if (!item.roles) return true;
      return auth.user && item.roles.includes(auth.user.role);
    })
  );

  function isActive(href: string, currentPath: string): boolean {
    if (href === '/') return currentPath === '/';
    return currentPath.startsWith(href);
  }

  onMount(async () => {
    await bootstrapAuth();
    authReady = true;
  });
</script>

{#if !authReady}
  <main class="content loading-shell">
    <p>Loading...</p>
  </main>
{:else if !auth.isAuthenticated}
  {@render children()}
{:else}
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1>Findings</h1>
        <span class="version">v0.1</span>
      </div>
      <nav>
        {#each visibleNav as item}
          <a
            href={item.href}
            class="nav-item"
            class:active={isActive(item.href, page.url.pathname)}
          >
            <span class="nav-icon">{item.icon}</span>
            {item.label}
          </a>
        {/each}
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-name">{auth.user?.full_name || auth.user?.username}</div>
          <div class="user-role">{auth.user?.role?.replace('_', ' ')}</div>
        </div>
        <button class="logout-btn" onclick={logout}>Logout</button>
      </div>
    </aside>
    <main class="content">
      {@render children()}
    </main>
  </div>
{/if}

<style>
  .app-layout {
    display: flex;
    min-height: 100vh;
  }
  .sidebar {
    width: 240px;
    background: var(--sidebar-bg);
    color: var(--text-light);
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 100;
  }
  .sidebar-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }
  .sidebar-header h1 { font-size: 1.25rem; font-weight: 700; }
  .version { font-size: 0.7rem; opacity: 0.5; }
  nav {
    flex: 1;
    padding: 0.75rem 0;
  }
  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.625rem 1.5rem;
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    font-size: 0.9rem;
    transition: all 0.15s;
  }
  .nav-item:hover {
    background: var(--sidebar-hover);
    color: white;
    text-decoration: none;
  }
  .nav-item.active {
    background: var(--sidebar-active);
    color: white;
    border-right: 3px solid var(--accent);
  }
  .nav-icon { font-size: 1rem; width: 1.25rem; text-align: center; }
  .sidebar-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  .user-info { margin-bottom: 0.75rem; }
  .user-name { font-size: 0.875rem; font-weight: 600; }
  .user-role { font-size: 0.75rem; opacity: 0.6; text-transform: capitalize; }
  .logout-btn {
    width: 100%;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 0.375rem;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.8rem;
    cursor: pointer;
  }
  .logout-btn:hover { background: rgba(255, 255, 255, 0.2); }
  .content {
    flex: 1;
    margin-left: 240px;
    padding: 2rem;
    min-height: 100vh;
  }
  .loading-shell {
    margin-left: 0;
  }
</style>
