# Bundle Size Optimization Guide

This guide provides comprehensive strategies for maintaining optimal bundle sizes while implementing the mobile optimization features and animated backgrounds.

## 🎯 Bundle Size Targets

### Recommended Limits
- **Main Bundle**: ≤ 500KB (critical path)
- **Total Bundle**: ≤ 2.5MB (all chunks combined)
- **Critical Path**: ≤ 800KB (essential chunks for initial load)
- **Mobile Optimizations**: ≤ 50KB (lazy-loaded features)

### Critical Path Chunks
- `vendor-react` (React ecosystem)
- `vendor-routing` (React Router)
- `main` (application code)

## 📊 Monitoring and Analysis

### Daily Monitoring
```bash
# Record current bundle sizes
npm run bundle:monitor:record

# Analyze size changes and trends
npm run bundle:monitor:analyze

# Generate comprehensive report
npm run bundle:monitor --report --trends
```

### Bundle Analysis
```bash
# Check bundle size limits
npm run bundle:enforce

# Generate visual analysis
npm run build:analyze

# Check specific size limits
npm run size:limit
```

### Dashboard Access
```bash
# Generate and view bundle dashboard
npm run bundle:dashboard
open dist/bundle-dashboard.html
```

## 🚀 Optimization Strategies

### 1. Lazy Loading Implementation

#### Animation Libraries
```typescript
// ✅ Good: Lazy load heavy animation libraries
const AnimationLibraryLoader = lazy(() => import('./utils/animationLibraryLoader'));

// ❌ Bad: Import all libraries upfront
import * as THREE from 'three';
import VANTA from 'vanta';
```

#### Mobile Optimization Features
```typescript
// ✅ Good: Conditional loading based on device capabilities
const mobileOptimizations = await loadMobileOptimizations();

// ❌ Bad: Load all mobile features regardless of device
import './utils/mobileDetection';
import './utils/mobilePerformanceMonitor';
```

### 2. Code Splitting Configuration

#### Vite Configuration
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Animation libraries - separate chunks for lazy loading
          if (id.includes('node_modules/three')) return 'animation-three';
          if (id.includes('node_modules/vanta')) return 'animation-vanta';
          
          // Mobile optimizations - small, conditional chunk
          if (id.includes('src/utils/mobile')) return 'mobile-optimizations';
          
          // Heavy libraries - lazy load when needed
          if (id.includes('node_modules/mapbox-gl')) return 'vendor-maps';
        }
      }
    }
  }
});
```

### 3. Tree Shaking and Dead Code Elimination

#### Import Optimization
```typescript
// ✅ Good: Import only what you need
import { format } from 'date-fns';
import { Button } from '@radix-ui/react-button';

// ❌ Bad: Import entire libraries
import * as dateFns from 'date-fns';
import * as RadixUI from '@radix-ui/react';
```

#### Unused Code Detection
```bash
# Use bundle analyzer to identify unused code
npm run build:analyze

# Check for unused dependencies
npx depcheck
```

### 4. Dynamic Imports and Conditional Loading

#### Feature-Based Loading
```typescript
// Load features only when needed
const loadMapComponents = async () => {
  if (shouldShowMap) {
    const { MapComponent } = await import('./components/Map');
    return MapComponent;
  }
  return null;
};
```

#### Device-Aware Loading
```typescript
// Load based on device capabilities
const loadAnimationFeatures = async () => {
  const capabilities = await getMobileCapabilities();
  
  if (capabilities.supportsWebGL2 && capabilities.gpuMemoryMB > 1024) {
    return import('./utils/advancedAnimations');
  } else {
    return import('./utils/basicAnimations');
  }
};
```

### 5. Bundle Optimization Modes

#### Minimal Mode (< 300KB)
```typescript
const OptimizedBackground = ({ bundleOptimization = 'minimal' }) => {
  if (bundleOptimization === 'minimal') {
    return <StaticBackground />; // CSS-only background
  }
  // ... full implementation
};
```

#### Balanced Mode (< 500KB)
```typescript
if (bundleOptimization === 'balanced') {
  // Load basic animations with mobile optimizations
  const basicAnimations = await import('./utils/basicAnimations');
  const mobileSettings = getBasicMobileSettings();
}
```

#### Full Mode (< 800KB)
```typescript
if (bundleOptimization === 'full') {
  // Load all features with full optimization
  const allModules = await loadMobileOptimizations();
  const animationLibs = await loadAnimationLibraries();
}
```

## 🔧 Optimization Techniques

### 1. Image and Asset Optimization

```typescript
// Vite asset optimization
export default defineConfig({
  build: {
    assetsInlineLimit: 4096, // Inline assets < 4KB
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  }
});
```

### 2. CSS Optimization

```typescript
// Use Tailwind JIT for minimal CSS
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Only include used utilities
    }
  }
};
```

### 3. JavaScript Minification

```typescript
// Terser optimization
export default defineConfig({
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log']
      }
    }
  }
});
```

### 4. Dependencies Audit

```bash
# Regular dependency analysis
npm run bundle:monitor

# Check for duplicate dependencies
npm ls --depth=0

# Analyze package sizes
npx bundlephobia <package-name>
```

## 📈 Performance Monitoring

### 1. Automated Monitoring

```bash
# Set up automated bundle size tracking
npm run bundle:monitor:record  # After each build
npm run bundle:monitor:analyze # Check for regressions
```

### 2. CI/CD Integration

```yaml
# GitHub Actions integration
- name: Check bundle sizes
  run: npm run bundle:enforce:strict --ci
  
- name: Monitor bundle trends
  run: npm run bundle:monitor:trends
```

### 3. Performance Budgets

```javascript
// Set performance budgets
const PERFORMANCE_BUDGETS = {
  maxJSSize: 500 * 1024,     // 500KB
  maxCSSSize: 100 * 1024,    // 100KB
  maxImageSize: 200 * 1024,  // 200KB
  maxTotalSize: 2.5 * 1024 * 1024 // 2.5MB
};
```

## 🚨 Common Pitfalls and Solutions

### 1. Animation Library Size Issues

**Problem**: Three.js and Vanta.js are too large for mobile
**Solution**: 
```typescript
// Implement conditional loading
const animationLoader = AnimationLibraryLoader.getInstance();
if (animationLoader.shouldLoadAnimationLibraries()) {
  await animationLoader.loadThreeJS();
}
```

### 2. Mobile Optimization Overhead

**Problem**: Mobile optimizations add unnecessary weight
**Solution**:
```typescript
// Use lightweight basic settings by default
const basicSettings = getBasicMobileSettings();
// Load advanced features only when beneficial
if (deviceCapabilities.supportsAdvancedFeatures) {
  const advanced = await loadAdvancedOptimizations();
}
```

### 3. Dependency Bloat

**Problem**: Heavy dependencies for simple features
**Solution**:
```typescript
// Replace heavy libraries with lightweight alternatives
// Instead of: import moment from 'moment'
import { format } from 'date-fns';

// Instead of: import _ from 'lodash'
import { debounce } from 'lodash-es';
```

### 4. Unused Code Accumulation

**Problem**: Dead code increasing bundle size
**Solution**:
```bash
# Regular cleanup
npm run build:analyze  # Identify unused code
npx depcheck          # Find unused dependencies
eslint --fix          # Remove unused imports
```

## 📋 Maintenance Checklist

### Weekly Tasks
- [ ] Run bundle size analysis: `npm run bundle:monitor:trends`
- [ ] Check for bundle size regressions
- [ ] Review bundle dashboard for insights
- [ ] Update optimization recommendations

### Monthly Tasks
- [ ] Audit dependencies for updates/alternatives
- [ ] Review and optimize code splitting strategy
- [ ] Analyze loading patterns and user behavior
- [ ] Update bundle size targets if needed

### Release Tasks
- [ ] Run strict bundle enforcement: `npm run bundle:enforce:strict`
- [ ] Generate bundle analysis report
- [ ] Document any significant size changes
- [ ] Update performance budgets if necessary

## 🔗 Useful Resources

### Bundle Analysis Tools
- Vite Bundle Analyzer: Visual chunk analysis
- Rollup Plugin Visualizer: Interactive bundle map
- Bundle Monitor Dashboard: Historical trends and alerts

### Commands Reference
```bash
# Bundle size management
npm run bundle:enforce           # Check limits
npm run bundle:enforce:strict    # Strict enforcement
npm run bundle:monitor          # Full monitoring
npm run bundle:monitor:record   # Record current sizes
npm run bundle:monitor:analyze  # Analyze changes
npm run bundle:monitor:trends   # Generate trends
npm run bundle:dashboard        # Generate dashboard

# Analysis and optimization
npm run build:analyze           # Visual bundle analysis
npm run size                    # Basic size check
npm run size:limit             # Check against limits
```

### Best Practices Summary
1. **Implement lazy loading** for heavy features
2. **Use conditional imports** based on device capabilities
3. **Monitor bundle sizes** continuously
4. **Set and enforce** performance budgets
5. **Regular maintenance** and optimization
6. **Automate checks** in CI/CD pipeline

This guide ensures your bundle sizes remain optimal while providing rich mobile optimization features and animated backgrounds.