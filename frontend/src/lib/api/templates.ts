import { api } from './client';
import type { PaginatedResponse } from './types';

export interface Template {
  template_id: string;
  stable_id: string;
  name: string;
  category: string | null;
  is_builtin: boolean;
  title: string | null;
  description: string | null;
  risk_level: string | null;
  impact: string | null;
  recommendation: string | null;
  references: string[] | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export const templatesApi = {
  list: (category?: string, page = 1, perPage = 100) => {
    const qs = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (category) qs.set('category', category);
    return api.get<PaginatedResponse<Template>>(`/api/templates?${qs}`);
  },
  get: (id: string) => api.get<Template>(`/api/templates/${id}`),
  create: (data: Partial<Template>) => api.post<Template>('/api/templates', data),
  update: (id: string, data: Partial<Template>) => api.patch<Template>(`/api/templates/${id}`, data),
  delete: (id: string) => api.delete<void>(`/api/templates/${id}`),
};
