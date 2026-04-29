import { readPublicErrorMessage } from '$lib/api/errors';
import {
  APPLICATION_UNAVAILABLE_MESSAGE,
  appAvailability,
  fetchWithAvailability,
} from '$lib/stores/app-availability.svelte';

export interface InviteVerifyResponse {
  email: string;
}

export interface OnboardingStateResponse {
  email: string;
}

export interface OnboardingCompleteRequest {
  username: string;
  password: string;
  full_name?: string | null;
  company_name?: string | null;
}

export interface OnboardingCompleteResponse {
  username: string;
  email: string;
}

async function parseJson<T>(res: Response): Promise<T> {
  return res.json() as Promise<T>;
}

async function publicJsonRequest<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetchWithAvailability(
    path,
    {
      credentials: 'include',
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init.headers || {}),
      },
    },
    true,
  );

  if (!response.ok) {
    if (appAvailability.unavailable) {
      throw new Error(APPLICATION_UNAVAILABLE_MESSAGE);
    }
    throw new Error(await readPublicErrorMessage(response));
  }

  return parseJson<T>(response);
}

export const onboardingApi = {
  verifyInvite: (inviteCode: string) =>
    publicJsonRequest<InviteVerifyResponse>('/api/invites/verify', {
      method: 'POST',
      body: JSON.stringify({ invite_code: inviteCode }),
    }),
  getState: () =>
    publicJsonRequest<OnboardingStateResponse>('/api/onboarding/state', {
      method: 'GET',
      headers: {},
    }),
  complete: (body: OnboardingCompleteRequest) =>
    publicJsonRequest<OnboardingCompleteResponse>('/api/onboarding/complete', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
