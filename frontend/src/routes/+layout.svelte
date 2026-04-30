<script lang="ts">
  import { onMount, setContext } from 'svelte';
  import { goto } from '$app/navigation';
  import '../app.css';
  import { auth, bootstrapAuth, logout } from '$lib/stores/auth.svelte';
  import { appAvailability } from '$lib/stores/app-availability.svelte';
  import { taxonomy } from '$lib/stores/taxonomy.svelte';
  import AvailabilityBanner from '$lib/components/AvailabilityBanner.svelte';
  import AppSidebar from '$lib/components/AppSidebar.svelte';
  import type { NavItem } from '$lib/components/AppSidebar.svelte';
  import AppTopbar from '$lib/components/AppTopbar.svelte';
  import PublicFooter from '$lib/components/PublicFooter.svelte';
  import ToastViewport from '$lib/components/ToastViewport.svelte';
  import { APP_SHELL_CONTEXT_KEY } from '$lib/components/app-shell-context';
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
  // Two categories:
  //   AUTH_GATEWAY_PREFIXES — pages that exist only to onboard / sign in.
  //     Authenticated users get redirected away from these to /app.
  //   INFO_PUBLIC_PREFIXES — universal info / legal pages reachable by
  //     anyone (signed in or not). Listed in PUBLIC_PATH_PREFIXES so the
  //     auth-required gate doesn't bounce signed-out visitors.
  const AUTH_GATEWAY_PREFIXES = ['/login', '/invite', '/onboarding'];
  const INFO_PUBLIC_PREFIXES = [
    '/about', '/help', '/trust', '/privacy', '/terms', '/guidelines', '/contact', '/support',
  ];
  const PUBLIC_PATH_PREFIXES = [...AUTH_GATEWAY_PREFIXES, ...INFO_PUBLIC_PREFIXES];

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

  // True only for pages an authenticated user should be bounced away from
  // (login, invite, onboarding, root waitlist). Universal info pages like
  // /about, /trust, /privacy etc. return false here so signed-in users can
  // navigate to them via the footer without being redirected back to /app.
  function isAuthGatewayRoute(pathname: string): boolean {
    if (pathname === '/') return true;
    return AUTH_GATEWAY_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
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

  // Only bounce signed-in users away from auth-gateway pages (/login,
  // /invite, /onboarding, /). Info pages (/about, /trust, etc.) stay
  // accessible — clicking them from the in-app PublicFooter navigates
  // normally instead of triggering a redirect loop that would re-mount
  // the dashboard and re-fire its API calls.
  $effect(() => {
    if (authReady && auth.isAuthenticated && isAuthGatewayRoute(page.url.pathname)) {
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

  // Tell descendants whether the /app shell (sidebar + topbar + footer) is
  // currently wrapping them. PublicShell reads this and downgrades to a
  // bare children-only render so navigating an authenticated user to
  // /trust et al. doesn't double up the chrome.
  const isAppShellActive = $derived(authReady && auth.isAuthenticated);
  setContext(APP_SHELL_CONTEXT_KEY, () => isAppShellActive);
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
      <AppTopbar {crumbs}>
        {#snippet actions()}
          {#if auth.user?.role === 'admin' || auth.user?.role === 'reviewer'}
            <a class="topbar-cta" href={`${APP_BASE_PATH}/findings?new=1`}>+ New finding</a>
          {/if}
        {/snippet}
      </AppTopbar>
      <div class="content-inner">
        {@render children()}
      </div>
      <PublicFooter />
    </main>
  </div>
{/if}

<ToastViewport />

<style>
  /* Same warm pastel-glass gradient as the public pages so the
     visual transition between login/waitlist and /app feels seamless. */
  .app-layout {
    display: flex;
    min-height: 100vh;
    background:
      radial-gradient(ellipse 80% 60% at 15% 25%, rgba(255, 180, 150, 0.4) 0%, transparent 55%),
      radial-gradient(ellipse 70% 55% at 95% 15%, rgba(255, 200, 220, 0.3) 0%, transparent 60%),
      radial-gradient(ellipse 90% 70% at 85% 90%, rgba(180, 155, 245, 0.32) 0%, transparent 60%),
      linear-gradient(160deg, #fae2d8 0%, #f3d0e8 30%, #e0cdf5 60%, #d4d8f5 85%, #dad5f0 100%);
    background-attachment: fixed;
  }
  .content {
    flex: 1;
    margin-left: 224px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: transparent;
    transition: margin-left 240ms cubic-bezier(0.4, 0, 0.2, 1);
  }
  .app-layout.sidebar-collapsed .content {
    margin-left: 64px;
  }
  .content > :global(.content-inner) {
    flex: 1;
  }
  /* Public footer needs a translucent surface here so the gradient
     shows through, matching the rest of /app's glassy treatment. */
  .content > :global(.public-footer) {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
    border-top: 1px solid rgba(255, 255, 255, 0.55);
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
