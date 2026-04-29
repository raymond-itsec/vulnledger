<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import '../app.css';
  import { auth, bootstrapAuth, logout } from '$lib/stores/auth.svelte';
  import { appAvailability } from '$lib/stores/app-availability.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import AvailabilityBanner from '$lib/components/AvailabilityBanner.svelte';
  import ToastViewport from '$lib/components/ToastViewport.svelte';
  import { APP_VERSION } from '$lib/config/app-meta';
  import { APP_BASE_PATH, LOGIN_PATH } from '$lib/config/routes';
  import { page } from '$app/state';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
  let authReady = $state(false);
  let userMenuOpen = $state(false);
  let userMenuRoot = $state<HTMLDivElement | null>(null);
  const AUTH_BOOTSTRAP_TIMEOUT_MS = 10000;
  const PUBLIC_PATH_PREFIXES = ['/login', '/invite', '/onboarding'];

  const navItems = [
    { href: APP_BASE_PATH, label: 'Dashboard', icon: '⊞' },
    { href: `${APP_BASE_PATH}/clients`, label: 'Clients', icon: '⊟' },
    { href: `${APP_BASE_PATH}/assets`, label: 'Assets', icon: '⊠' },
    { href: `${APP_BASE_PATH}/sessions`, label: 'Sessions', icon: '⊡' },
    { href: `${APP_BASE_PATH}/findings`, label: 'Findings', icon: '⊘' },
    { href: `${APP_BASE_PATH}/admin`, label: 'Admin', icon: '⚙', roles: ['admin'] },
    { href: `${APP_BASE_PATH}/templates`, label: 'Templates', icon: '⊙', roles: ['admin', 'reviewer'] },
  ];

  let visibleNav = $derived(
    navItems.filter((item) => {
      if (!item.roles) return true;
      return auth.user && item.roles.includes(auth.user.role);
    })
  );

  function isPublicRoute(pathname: string): boolean {
    if (pathname === '/') return true;
    return PUBLIC_PATH_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
  }

  function normalizedAppPath(pathname: string): string {
    if (pathname === APP_BASE_PATH) return APP_BASE_PATH;
    if (pathname.startsWith(`${APP_BASE_PATH}/`)) return pathname;
    if (pathname !== '/' && !isPublicRoute(pathname)) return `${APP_BASE_PATH}${pathname}`;
    return pathname;
  }

  function isActive(href: string, currentPath: string): boolean {
    const normalized = normalizedAppPath(currentPath);
    if (href === APP_BASE_PATH) {
      return normalized === APP_BASE_PATH;
    }
    return normalized.startsWith(href);
  }

  onMount(() => {
    let unmounted = false;
    void (async () => {
      try {
        await Promise.race([
          bootstrapAuth(),
          new Promise<void>((resolve) => {
            setTimeout(resolve, AUTH_BOOTSTRAP_TIMEOUT_MS);
          }),
        ]);
        if (!unmounted && auth.isAuthenticated && !appAvailability.unavailable) {
          await taxonomy.load();
        }
      } catch (error) {
        console.error('[auth-bootstrap] startup failed', error);
      } finally {
        if (!unmounted) {
          authReady = true;
        }
      }
    })();

    return () => {
      unmounted = true;
      appAvailability.stop();
    };
  });

  $effect(() => {
    appAvailability.setAuthToken(auth.token);
  });

  $effect(() => {
    if (!authReady || !auth.isAuthenticated) {
      appAvailability.stop();
      return;
    }
    appAvailability.start();
  });

  $effect(() => {
    if (authReady && !auth.isAuthenticated && !isPublicRoute(page.url.pathname)) {
      goto(LOGIN_PATH, { replaceState: true });
    }
  });

  $effect(() => {
    if (authReady && auth.isAuthenticated && isPublicRoute(page.url.pathname)) {
      goto(APP_BASE_PATH, { replaceState: true });
    }
  });

  $effect(() => {
    if (authReady && !appAvailability.unavailable && auth.isAuthenticated && !taxonomy.current && !taxonomy.loading) {
      void taxonomy.load();
    }
  });

  async function handleLogout() {
    userMenuOpen = false;
    await logout();
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
    if (target && !userMenuRoot.contains(target)) {
      userMenuOpen = false;
    }
  }

  function handleWindowKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      userMenuOpen = false;
    }
  }

  onMount(() => {
    document.addEventListener('click', handleDocumentClick);
    return () => {
      document.removeEventListener('click', handleDocumentClick);
    };
  });
</script>

<svelte:window onkeydown={handleWindowKeydown} />

<AvailabilityBanner />

{#if !authReady}
  <main class="content loading-shell">
    <p>Loading...</p>
  </main>
{:else if !auth.isAuthenticated}
  {#if isPublicRoute(page.url.pathname)}
    {@render children()}
  {:else}
    <main class="content loading-shell">
      <p>Redirecting to login...</p>
    </main>
  {/if}
{:else}
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <img class="sidebar-logo" src="/branding/vl-logo-small.png" alt="VulnLedger logo" />
        <span class="version">{APP_VERSION}</span>
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
      <div class="sidebar-footer" bind:this={userMenuRoot}>
        <button class="user-trigger" onclick={toggleUserMenu}>
          <div class="user-info">
            <div class="user-name">{auth.user?.full_name || auth.user?.username}</div>
            <div class="user-role">{auth.user?.role?.replace('_', ' ')}</div>
          </div>
          <span class="user-trigger-caret">{userMenuOpen ? '▴' : '▾'}</span>
        </button>
        {#if userMenuOpen}
          <div class="user-menu">
            <a class="user-menu-item" href={`${APP_BASE_PATH}/profile`} onclick={closeUserMenu}>Profile settings</a>
            {#if auth.user?.role === 'admin'}
              <a class="user-menu-item" href={`${APP_BASE_PATH}/admin`} onclick={closeUserMenu}>Admin</a>
            {/if}
            <button class="user-menu-item danger" onclick={handleLogout}>Log out</button>
          </div>
        {/if}
      </div>
    </aside>
    <main class="content">
      {@render children()}
    </main>
  </div>
{/if}

<ToastViewport />

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
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  .sidebar-logo {
    width: 11rem;
    height: auto;
    flex-shrink: 0;
    object-fit: contain;
  }
  .version {
    display: block;
    font-size: 0.7rem;
    opacity: 0.55;
  }
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
    position: relative;
    padding: 1rem 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  .user-trigger {
    width: 100%;
    padding: 0.625rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 0.375rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
    text-align: left;
  }
  .user-trigger:hover { background: rgba(255, 255, 255, 0.2); }
  .user-info { margin: 0; }
  .user-name { font-size: 0.875rem; font-weight: 600; }
  .user-role { font-size: 0.75rem; opacity: 0.6; text-transform: capitalize; }
  .user-trigger-caret {
    font-size: 0.75rem;
    opacity: 0.75;
  }
  .user-menu {
    position: absolute;
    left: 1.5rem;
    right: 1.5rem;
    bottom: calc(100% + 0.5rem);
    background: rgba(23, 30, 20, 0.98);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 0.5rem;
    overflow: hidden;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.32);
  }
  .user-menu-item {
    display: block;
    width: 100%;
    padding: 0.625rem 0.75rem;
    background: transparent;
    border: none;
    text-align: left;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.82rem;
    text-decoration: none;
    cursor: pointer;
  }
  .user-menu-item:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  .user-menu-item.danger {
    color: #fecaca;
  }
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
