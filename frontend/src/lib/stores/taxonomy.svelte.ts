import { taxonomyApi, type TaxonomyEntry, type TaxonomyVersion } from '$lib/api/taxonomy';

function humanize(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

let state = $state({
  current: null as TaxonomyVersion | null,
  loading: false,
  loadPromise: null as Promise<void> | null,
});

function sortedEntries(entries: TaxonomyEntry[] | undefined): TaxonomyEntry[] {
  return [...(entries || [])].sort((a, b) => a.sort_order - b.sort_order || a.label.localeCompare(b.label));
}

export const taxonomy = {
  get current() {
    return state.current;
  },
  get versionNumber() {
    return state.current?.version_number ?? null;
  },
  get loading() {
    return state.loading;
  },
  async load(force = false) {
    if (!force && state.current) return;
    if (!force && state.loadPromise) {
      await state.loadPromise;
      return;
    }

    state.loading = true;
    state.loadPromise = (async () => {
      try {
        state.current = await taxonomyApi.current();
      } finally {
        state.loading = false;
        state.loadPromise = null;
      }
    })();
    await state.loadPromise;
  },
  activeEntries(domain: string): TaxonomyEntry[] {
    return sortedEntries(state.current?.domains[domain]).filter((entry) => entry.is_active);
  },
  entry(domain: string, value: string): TaxonomyEntry | undefined {
    return state.current?.domains[domain]?.find((entry) => entry.value === value);
  },
  label(domain: string, value: string): string {
    const match = this.entry(domain, value);
    return match?.label || humanize(value);
  },
  color(domain: string, value: string, fallback = '#6b7280'): string {
    const match = this.entry(domain, value);
    return match?.color || fallback;
  },
  hasEntry(domain: string, value: string): boolean {
    return !!this.entry(domain, value);
  },
  isAllowed(domain: string, value: string): boolean {
    return this.activeEntries(domain).some((entry) => entry.value === value);
  },
};
