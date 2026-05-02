import { api } from './client';
import type { PaginatedResponse } from './types';

export interface SessionInfo {
  refresh_session_id: string;
  family_id: string;
  issued_at: string;
  last_seen_at: string;
  ip_address: string | null;
  user_agent: string | null;
  is_current: boolean;
}

export interface SessionRevokeResponse {
  revoked: boolean;
  refresh_session_id: string;
}

export interface SessionRevokeAllResponse {
  revoked_count: number;
}

export interface SecurityEventInfo {
  security_event_id: string;
  event_type: string;
  occurred_at: string;
  family_id: string | null;
  refresh_session_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  details: Record<string, unknown> | null;
}

export const authApi = {
  listSessions: (page = 1, perPage = 50) =>
    api.get<PaginatedResponse<SessionInfo>>(
      `/api/v1/auth/sessions?page=${page}&per_page=${perPage}`,
    ),
  revokeSession: (refreshSessionId: string) =>
    api.post<SessionRevokeResponse>(`/api/v1/auth/sessions/${refreshSessionId}/revoke`, {}),
  revokeAllSessions: () =>
    api.post<SessionRevokeAllResponse>('/api/v1/auth/sessions/revoke-all', {}),
  listSecurityEvents: (page = 1, perPage = 20) =>
    api.get<PaginatedResponse<SecurityEventInfo>>(
      `/api/v1/auth/security-events?page=${page}&per_page=${perPage}`,
    ),
};
