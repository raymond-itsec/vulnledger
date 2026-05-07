import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Local ambient declaration for the only Node API this config touches.
// Avoids pulling @types/node into devDependencies just for one read of
// an env var. Vite runs this file at build time on Node, so `process`
// is always present at runtime; this just gives it a narrow type.
declare const process: { env: Record<string, string | undefined> };

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': apiProxyTarget
    }
  }
});
