import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      fallback: 'index.html'
    }),
    csp: {
      mode: 'hash',
      directives: {
        'default-src': ["'self'"],
        'script-src': ["'self'"],
        // Svelte components and the Kit bootstrap div rely on inline
        // style= attributes. CSP Level 3 requires 'unsafe-hashes' to allow
        // inline style attributes via hashes, which doesn't compose with
        // Kit's hash-mode auto-generation. Inline styles cannot execute
        // code, so 'unsafe-inline' on style-src only is an accepted trade.
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:', 'blob:'],
        'font-src': ["'self'"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
        'object-src': ["'none'"]
      }
    }
  }
};
