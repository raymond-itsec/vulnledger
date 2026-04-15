import { api } from './client';
import type { PaginatedResponse } from './types';

export interface Client {
  client_id: string;
  company_name: string;
  primary_contact_name: string | null;
  primary_contact_email: string | null;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export const clientsApi = {
  list: (page = 1, perPage = 25) =>
    api.get<PaginatedResponse<Client>>(`/api/clients?page=${page}&per_page=${perPage}`),
  get: (id: string) => api.get<Client>(`/api/clients/${id}`),
  create: (data: Partial<Client>) => api.post<Client>('/api/clients', data),
  update: (id: string, data: Partial<Client>) => api.patch<Client>(`/api/clients/${id}`, data),
};
