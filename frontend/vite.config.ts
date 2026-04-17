import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': apiProxyTarget
    }
  }
});
