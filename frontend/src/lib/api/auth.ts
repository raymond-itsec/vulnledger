import { api } from './client';

export interface SessionInfo {
  refresh_session_id: string;
  family_id: string;
  issued_at: string;
  last_seen_at: string;
  ip_address: string | null;
  user_agent: string | null;
  is_current: boolean;
}

export interface SessionListResponse {
  items: SessionInfo[];
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

export interface SecurityEventListResponse {
  items: SecurityEventInfo[];
  limit: number;
}

export const authApi = {
  listSessions: () => api.get<SessionListResponse>('/api/auth/sessions'),
  revokeSession: (refreshSessionId: string) =>
    api.post<SessionRevokeResponse>(`/api/auth/sessions/${refreshSessionId}/revoke`, {}),
  revokeAllSessions: () =>
    api.post<SessionRevokeAllResponse>('/api/auth/sessions/revoke-all', {}),
  listSecurityEvents: (limit = 20) =>
    api.get<SecurityEventListResponse>(`/api/auth/security-events?limit=${limit}`),
};
