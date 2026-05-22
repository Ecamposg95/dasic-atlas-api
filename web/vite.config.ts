import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: '../app/static/dist',
    emptyOutDir: true,
    manifest: true,
    // Subir el límite — el chunk principal ya es mucho más chico tras code-split,
    // pero algunos vendor chunks (react-dom) rondan 130kB minified y disparan
    // el warning default de 500kB cuando estaba unificado. Tras chunking no
    // debería verse el warning, pero conservamos margen.
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        // Vendor chunking: separamos las libs que cambian poco (react, query,
        // router, radix) de nuestro código. Eso permite cachear el vendor entre
        // deploys y solo invalidar el chunk de aplicación cuando editamos features.
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-query': ['@tanstack/react-query', '@tanstack/react-query-devtools'],
          'vendor-ui': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-slot',
            '@radix-ui/react-toast',
            'class-variance-authority',
            'clsx',
            'tailwind-merge',
            'lucide-react',
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
        secure: false,
      },
    },
  },
});
