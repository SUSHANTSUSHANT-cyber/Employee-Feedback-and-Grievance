import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// When the UI is run with `npm run dev`, requests to /api/rest must be proxied
// to FastAPI rather than handled by Vite's static-file server. Override the
// target for a non-local API with VITE_API_PROXY_TARGET.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: { outDir: '../api/static', emptyOutDir: true },
})
