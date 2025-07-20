import react from '@vitejs/plugin-react';
import * as path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    // Google OAuth Client ID - replace with actual value
    'import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID': JSON.stringify(
      process.env.VITE_GOOGLE_OAUTH_CLIENT_ID || 'your_google_client_id_here'
    ),
    // Suppress MUI Grid deprecation warnings in development
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    sourcemap: false, // Disable source maps for production to reduce warnings
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          oauth: ['@react-oauth/google'],
          mui: ['@mui/material', '@mui/icons-material'],
        },
      },
    },
  },
  optimizeDeps: {
    include: ['@mui/material', '@mui/icons-material', '@react-oauth/google'],
    force: true, // Force re-optimization to ensure dependencies are properly cached
  },
  css: {
    devSourcemap: false, // Disable CSS source maps in development to reduce warnings
  },
  // Disable source maps in development to prevent source map parsing errors
  esbuild: {
    sourcemap: false,
  },
});
