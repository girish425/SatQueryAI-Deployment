import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/chat': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/retrieve': 'http://127.0.0.1:8000',
      '/history': 'http://127.0.0.1:8000',
      '/conversation': 'http://127.0.0.1:8000',
      '/analysis': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
      '/evidence': 'http://127.0.0.1:8000',
      '/sample_data': 'http://127.0.0.1:8000'
    }
  }
})

