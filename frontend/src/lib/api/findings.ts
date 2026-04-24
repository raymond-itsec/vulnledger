import { api } from './client';
import type { PaginatedResponse } from './types';

export interface Finding {
  finding_id: string;
  session_id: string;
  title: string;
  description: string;
  risk_level: string;
  impact: string | null;
  recommendation: string | null;
  remediation_status: string;
  references: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface FindingHistory {
  history_id: string;
  finding_id: string;
  changed_by: string;
  changed_by_name: string | null;
  changed_at: string;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
}

export const findingsApi = {
  list: (params?: {
    session_id?: string;
    risk_level?: string;
    remediation_status?: string;
    search?: string;
    page?: number;
    per_page?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.session_id) qs.set('session_id', params.session_id);
    if (params?.risk_level) qs.set('risk_level', params.risk_level);
    if (params?.remediation_status) qs.set('remediation_status', params.remediation_status);
    if (params?.search) qs.set('search', params.search);
    qs.set('page', String(params?.page || 1));
    qs.set('per_page', String(params?.per_page || 25));
    return api.get<PaginatedResponse<Finding>>(`/api/findings?${qs}`);
  },
  get: (id: string) => api.get<Finding>(`/api/findings/${id}`),
  create: (data: Partial<Finding>) => api.post<Finding>('/api/findings', data),
  update: (id: string, data: Partial<Finding>) => api.patch<Finding>(`/api/findings/${id}`, data),
  history: (id: string) => api.get<FindingHistory[]>(`/api/findings/${id}/history`),
};
