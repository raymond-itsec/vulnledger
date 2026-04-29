import { api } from './client';
import type { PaginatedResponse } from './types';

export interface Invite {
  invite_id: string;
  code: string;
  email: string;
  source: string;
  expires_at: string | null;
  claimed_at: string | null;
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface InviteCreateRequest {
  email: string;
  expires_at?: string | null;
}

export interface InviteRevokeResponse {
  revoked: boolean;
  invite_id: string;
}

export const invitesApi = {
  list: (page = 1, perPage = 25) =>
    api.get<PaginatedResponse<Invite>>(`/api/invites?page=${page}&per_page=${perPage}`),
  create: (body: InviteCreateRequest) =>
    api.post<Invite>('/api/invites', body),
  revoke: (inviteId: string) =>
    api.post<InviteRevokeResponse>(`/api/invites/${inviteId}/revoke`, {}),
};
