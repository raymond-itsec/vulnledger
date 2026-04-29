<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import '../app.css';
  import { auth, bootstrapAuth, logout } from '$lib/stores/auth.svelte';
  import { appAvailability } from '$lib/stores/app-availability.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import AvailabilityBanner from '$lib/components/AvailabilityBanner.svelte';
  import AppSidebar from '$lib/components/AppSidebar.svelte';
  import type { NavItem } from '$lib/components/AppSidebar.svelte';
  import AppTopbar from '$lib/components/AppTopbar.svelte';
  import ToastViewport from '$lib/components/ToastViewport.svelte';
  import { APP_VERSION } from '$lib/config/app-meta';
  import { APP_BASE_PATH, LOGIN_PATH } from '$lib/config/routes';
  import { breadcrumb } from '$lib/stores/breadcrumb.svelte';
  import type { Crumb } from '$lib/stores/breadcrumb.svelte';
  import { sidebar } from '$lib/stores/sidebar.svelte';
  import { page } from '$app/state';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
  let authReady = $state(false);
  const AUTH_BOOTSTRAP_TIMEOUT_MS = 10000;

  const sidebarCollapsed = $derived(sidebar.collapsed);
  const PUBLIC_PATH_PREFIXES = [
    '/login', '/invite', '/onboarding',
    '/about', '/help', '/trust', '/privacy', '/terms', '/guidelines', '/contact', '/support',
  ];

  type AppNavItem = NavItem & { roles?: string[] };

  const navItems: AppNavItem[] = [
    { href: APP_BASE_PATH, label: 'Dashboard', icon: 'dashboard' },
    { href: `${APP_BASE_PATH}/clients`, label: 'Clients', icon: 'clients' },
    { href: `${APP_BASE_PATH}/assets`, label: 'Assets', icon: 'assets' },
    { href: `${APP_BASE_PATH}/sessions`, label: 'Sessions', icon: 'sessions' },
    { href: `${APP_BASE_PATH}/findings`, label: 'Findings', icon: 'findings' },
    { href: `${APP_BASE_PATH}/admin`, label: 'Admin', icon: 'admin', section: 'Administration', roles: ['admin'] },
    { href: `${APP_BASE_PATH}/templates`, label: 'Templates', icon: 'templates', section: 'Administration', roles: ['admin', 'reviewer'] },
  ];

  let visibleNav = $derived(
    navItems.filter((item) => {
      if (!item.roles) return true;
      return auth.user && item.roles.includes(auth.user.role);
    }),
  );

  const sectionTitle = $derived.by(() => {
    const pathname = normalizedAppPath(page.url.pathname);
    if (pathname === APP_BASE_PATH) return 'Dashboard';
    const match = navItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));
    return match?.label ?? 'Workspace';
  });

  // Crumbs come from the breadcrumb store when a page sets them; otherwise we
  // synthesize a sensible default from the path. Pages can call setCrumbs() in
  // onMount to override (see frontend/src/lib/stores/breadcrumb.svelte.ts).
  const crumbs = $derived.by<Crumb[]>(() => {
    if (breadcrumb.crumbs && breadcrumb.crumbs.length > 0) return breadcrumb.crumbs;
    const pathname = normalizedAppPath(page.url.pathname);
    if (pathname === APP_BASE_PATH) return [{ label: 'Dashboard' }];
    const match = navItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));
    if (!match) return [{ label: 'Workspace' }];
    if (pathname === match.href) return [{ label: match.label }];
    return [{ label: match.label, href: match.href }, { label: 'Detail' }];
  });

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
    await logout();
  }
</script>

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
  <div class="app-layout" class:sidebar-collapsed={sidebarCollapsed}>
    <AppSidebar
      items={visibleNav}
      activeHref={page.url.pathname}
      user={auth.user}
      role={auth.user?.role ?? null}
      version={APP_VERSION}
      onLogout={handleLogout}
      profileHref={`${APP_BASE_PATH}/profile`}
      adminHref={`${APP_BASE_PATH}/admin`}
    />
    <main class="content">
      <AppTopbar {crumbs} title={sectionTitle}>
        {#snippet actions()}
          {#if auth.user?.role === 'admin' || auth.user?.role === 'reviewer'}
            <a class="topbar-cta" href={`${APP_BASE_PATH}/findings?new=1`}>+ New finding</a>
          {/if}
        {/snippet}
      </AppTopbar>
      <div class="content-inner">
        {@render children()}
      </div>
    </main>
  </div>
{/if}

<ToastViewport />

<style>
  .app-layout {
    display: flex;
    min-height: 100vh;
    background: var(--bg-page, #f2ede6);
  }
  .content {
    flex: 1;
    margin-left: 224px;
    min-height: 100vh;
    background: transparent;
    transition: margin-left 240ms cubic-bezier(0.4, 0, 0.2, 1);
  }
  .app-layout.sidebar-collapsed .content {
    margin-left: 64px;
  }
  .topbar-cta {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 7px 14px;
    border-radius: 10px;
    background: #f07340;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    box-shadow: 0 2px 8px rgba(240, 115, 64, 0.3);
    transition: background 150ms;
  }
  .topbar-cta:hover {
    background: #d96530;
    text-decoration: none;
  }
  .content-inner {
    padding: 20px 28px 32px;
  }
  .loading-shell {
    margin-left: 0;
  }
</style>
