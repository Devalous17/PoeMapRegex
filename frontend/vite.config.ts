import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  build: mode === 'vercel'
    ? { outDir: 'dist', emptyOutDir: true }
    : { outDir: '../static', emptyOutDir: false },
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
}));
