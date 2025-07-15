import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { visualizer } from "rollup-plugin-visualizer";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [
    react(),
    mode === 'development' && componentTagger(),
    mode === 'analyze' && visualizer({
      filename: 'dist/stats.html',
      open: true,
      brotliSize: true,
      gzipSize: true,
    }),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Dynamic chunk splitting based on file paths and dependencies
          
          // Core React ecosystem - keep together but separate from app
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor-react';
          }
          
          // Animation libraries - split into separate chunks for lazy loading
          if (id.includes('node_modules/three')) {
            return 'animation-three';
          }
          
          if (id.includes('node_modules/vanta')) {
            return 'animation-vanta';
          }
          
          if (id.includes('node_modules/p5')) {
            return 'animation-p5';
          }
          
          // Maps - heavy library, load only when needed
          if (id.includes('node_modules/mapbox-gl')) {
            return 'vendor-maps';
          }
          
          // Charts - load only when needed
          if (id.includes('node_modules/recharts')) {
            return 'vendor-charts';
          }
          
          // UI components - group related Radix components
          if (id.includes('node_modules/@radix-ui')) {
            return 'vendor-ui-radix';
          }
          
          // Form handling
          if (id.includes('node_modules/react-hook-form') || 
              id.includes('node_modules/@hookform') ||
              id.includes('node_modules/zod')) {
            return 'vendor-forms';
          }
          
          // Routing
          if (id.includes('node_modules/react-router')) {
            return 'vendor-routing';
          }
          
          // Query management
          if (id.includes('node_modules/@tanstack/react-query')) {
            return 'vendor-query';
          }
          
          // Mobile optimization modules - lazy loaded
          if (id.includes('src/utils/mobileDetection') ||
              id.includes('src/utils/mobilePerformanceMonitor') ||
              id.includes('src/utils/connectionAwareOptimizer') ||
              id.includes('src/utils/mobileTouchOptimizer')) {
            return 'mobile-optimizations';
          }
          
          // Utility libraries
          if (id.includes('node_modules/date-fns') ||
              id.includes('node_modules/clsx') ||
              id.includes('node_modules/class-variance-authority')) {
            return 'vendor-utils';
          }
          
          // Icons
          if (id.includes('node_modules/lucide-react') ||
              id.includes('node_modules/react-icons')) {
            return 'vendor-icons';
          }
          
          // Other vendor libraries
          if (id.includes('node_modules/')) {
            return 'vendor-misc';
          }
        },
      },
    },
    // Bundle size warnings and optimization
    chunkSizeWarningLimit: 500, // 500KB limit
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'], // Remove specific console methods
      },
    },
    // Asset optimization
    assetsInlineLimit: 4096, // Inline assets smaller than 4KB
  },
}));
