import { api } from './client';
import type { PaginatedResponse } from './types';

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
  versions: (page = 1, perPage = 50) =>
    api.get<PaginatedResponse<TaxonomyVersion>>(
      `/api/taxonomy/versions?page=${page}&per_page=${perPage}`,
    ),
};
