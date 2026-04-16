import { api } from './client';

export type TaxonomyEntry = {
  taxonomy_entry_id: string;
  domain: string;
  value: string;
  label: string;
  sort_order: number;
  color?: string | null;
  is_active: boolean;
};

export type TaxonomyVersion = {
  taxonomy_version_id: string;
  version_number: number;
  description?: string | null;
  is_current: boolean;
  created_at: string;
  updated_at: string;
  domains: Record<string, TaxonomyEntry[]>;
};

export const taxonomyApi = {
  current: () => api.get<TaxonomyVersion>('/api/taxonomy/current'),
  versions: () => api.get<TaxonomyVersion[]>('/api/taxonomy/versions'),
};
