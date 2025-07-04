/**
 * Browser Polyfills and Fallbacks
 * 
 * Provides polyfills and fallback implementations for missing browser features
 * across Chrome 80+, Firefox 75+, Safari 13+, Edge 80+ with graceful degradation
 */

import { detectBrowser, type BrowserInfo, type FeatureSupport } from './browserCompatibility';

export interface PolyfillConfig {
  enableRequestAnimationFrame: boolean;
  enableIntersectionObserver: boolean;
  enableResizeObserver: boolean;
  enableWebGL: boolean;
  enablePerformanceMemory: boolean;
  enableCSSSupports: boolean;
  enableMatchMedia: boolean;
  enableCustomProperties: boolean;
  debug: boolean;
}

export interface PolyfillStatus {
  requestAnimationFrame: 'native' | 'polyfilled' | 'fallback' | 'unavailable';
  intersectionObserver: 'native' | 'polyfilled' | 'fallback' | 'unavailable';
  resizeObserver: 'native' | 'polyfilled' | 'fallback' | 'unavailable';
  webgl: 'native' | 'fallback' | 'unavailable';
  performanceMemory: 'native' | 'polyfilled' | 'unavailable';
  cssSupports: 'native' | 'polyfilled' | 'unavailable';
  matchMedia: 'native' | 'polyfilled' | 'unavailable';
  customProperties: 'native' | 'fallback' | 'unavailable';
}

let polyfillsLoaded = false;
let polyfillStatus: PolyfillStatus | null = null;

/**
 * Load all necessary polyfills based on browser capabilities
 */
export async function loadPolyfills(config: Partial<PolyfillConfig> = {}): Promise<PolyfillStatus> {
  if (polyfillsLoaded && polyfillStatus) {
    return polyfillStatus;
  }

  const defaultConfig: PolyfillConfig = {
    enableRequestAnimationFrame: true,
    enableIntersectionObserver: true,
    enableResizeObserver: true,
    enableWebGL: true,
    enablePerformanceMemory: true,
    enableCSSSupports: true,
    enableMatchMedia: true,
    enableCustomProperties: true,
    debug: false,
    ...config,
  };

  const browser = detectBrowser();
  const status: PolyfillStatus = {
    requestAnimationFrame: 'unavailable',
    intersectionObserver: 'unavailable',
    resizeObserver: 'unavailable',
    webgl: 'unavailable',
    performanceMemory: 'unavailable',
    cssSupports: 'unavailable',
    matchMedia: 'unavailable',
    customProperties: 'unavailable',
  };

  if (defaultConfig.debug) {
    console.log('Loading polyfills for:', browser);
  }

  // Load polyfills in parallel for better performance
  const polyfillPromises = [
    defaultConfig.enableRequestAnimationFrame ? loadRequestAnimationFramePolyfill(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enableIntersectionObserver ? loadIntersectionObserverPolyfill(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enableResizeObserver ? loadResizeObserverPolyfill(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enableWebGL ? loadWebGLFallback(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enablePerformanceMemory ? loadPerformanceMemoryPolyfill(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enableCSSSupports ? loadCSSSupportsPolyfill(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enableMatchMedia ? loadMatchMediaPolyfill(status, defaultConfig.debug) : Promise.resolve(),
    defaultConfig.enableCustomProperties ? loadCustomPropertiesFallback(status, defaultConfig.debug) : Promise.resolve(),
  ];

  await Promise.all(polyfillPromises);

  // Apply browser-specific fixes
  applyBrowserSpecificFixes(browser, defaultConfig.debug);

  polyfillsLoaded = true;
  polyfillStatus = status;

  if (defaultConfig.debug) {
    console.log('Polyfill status:', status);
  }

  return status;
}

/**
 * RequestAnimationFrame polyfill
 */
async function loadRequestAnimationFramePolyfill(status: PolyfillStatus, debug: boolean): Promise<void> {
  if (typeof requestAnimationFrame !== 'undefined') {
    status.requestAnimationFrame = 'native';
    return;
  }

  if (debug) {
    console.log('Loading requestAnimationFrame polyfill');
  }

  let lastTime = 0;
  
  (window as any).requestAnimationFrame = function(callback: FrameRequestCallback): number {
    const currTime = new Date().getTime();
    const timeToCall = Math.max(0, 16 - (currTime - lastTime));
    const id = window.setTimeout(() => {
      callback(currTime + timeToCall);
    }, timeToCall);
    lastTime = currTime + timeToCall;
    return id;
  };

  (window as any).cancelAnimationFrame = function(id: number): void {
    clearTimeout(id);
  };

  status.requestAnimationFrame = 'polyfilled';
}

/**
 * IntersectionObserver polyfill
 */
async function loadIntersectionObserverPolyfill(status: PolyfillStatus, debug: boolean): Promise<void> {
  if (typeof IntersectionObserver !== 'undefined') {
    status.intersectionObserver = 'native';
    return;
  }

  if (debug) {
    console.log('Loading IntersectionObserver polyfill');
  }

  // Simple fallback implementation
  class IntersectionObserverPolyfill {
    private callback: IntersectionObserverCallback;
    private targets: Element[] = [];
    private checkInterval: number | null = null;

    constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
      this.callback = callback;
    }

    observe(target: Element): void {
      if (!this.targets.includes(target)) {
        this.targets.push(target);
        this.startChecking();
      }
    }

    unobserve(target: Element): void {
      const index = this.targets.indexOf(target);
      if (index > -1) {
        this.targets.splice(index, 1);
        if (this.targets.length === 0) {
          this.stopChecking();
        }
      }
    }

    disconnect(): void {
      this.targets = [];
      this.stopChecking();
    }

    private startChecking(): void {
      if (this.checkInterval) return;
      
      this.checkInterval = window.setInterval(() => {
        const entries = this.targets.map(target => {
          const rect = target.getBoundingClientRect();
          const isIntersecting = rect.top >= 0 && rect.bottom <= window.innerHeight;
          
          return {
            target,
            isIntersecting,
            intersectionRatio: isIntersecting ? 1 : 0,
            boundingClientRect: rect,
            intersectionRect: isIntersecting ? rect : null,
            rootBounds: {
              top: 0,
              left: 0,
              bottom: window.innerHeight,
              right: window.innerWidth,
              width: window.innerWidth,
              height: window.innerHeight,
            },
            time: performance.now(),
          } as IntersectionObserverEntry;
        });

        if (entries.length > 0) {
          this.callback(entries, this as any);
        }
      }, 100);
    }

    private stopChecking(): void {
      if (this.checkInterval) {
        clearInterval(this.checkInterval);
        this.checkInterval = null;
      }
    }
  }

  (window as any).IntersectionObserver = IntersectionObserverPolyfill;
  status.intersectionObserver = 'polyfilled';
}

/**
 * ResizeObserver polyfill
 */
async function loadResizeObserverPolyfill(status: PolyfillStatus, debug: boolean): Promise<void> {
  if (typeof ResizeObserver !== 'undefined') {
    status.resizeObserver = 'native';
    return;
  }

  if (debug) {
    console.log('Loading ResizeObserver polyfill');
  }

  class ResizeObserverPolyfill {
    private callback: ResizeObserverCallback;
    private targets: Map<Element, { width: number; height: number }> = new Map();
    private checkInterval: number | null = null;

    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }

    observe(target: Element): void {
      const rect = target.getBoundingClientRect();
      this.targets.set(target, { width: rect.width, height: rect.height });
      this.startChecking();
    }

    unobserve(target: Element): void {
      this.targets.delete(target);
      if (this.targets.size === 0) {
        this.stopChecking();
      }
    }

    disconnect(): void {
      this.targets.clear();
      this.stopChecking();
    }

    private startChecking(): void {
      if (this.checkInterval) return;
      
      this.checkInterval = window.setInterval(() => {
        const entries: ResizeObserverEntry[] = [];
        
        this.targets.forEach((lastSize, target) => {
          const rect = target.getBoundingClientRect();
          const newSize = { width: rect.width, height: rect.height };
          
          if (newSize.width !== lastSize.width || newSize.height !== lastSize.height) {
            this.targets.set(target, newSize);
            
            entries.push({
              target,
              contentRect: rect,
              borderBoxSize: [{ inlineSize: rect.width, blockSize: rect.height }],
              contentBoxSize: [{ inlineSize: rect.width, blockSize: rect.height }],
              devicePixelContentBoxSize: [{ inlineSize: rect.width, blockSize: rect.height }],
            } as ResizeObserverEntry);
          }
        });

        if (entries.length > 0) {
          this.callback(entries, this as any);
        }
      }, 100);
    }

    private stopChecking(): void {
      if (this.checkInterval) {
        clearInterval(this.checkInterval);
        this.checkInterval = null;
      }
    }
  }

  (window as any).ResizeObserver = ResizeObserverPolyfill;
  status.resizeObserver = 'polyfilled';
}

/**
 * WebGL fallback detection
 */
async function loadWebGLFallback(status: PolyfillStatus, debug: boolean): Promise<void> {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (gl) {
      status.webgl = 'native';
      return;
    }
  } catch (error) {
    if (debug) {
      console.warn('WebGL not available:', error);
    }
  }

  // WebGL not available - CSS fallback will be used
  status.webgl = 'fallback';
  
  if (debug) {
    console.log('WebGL not available, using CSS fallback animations');
  }
}

/**
 * Performance.memory polyfill (Chrome-specific)
 */
async function loadPerformanceMemoryPolyfill(status: PolyfillStatus, debug: boolean): Promise<void> {
  if ('memory' in performance) {
    status.performanceMemory = 'native';
    return;
  }

  if (debug) {
    console.log('Loading performance.memory polyfill');
  }

  // Simple mock implementation for non-Chrome browsers
  (performance as any).memory = {
    get usedJSHeapSize() { return 0; },
    get totalJSHeapSize() { return 0; },
    get jsHeapSizeLimit() { return 0; },
  };

  status.performanceMemory = 'polyfilled';
}

/**
 * CSS.supports polyfill
 */
async function loadCSSSupportsPolyfill(status: PolyfillStatus, debug: boolean): Promise<void> {
  if (typeof CSS !== 'undefined' && CSS.supports) {
    status.cssSupports = 'native';
    return;
  }

  if (debug) {
    console.log('Loading CSS.supports polyfill');
  }

  // Basic polyfill for CSS.supports
  if (typeof CSS === 'undefined') {
    (window as any).CSS = {};
  }

  CSS.supports = function(property: string, value?: string): boolean {
    if (value === undefined) {
      // Single argument form: CSS.supports('display: flex')
      const [prop, val] = property.split(':').map(s => s.trim());
      return testCSSProperty(prop, val);
    }
    // Two argument form: CSS.supports('display', 'flex')
    return testCSSProperty(property, value);
  };

  function testCSSProperty(property: string, value: string): boolean {
    const element = document.createElement('div');
    const camelCase = property.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    
    try {
      (element.style as any)[camelCase] = value;
      return (element.style as any)[camelCase] === value;
    } catch {
      return false;
    }
  }

  status.cssSupports = 'polyfilled';
}

/**
 * MatchMedia polyfill
 */
async function loadMatchMediaPolyfill(status: PolyfillStatus, debug: boolean): Promise<void> {
  if (typeof window.matchMedia !== 'undefined') {
    status.matchMedia = 'native';
    return;
  }

  if (debug) {
    console.log('Loading matchMedia polyfill');
  }

  (window as any).matchMedia = function(query: string): MediaQueryList {
    return {
      matches: false,
      media: query,
      addListener: function() {},
      removeListener: function() {},
      addEventListener: function() {},
      removeEventListener: function() {},
      dispatchEvent: function() { return false; },
    };
  };

  status.matchMedia = 'polyfilled';
}

/**
 * CSS Custom Properties fallback
 */
async function loadCustomPropertiesFallback(status: PolyfillStatus, debug: boolean): Promise<void> {
  try {
    if (CSS.supports && CSS.supports('(--foo: red)')) {
      status.customProperties = 'native';
      return;
    }
  } catch {}

  if (debug) {
    console.log('CSS Custom Properties not supported, using fallback values');
  }

  // Apply fallback CSS variables as regular CSS properties
  const fallbackStyles = document.createElement('style');
  fallbackStyles.textContent = `
    /* Fallback for CSS custom properties */
    .fallback-theme--primary,
    .fallback-theme--primary * {
      color: #3674B5 !important;
    }
    
    .fallback-theme--accent,
    .fallback-theme--accent * {
      color: #F5F0CD !important;
    }
    
    /* Brand color fallbacks */
    .brand-primary { color: #3674B5 !important; }
    .brand-secondary { color: #578FCA !important; }
    .brand-accent-1 { color: #F5F0CD !important; }
    .brand-accent-2 { color: #FADA7A !important; }
    
    .bg-brand-primary { background-color: #3674B5 !important; }
    .bg-brand-secondary { background-color: #578FCA !important; }
    .bg-brand-accent-1 { background-color: #F5F0CD !important; }
    .bg-brand-accent-2 { background-color: #FADA7A !important; }
  `;
  
  document.head.appendChild(fallbackStyles);
  status.customProperties = 'fallback';
}

/**
 * Apply browser-specific fixes and optimizations
 */
function applyBrowserSpecificFixes(browser: BrowserInfo, debug: boolean): void {
  if (debug) {
    console.log('Applying browser-specific fixes for:', browser.name);
  }

  // Safari-specific fixes
  if (browser.name === 'Safari') {
    // Fix backdrop-filter for older Safari versions
    if (browser.majorVersion < 14) {
      const safariStyles = document.createElement('style');
      safariStyles.textContent = `
        .backdrop-blur {
          -webkit-backdrop-filter: blur(10px) !important;
          backdrop-filter: blur(10px) !important;
        }
      `;
      document.head.appendChild(safariStyles);
    }

    // iOS Safari viewport fixes
    if (browser.isMobile) {
      const iosStyles = document.createElement('style');
      iosStyles.textContent = `
        /* iOS Safari viewport fixes */
        body {
          -webkit-overflow-scrolling: touch;
        }
        
        .animation-container {
          transform: translate3d(0, 0, 0);
          -webkit-transform: translate3d(0, 0, 0);
        }
      `;
      document.head.appendChild(iosStyles);
    }
  }

  // Firefox-specific fixes
  if (browser.name === 'Firefox') {
    const firefoxStyles = document.createElement('style');
    firefoxStyles.textContent = `
      /* Firefox animation optimizations */
      .fallback-particle,
      .fallback-gradient-animation {
        will-change: transform, opacity;
      }
      
      /* Firefox WebGL context optimization */
      canvas {
        image-rendering: -moz-crisp-edges;
      }
    `;
    document.head.appendChild(firefoxStyles);
  }

  // Edge-specific fixes
  if (browser.name === 'Edge' && browser.majorVersion < 85) {
    const edgeStyles = document.createElement('style');
    edgeStyles.textContent = `
      /* Legacy Edge fixes */
      .fallback-gradient-animation {
        filter: none; /* Remove filter effects that may cause issues */
      }
    `;
    document.head.appendChild(edgeStyles);
  }

  // Mobile device optimizations
  if (browser.isMobile) {
    const mobileStyles = document.createElement('style');
    mobileStyles.textContent = `
      /* Mobile performance optimizations */
      .animation-container {
        -webkit-transform: translate3d(0, 0, 0);
        transform: translate3d(0, 0, 0);
        -webkit-perspective: 1000px;
        perspective: 1000px;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
      }
      
      /* Reduce animation complexity on mobile */
      @media (max-width: 768px) {
        .fallback-particle {
          animation-duration: 20s !important;
        }
        
        .vanta-canvas {
          will-change: auto !important;
        }
      }
    `;
    document.head.appendChild(mobileStyles);
  }
}

/**
 * Check if specific polyfill is loaded
 */
export function isPolyfillLoaded(feature: keyof PolyfillStatus): boolean {
  return polyfillStatus?.[feature] === 'polyfilled' || polyfillStatus?.[feature] === 'native';
}

/**
 * Get current polyfill status
 */
export function getPolyfillStatus(): PolyfillStatus | null {
  return polyfillStatus;
}

/**
 * Reset polyfills (for testing purposes)
 */
export function resetPolyfills(): void {
  polyfillsLoaded = false;
  polyfillStatus = null;
}

/**
 * Load specific polyfill manually
 */
export async function loadSpecificPolyfill(
  feature: keyof PolyfillStatus,
  debug: boolean = false
): Promise<'native' | 'polyfilled' | 'fallback' | 'unavailable'> {
  if (!polyfillStatus) {
    polyfillStatus = {
      requestAnimationFrame: 'unavailable',
      intersectionObserver: 'unavailable',
      resizeObserver: 'unavailable',
      webgl: 'unavailable',
      performanceMemory: 'unavailable',
      cssSupports: 'unavailable',
      matchMedia: 'unavailable',
      customProperties: 'unavailable',
    };
  }

  switch (feature) {
    case 'requestAnimationFrame':
      await loadRequestAnimationFramePolyfill(polyfillStatus, debug);
      break;
    case 'intersectionObserver':
      await loadIntersectionObserverPolyfill(polyfillStatus, debug);
      break;
    case 'resizeObserver':
      await loadResizeObserverPolyfill(polyfillStatus, debug);
      break;
    case 'webgl':
      await loadWebGLFallback(polyfillStatus, debug);
      break;
    case 'performanceMemory':
      await loadPerformanceMemoryPolyfill(polyfillStatus, debug);
      break;
    case 'cssSupports':
      await loadCSSSupportsPolyfill(polyfillStatus, debug);
      break;
    case 'matchMedia':
      await loadMatchMediaPolyfill(polyfillStatus, debug);
      break;
    case 'customProperties':
      await loadCustomPropertiesFallback(polyfillStatus, debug);
      break;
  }

  return polyfillStatus[feature];
}

export default {
  loadPolyfills,
  isPolyfillLoaded,
  getPolyfillStatus,
  resetPolyfills,
  loadSpecificPolyfill,
};