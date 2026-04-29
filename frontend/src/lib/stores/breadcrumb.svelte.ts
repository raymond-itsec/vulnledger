// Breadcrumb state shared across the layout.
// Each page/route can override the trail via setCrumbs(). When a page
// hasn't set anything, the layout falls back to a path-derived default.
//
// Usage in a route component:
//
//   import { setCrumbs, clearCrumbs } from '$lib/stores/breadcrumb.svelte';
//   import { onMount } from 'svelte';
//   onMount(() => {
//     setCrumbs([
//       { label: 'Clients', href: '/app/clients' },
//       { label: client.name },               // current page (no href)
//     ]);
//     return clearCrumbs;                     // tidy on unmount
//   });

export interface Crumb {
  label: string;
  href?: string;
}

let crumbs = $state<Crumb[] | null>(null);

export const breadcrumb = {
  get crumbs() {
    return crumbs;
  },
};

export function setCrumbs(next: Crumb[] | null) {
  crumbs = next;
}

export function clearCrumbs() {
  crumbs = null;
}
