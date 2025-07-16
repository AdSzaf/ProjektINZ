import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // pozwala na dostęp spoza kontenera
    port: 5173,       // domyślny port Vite
    strictPort: true,
    watch: {
      usePolling: true
    },
    proxy: {
      // proxy API requests to Django backend
      '/api': {
        target: 'http://backend:8000', // nazwa kontenera backendu z docker-compose
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '/api'),
      }
    }
  },
  // Opcjonalnie ustaw base path jeśli frontend będzie serwowany z podścieżki
  // base: '/static/', 
})
