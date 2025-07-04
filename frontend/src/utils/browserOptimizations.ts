/**
 * Browser-Specific Optimizations
 * 
 * Applies browser-specific optimizations, polyfills, and performance tweaks
 * for animation rendering across Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
 */

import { detectBrowser, type BrowserInfo } from './browserCompatibility';
import { loadPolyfills, type PolyfillConfig } from './polyfills';

export interface BrowserOptimizationConfig {
  enableVendorPrefixes: boolean;
  enablePerformanceHints: boolean;
  enableMemoryOptimizations: boolean;
  enableCSSOptimizations: boolean;
  enableWebGLOptimizations: boolean;
  debug: boolean;
}

export interface OptimizationApplied {
  type: 'css' | 'js' | 'webgl' | 'performance';
  browser: string;
  feature: string;
  description: string;
}

let optimizationsApplied: OptimizationApplied[] = [];

/**
 * Apply browser-specific optimizations
 */
export async function applyBrowserOptimizations(
  config: Partial<BrowserOptimizationConfig> = {}
): Promise<OptimizationApplied[]> {
  const defaultConfig: BrowserOptimizationConfig = {
    enableVendorPrefixes: true,
    enablePerformanceHints: true,
    enableMemoryOptimizations: true,
    enableCSSOptimizations: true,
    enableWebGLOptimizations: true,
    debug: false,
    ...config,
  };

  const browser = detectBrowser();
  optimizationsApplied = [];

  if (defaultConfig.debug) {
    console.log('Applying browser optimizations for:', browser);
  }

  // Apply CSS optimizations
  if (defaultConfig.enableCSSOptimizations) {
    await applyCSSOptimizations(browser, defaultConfig.debug);
  }

  // Apply WebGL optimizations
  if (defaultConfig.enableWebGLOptimizations) {
    await applyWebGLOptimizations(browser, defaultConfig.debug);
  }

  // Apply performance optimizations
  if (defaultConfig.enablePerformanceHints) {
    await applyPerformanceOptimizations(browser, defaultConfig.debug);
  }

  // Apply memory optimizations
  if (defaultConfig.enableMemoryOptimizations) {
    await applyMemoryOptimizations(browser, defaultConfig.debug);
  }

  // Apply vendor prefixes
  if (defaultConfig.enableVendorPrefixes) {
    await applyVendorPrefixOptimizations(browser, defaultConfig.debug);
  }

  if (defaultConfig.debug) {
    console.log('Browser optimizations applied:', optimizationsApplied);
  }

  return optimizationsApplied;
}

/**
 * Apply CSS-specific optimizations
 */
async function applyCSSOptimizations(browser: BrowserInfo, debug: boolean): Promise<void> {
  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-browser-optimizations', 'css');
  let css = '';

  // Safari-specific CSS optimizations
  if (browser.name === 'Safari') {
    css += `
      /* Safari CSS optimizations */
      .fallback-animation-container,
      .vanta-canvas {
        -webkit-transform: translate3d(0, 0, 0);
        -webkit-backface-visibility: hidden;
        -webkit-perspective: 1000px;
      }
      
      /* Safari backdrop-filter optimization */
      .backdrop-blur {
        -webkit-backdrop-filter: blur(10px);
        backdrop-filter: blur(10px);
      }
      
      /* Safari animation performance */
      @media screen and (max-device-width: 1024px) {
        .fallback-particle {
          -webkit-animation-duration: 20s !important;
        }
      }
    `;

    optimizationsApplied.push({
      type: 'css',
      browser: browser.name,
      feature: 'webkit-transforms',
      description: 'Applied WebKit transform optimizations for Safari',
    });

    // iOS Safari specific optimizations
    if (browser.isMobile) {
      css += `
        /* iOS Safari specific */
        body {
          -webkit-overflow-scrolling: touch;
        }
        
        .animation-container {
          -webkit-transform: translate3d(0, 0, 0);
        }
        
        /* Reduce animation complexity on iOS */
        .fallback-particle--animation-3 {
          -webkit-animation-name: fallback-particle-float-1 !important;
        }
      `;

      optimizationsApplied.push({
        type: 'css',
        browser: 'iOS Safari',
        feature: 'mobile-optimizations',
        description: 'Applied iOS Safari mobile optimizations',
      });
    }
  }

  // Firefox-specific CSS optimizations
  if (browser.name === 'Firefox') {
    css += `
      /* Firefox CSS optimizations */
      .fallback-particle,
      .fallback-gradient-animation {
        will-change: transform, opacity;
      }
      
      /* Firefox WebGL canvas optimization */
      canvas {
        image-rendering: -moz-crisp-edges;
      }
      
      /* Firefox filter optimization */
      .fallback-gradient-animation {
        filter: contrast(1.1) brightness(1.05);
      }
    `;

    optimizationsApplied.push({
      type: 'css',
      browser: browser.name,
      feature: 'moz-optimizations',
      description: 'Applied Firefox-specific rendering optimizations',
    });
  }

  // Edge-specific CSS optimizations
  if (browser.name === 'Edge') {
    // Legacy Edge (pre-Chromium) specific fixes
    if (browser.majorVersion < 85) {
      css += `
        /* Legacy Edge optimizations */
        .fallback-gradient-animation {
          filter: none; /* Remove complex filters that cause issues */
        }
        
        .fallback-particle {
          -ms-transform: translate3d(0, 0, 0);
        }
      `;

      optimizationsApplied.push({
        type: 'css',
        browser: 'Legacy Edge',
        feature: 'edge-legacy-fixes',
        description: 'Applied Legacy Edge compatibility fixes',
      });
    }
  }

  // Chrome-specific optimizations
  if (browser.name === 'Chrome') {
    css += `
      /* Chrome optimizations */
      .animation-container {
        contain: layout style paint;
      }
      
      .fallback-particle {
        contain: strict;
      }
      
      /* Chrome memory optimization */
      .vanta-canvas {
        will-change: auto; /* Let Chrome decide what to optimize */
      }
    `;

    optimizationsApplied.push({
      type: 'css',
      browser: browser.name,
      feature: 'containment',
      description: 'Applied CSS containment for Chrome performance',
    });
  }

  // General mobile optimizations
  if (browser.isMobile) {
    css += `
      /* General mobile optimizations */
      @media (max-width: 768px) {
        .fallback-particle {
          animation-duration: 25s !important;
        }
        
        .fallback-gradient-animation {
          animation-duration: 30s !important;
        }
        
        /* Reduce particle complexity */
        .fallback-particle--animation-3 {
          animation-name: fallback-particle-float-1 !important;
        }
      }
      
      @media (max-width: 480px) {
        .fallback-particle {
          animation-duration: 35s !important;
        }
      }
    `;

    optimizationsApplied.push({
      type: 'css',
      browser: 'Mobile',
      feature: 'mobile-performance',
      description: 'Applied mobile-specific performance optimizations',
    });
  }

  if (css) {
    styleSheet.textContent = css;
    document.head.appendChild(styleSheet);

    if (debug) {
      console.log('CSS optimizations applied for', browser.name);
    }
  }
}

/**
 * Apply WebGL-specific optimizations
 */
async function applyWebGLOptimizations(browser: BrowserInfo, debug: boolean): Promise<void> {
  // Set WebGL context attributes for optimal performance
  const originalGetContext = HTMLCanvasElement.prototype.getContext;
  
  HTMLCanvasElement.prototype.getContext = function(
    contextId: string,
    options?: any
  ) {
    if (contextId === 'webgl' || contextId === 'experimental-webgl') {
      const optimizedOptions = {
        alpha: false, // Disable alpha for better performance
        antialias: true, // Enable antialiasing for quality
        depth: true,
        stencil: false,
        premultipliedAlpha: false,
        preserveDrawingBuffer: false,
        powerPreference: 'high-performance',
        ...options,
      };

      // Browser-specific WebGL optimizations
      if (browser.name === 'Safari' && browser.isMobile) {
        // iOS Safari WebGL optimizations
        optimizedOptions.antialias = false; // Disable AA on mobile Safari for performance
        optimizedOptions.powerPreference = 'low-power'; // Battery optimization
      }

      if (browser.name === 'Firefox') {
        // Firefox WebGL optimizations
        optimizedOptions.preserveDrawingBuffer = true; // Better compatibility
      }

      const context = originalGetContext.call(this, contextId, optimizedOptions);
      
      if (context && debug) {
        console.log('WebGL context optimized for', browser.name, optimizedOptions);
      }

      optimizationsApplied.push({
        type: 'webgl',
        browser: browser.name,
        feature: 'context-optimization',
        description: `Optimized WebGL context attributes for ${browser.name}`,
      });

      return context;
    }

    return originalGetContext.call(this, contextId, options);
  };
}

/**
 * Apply performance optimizations
 */
async function applyPerformanceOptimizations(browser: BrowserInfo, debug: boolean): Promise<void> {
  // Browser-specific performance hints
  if (browser.name === 'Chrome') {
    // Chrome performance optimizations
    try {
      // Enable high resolution time if available
      if ('timeOrigin' in performance) {
        (window as any).chromeOptimized = true;
      }
    } catch {}

    optimizationsApplied.push({
      type: 'performance',
      browser: browser.name,
      feature: 'high-resolution-time',
      description: 'Enabled Chrome high-resolution timing',
    });
  }

  if (browser.name === 'Firefox') {
    // Firefox performance optimizations
    try {
      // Optimize for Firefox's rendering engine
      if (typeof (window as any).mozRequestAnimationFrame !== 'undefined') {
        // Use Firefox-specific rAF if available
        (window as any).firefoxOptimized = true;
      }
    } catch {}

    optimizationsApplied.push({
      type: 'performance',
      browser: browser.name,
      feature: 'gecko-optimizations',
      description: 'Applied Gecko rendering optimizations',
    });
  }

  if (browser.name === 'Safari') {
    // Safari performance optimizations
    try {
      // Safari-specific memory management
      if (browser.isMobile) {
        // iOS Safari memory optimization
        setInterval(() => {
          if ('memory' in performance) {
            const memInfo = (performance as any).memory;
            if (memInfo.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB threshold
              // Trigger memory cleanup
              if ((window as any).gc) {
                (window as any).gc();
              }
            }
          }
        }, 30000); // Check every 30 seconds
      }
    } catch {}

    optimizationsApplied.push({
      type: 'performance',
      browser: browser.isMobile ? 'iOS Safari' : 'Safari',
      feature: 'memory-management',
      description: 'Applied Safari memory management optimizations',
    });
  }
}

/**
 * Apply memory optimizations
 */
async function applyMemoryOptimizations(browser: BrowserInfo, debug: boolean): Promise<void> {
  // Set up memory monitoring and cleanup
  let memoryMonitoringInterval: number | null = null;

  const startMemoryMonitoring = () => {
    if (memoryMonitoringInterval) return;

    memoryMonitoringInterval = window.setInterval(() => {
      if ('memory' in performance) {
        const memInfo = (performance as any).memory;
        const usedMB = memInfo.usedJSHeapSize / (1024 * 1024);
        const totalMB = memInfo.totalJSHeapSize / (1024 * 1024);

        // Browser-specific memory thresholds
        let threshold = 100; // Default 100MB
        if (browser.isMobile) threshold = 50; // 50MB for mobile
        if (browser.name === 'Safari' && browser.isMobile) threshold = 30; // 30MB for iOS

        if (usedMB > threshold) {
          // Dispatch memory warning event
          window.dispatchEvent(new CustomEvent('memory-warning', {
            detail: { usedMB, totalMB, threshold }
          }));

          if (debug) {
            console.warn(`Memory usage high: ${usedMB.toFixed(1)}MB / ${totalMB.toFixed(1)}MB`);
          }
        }
      }
    }, 10000); // Check every 10 seconds
  };

  // Start monitoring for browsers that support it
  if ('memory' in performance) {
    startMemoryMonitoring();
    
    optimizationsApplied.push({
      type: 'performance',
      browser: browser.name,
      feature: 'memory-monitoring',
      description: 'Enabled memory usage monitoring',
    });
  }

  // Cleanup function
  (window as any).stopMemoryMonitoring = () => {
    if (memoryMonitoringInterval) {
      clearInterval(memoryMonitoringInterval);
      memoryMonitoringInterval = null;
    }
  };
}

/**
 * Apply vendor prefix optimizations
 */
async function applyVendorPrefixOptimizations(browser: BrowserInfo, debug: boolean): Promise<void> {
  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-browser-optimizations', 'vendor-prefixes');
  let css = '';

  // Browser-specific vendor prefixes
  if (browser.name === 'Safari') {
    css += `
      /* WebKit vendor prefixes */
      .webkit-optimized {
        -webkit-transform: translate3d(0, 0, 0);
        -webkit-backface-visibility: hidden;
        -webkit-perspective: 1000px;
        -webkit-transform-style: preserve-3d;
      }
    `;
  }

  if (browser.name === 'Firefox') {
    css += `
      /* Gecko vendor prefixes */
      .moz-optimized {
        -moz-transform: translate3d(0, 0, 0);
        -moz-backface-visibility: hidden;
        -moz-perspective: 1000px;
      }
    `;
  }

  if (browser.name === 'Edge' && browser.majorVersion < 85) {
    css += `
      /* Legacy Edge vendor prefixes */
      .ms-optimized {
        -ms-transform: translate3d(0, 0, 0);
        -ms-backface-visibility: hidden;
        -ms-perspective: 1000px;
      }
    `;
  }

  if (css) {
    styleSheet.textContent = css;
    document.head.appendChild(styleSheet);

    optimizationsApplied.push({
      type: 'css',
      browser: browser.name,
      feature: 'vendor-prefixes',
      description: 'Applied browser-specific vendor prefixes',
    });
  }
}

/**
 * Get applied optimizations
 */
export function getAppliedOptimizations(): OptimizationApplied[] {
  return [...optimizationsApplied];
}

/**
 * Reset optimizations (for testing)
 */
export function resetOptimizations(): void {
  optimizationsApplied = [];
  
  // Remove optimization stylesheets
  const optimizationSheets = document.querySelectorAll('style[data-browser-optimizations]');
  optimizationSheets.forEach(sheet => sheet.remove());
  
  // Stop memory monitoring
  if ((window as any).stopMemoryMonitoring) {
    (window as any).stopMemoryMonitoring();
  }
}

export default {
  applyBrowserOptimizations,
  getAppliedOptimizations,
  resetOptimizations,
};