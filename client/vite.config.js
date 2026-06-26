import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy /api al backend Flask durante desarrollo.
// En produccion (Docker), Nginx hace el proxy hacia el contenedor backend.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
