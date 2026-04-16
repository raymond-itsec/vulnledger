import { api } from './client';
import type { PaginatedResponse } from './types';

export interface User {
  user_id: string;
  username: string;
  full_name: string | null;
  company_name: string | null;
  email: string;
  role: string;
  linked_client_id: string | null;
  is_active: boolean;
}

export const usersApi = {
  list: (page = 1, perPage = 25) =>
    api.get<PaginatedResponse<User>>(`/api/users?page=${page}&per_page=${perPage}`),
  listReviewers: () => api.get<User[]>('/api/users/reviewers'),
  get: (id: string) => api.get<User>(`/api/users/${id}`),
  create: (data: Record<string, unknown>) => api.post<User>('/api/users', data),
  update: (id: string, data: Partial<User>) => api.patch<User>(`/api/users/${id}`, data),
};
