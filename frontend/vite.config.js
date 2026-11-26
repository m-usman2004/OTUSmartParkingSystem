import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      // primary central server
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      // backup central server (/backup-api/... is sent to 5100 as /api/...)
      '/backup-api': {
        target: 'http://127.0.0.1:5100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/backup-api/, '/api'),
      },
    },
  },
})
