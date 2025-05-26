import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Configuração padrão
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    hmr: {
      host: 'rfp.gustavotadeu.com.br',
    },
    proxy: {
      '/api': {
        target: 'https://rfpbackend.gustavotadeu.com.br',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      }
    },
    preview: {
      host: true,
      port: 4173,
      strictPort: true,
      // 🚨 Esta linha é essencial para permitir o host personalizado
      allowedHosts: ['rfp.gustavotadeu.com.br']
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
}));
