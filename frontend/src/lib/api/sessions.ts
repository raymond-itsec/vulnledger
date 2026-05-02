import { api } from './client';
import type { PaginatedResponse } from './types';

export interface Session {
  session_id: string;
  asset_id: string;
  review_name: string;
  review_date: string;
  reviewer_id: string;
  reviewer_name: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export const sessionsApi = {
  list: (assetId?: string, page = 1, perPage = 25) => {
    const qs = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (assetId) qs.set('asset_id', assetId);
    return api.get<PaginatedResponse<Session>>(`/api/v1/sessions?${qs}`);
  },
  get: (id: string) => api.get<Session>(`/api/v1/sessions/${id}`),
  create: (data: Partial<Session>) => api.post<Session>('/api/v1/sessions', data),
  update: (id: string, data: Partial<Session>) =>
    api.patch<Session>(`/api/v1/sessions/${id}`, data),
};
