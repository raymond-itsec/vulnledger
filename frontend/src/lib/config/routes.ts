export const APP_BASE_PATH = '/app';
export const LOGIN_PATH = '/login';
export const INVITE_PATH = '/invite';
export const ONBOARDING_PATH = '/onboarding';

export function appPath(path = ''): string {
  if (!path || path === '/') return APP_BASE_PATH;
  return `${APP_BASE_PATH}${path.startsWith('/') ? path : `/${path}`}`;
}
