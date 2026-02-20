import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Build output goes to Spring Boot static resources
  build: {
    outDir: '../java/src/main/resources/static',
    emptyOutDir: true,
  },
  
  // Proxy API calls to Spring Boot during development
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
