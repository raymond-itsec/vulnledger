// Context key used to signal "an /app layout shell is already wrapping me".
//
// The root +layout.svelte calls setContext(APP_SHELL_CONTEXT_KEY, true) in
// its authenticated branch. Any descendant component that would otherwise
// render its OWN page chrome (header/footer/page-background) — most
// notably PublicShell — uses getContext(APP_SHELL_CONTEXT_KEY) to detect
// the wrapping shell and downgrade to a bare children-only render so we
// don't end up with duplicated chrome (two topbars, two footers, etc.)
// when a public-info page like /trust is opened by an authenticated user.

export const APP_SHELL_CONTEXT_KEY = Symbol('vl.app-shell-active');
