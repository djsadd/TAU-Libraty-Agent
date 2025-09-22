// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      // всё, что начинается с /api, уходит на FastAPI
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // если ваш бэкенд слушает /chat без /api, раскомментируйте rewrite:
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['src/setupTests.ts'],
  },
  // hmr: { overlay: false }, // опционально: скрыть красный оверлей
});
