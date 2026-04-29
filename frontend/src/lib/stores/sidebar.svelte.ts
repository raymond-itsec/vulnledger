// Sidebar collapse state, persisted in localStorage so the user's
// preference survives reloads and route changes.

const STORAGE_KEY = 'vl_sidebar_collapsed';

function readInitial(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return window.localStorage.getItem(STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

let collapsed = $state<boolean>(readInitial());

function persist(value: boolean) {
  try {
    window.localStorage.setItem(STORAGE_KEY, value ? '1' : '0');
  } catch {
    /* ignore quota / privacy-mode errors */
  }
}

export const sidebar = {
  get collapsed() {
    return collapsed;
  },
  toggle() {
    collapsed = !collapsed;
    persist(collapsed);
  },
  set(value: boolean) {
    collapsed = value;
    persist(value);
  },
};
