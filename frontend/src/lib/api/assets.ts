import { api } from './client';
import type { PaginatedResponse } from './types';

export interface Asset {
  asset_id: string;
  client_id: string;
  asset_name: string;
  asset_type: string;
  description: string | null;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export const assetsApi = {
  list: (clientId?: string, page = 1, perPage = 25) => {
    const qs = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (clientId) qs.set('client_id', clientId);
    return api.get<PaginatedResponse<Asset>>(`/api/assets?${qs}`);
  },
  get: (id: string) => api.get<Asset>(`/api/assets/${id}`),
  create: (data: Partial<Asset>) => api.post<Asset>('/api/assets', data),
  update: (id: string, data: Partial<Asset>) => api.patch<Asset>(`/api/assets/${id}`, data),
};
