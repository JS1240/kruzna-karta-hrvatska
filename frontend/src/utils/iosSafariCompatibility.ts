/**
 * iOS Safari 13+ Compatibility Testing and Fixes
 * 
 * Comprehensive iOS Safari compatibility testing with automatic fixes
 * and optimizations for iOS Safari 13+ specific issues
 */

import { detectMobileBrowser, type IOSBrowserInfo } from './enhancedMobileBrowserDetection';

export interface IOSCompatibilityResult {
  platform: 'ios' | 'other';
  safariVersion: string;
  iosVersion: string;
  isSupported: boolean;
  features: IOSFeatureSupport;
  performance: IOSPerformanceMetrics;
  fixes: IOSCompatibilityFix[];
  recommendations: string[];
  score: number;
}

export interface IOSFeatureSupport {
  webgl: {
    supported: boolean;
    version: string;
    extensions: string[];
    maxTextureSize: number;
    maxRenderbufferSize: number;
    contextLossSupport: boolean;
  };
  css: {
    backdropFilter: boolean;
    webkitBackdropFilter: boolean;
    customProperties: boolean;
    gridLayout: boolean;
    flexbox: boolean;
    transforms3d: boolean;
    willChange: boolean;
    containment: boolean;
  };
  javascript: {
    intersectionObserver: boolean;
    resizeObserver: boolean;
    visualViewport: boolean;
    deviceMemory: boolean;
    performanceObserver: boolean;
    requestIdleCallback: boolean;
  };
  touch: {
    touchEvents: boolean;
    touchForceSupport: boolean;
    gestureEvents: boolean;
    maxTouchPoints: number;
    touchActionSupport: boolean;
  };
  viewport: {
    safeAreaSupport: boolean;
    viewportUnitsSupport: boolean;
    orientationSupport: boolean;
    standaloneMode: boolean;
  };
  media: {
    prefersReducedMotion: boolean;
    prefersColorScheme: boolean;
    hoverSupport: boolean;
    pointerSupport: boolean;
  };
}

export interface IOSPerformanceMetrics {
  memoryPressure: 'low' | 'medium' | 'high' | 'critical';
  webglPerformance: {
    fps: number;
    frameDrops: number;
    contextSwitches: number;
  };
  batteryImpact: 'low' | 'medium' | 'high';
  thermalState: 'nominal' | 'fair' | 'serious' | 'critical';
}

export interface IOSCompatibilityFix {
  issue: string;
  fix: string;
  applied: boolean;
  cssRules?: string;
  jsCode?: string;
}

/**
 * Run comprehensive iOS Safari compatibility test
 */
export async function testIOSSafariCompatibility(): Promise<IOSCompatibilityResult> {
  const browser = detectMobileBrowser();
  
  if (browser.platform !== 'ios') {
    return createNonIOSResult();
  }
  
  const iosBrowser = browser as IOSBrowserInfo;
  const isSupported = iosBrowser.majorVersion >= 13;
  
  // Test all iOS-specific features
  const features = await testIOSFeatures();
  const performance = await testIOSPerformance();
  const fixes = await applyIOSCompatibilityFixes(iosBrowser, features);
  const recommendations = generateIOSRecommendations(iosBrowser, features, performance);
  const score = calculateIOSCompatibilityScore(iosBrowser, features, performance);
  
  return {
    platform: 'ios',
    safariVersion: iosBrowser.version,
    iosVersion: iosBrowser.iosVersion,
    isSupported,
    features,
    performance,
    fixes,
    recommendations,
    score,
  };
}

/**
 * Test iOS-specific features
 */
async function testIOSFeatures(): Promise<IOSFeatureSupport> {
  const webgl = await testIOSWebGL();
  const css = testIOSCSS();
  const javascript = testIOSJavaScript();
  const touch = testIOSTouch();
  const viewport = testIOSViewport();
  const media = testIOSMedia();
  
  return {
    webgl,
    css,
    javascript,
    touch,
    viewport,
    media,
  };
}

/**
 * Test iOS WebGL capabilities with specific iOS limitations
 */
async function testIOSWebGL(): Promise<IOSFeatureSupport['webgl']> {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  
  let supported = false;
  let version = '';
  let extensions: string[] = [];
  let maxTextureSize = 0;
  let maxRenderbufferSize = 0;
  let contextLossSupport = false;
  
  try {
    const gl = canvas.getContext('webgl', {
      failIfMajorPerformanceCaveat: false,
      antialias: false, // iOS Safari preference
      alpha: false,
      depth: true,
      stencil: false,
      premultipliedAlpha: false,
      preserveDrawingBuffer: false,
      powerPreference: 'default', // iOS battery optimization
    }) || canvas.getContext('experimental-webgl');
    
    if (gl) {
      supported = true;
      version = gl.getParameter(gl.VERSION);
      
      // Get supported extensions
      const supportedExtensions = gl.getSupportedExtensions();
      extensions = supportedExtensions || [];
      
      // Test texture size limits (important for iOS)
      maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
      maxRenderbufferSize = gl.getParameter(gl.MAX_RENDERBUFFER_SIZE);
      
      // Test context loss handling (common on iOS)
      const lossExtension = gl.getExtension('WEBGL_lose_context');
      contextLossSupport = !!lossExtension;
      
      // Test if WebGL performance is acceptable on iOS
      const startTime = performance.now();
      
      // Simple rendering test
      gl.clearColor(0.0, 0.0, 0.0, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      
      const renderTime = performance.now() - startTime;
      
      // If rendering takes too long, WebGL might be software-rendered
      if (renderTime > 10) {
        console.warn('iOS WebGL may be software-rendered (slow performance detected)');
      }
    }
  } catch (error) {
    console.warn('iOS WebGL test failed:', error);
  }
  
  return {
    supported,
    version,
    extensions,
    maxTextureSize,
    maxRenderbufferSize,
    contextLossSupport,
  };
}

/**
 * Test iOS CSS features with WebKit-specific support
 */
function testIOSCSS(): IOSFeatureSupport['css'] {
  return {
    backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)'),
    webkitBackdropFilter: CSS.supports('-webkit-backdrop-filter', 'blur(10px)'),
    customProperties: CSS.supports('(--foo: red)'),
    gridLayout: CSS.supports('display', 'grid'),
    flexbox: CSS.supports('display', 'flex'),
    transforms3d: CSS.supports('transform', 'translate3d(0, 0, 0)'),
    willChange: CSS.supports('will-change', 'transform'),
    containment: CSS.supports('contain', 'layout style paint'),
  };
}

/**
 * Test iOS JavaScript API support
 */
function testIOSJavaScript(): IOSFeatureSupport['javascript'] {
  return {
    intersectionObserver: typeof IntersectionObserver !== 'undefined',
    resizeObserver: typeof ResizeObserver !== 'undefined',
    visualViewport: 'visualViewport' in window,
    deviceMemory: 'deviceMemory' in navigator,
    performanceObserver: typeof PerformanceObserver !== 'undefined',
    requestIdleCallback: typeof requestIdleCallback !== 'undefined',
  };
}

/**
 * Test iOS touch capabilities
 */
function testIOSTouch(): IOSFeatureSupport['touch'] {
  const touchEvents = 'ontouchstart' in window;
  const touchForceSupport = 'ontouchforcechange' in window;
  const gestureEvents = 'ongesturestart' in window;
  const maxTouchPoints = navigator.maxTouchPoints || 0;
  const touchActionSupport = CSS.supports('touch-action', 'manipulation');
  
  return {
    touchEvents,
    touchForceSupport,
    gestureEvents,
    maxTouchPoints,
    touchActionSupport,
  };
}

/**
 * Test iOS viewport features
 */
function testIOSViewport(): IOSFeatureSupport['viewport'] {
  const safeAreaSupport = CSS.supports('padding', 'env(safe-area-inset-top)');
  const viewportUnitsSupport = CSS.supports('height', '100vh');
  const orientationSupport = 'orientation' in screen;
  const standaloneMode = (navigator as any).standalone === true;
  
  return {
    safeAreaSupport,
    viewportUnitsSupport,
    orientationSupport,
    standaloneMode,
  };
}

/**
 * Test iOS media query support
 */
function testIOSMedia(): IOSFeatureSupport['media'] {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const prefersColorScheme = window.matchMedia('(prefers-color-scheme: dark)').media !== 'not all';
  const hoverSupport = window.matchMedia('(hover: hover)').matches;
  const pointerSupport = window.matchMedia('(pointer: fine)').matches;
  
  return {
    prefersReducedMotion,
    prefersColorScheme,
    hoverSupport,
    pointerSupport,
  };
}

/**
 * Test iOS performance characteristics
 */
async function testIOSPerformance(): Promise<IOSPerformanceMetrics> {
  // Memory pressure detection (iOS-specific heuristics)
  let memoryPressure: IOSPerformanceMetrics['memoryPressure'] = 'low';
  
  try {
    // Test memory allocation
    const testArrays = [];
    for (let i = 0; i < 10; i++) {
      testArrays.push(new Array(1000000).fill(0));
    }
    
    // Clean up
    testArrays.length = 0;
  } catch {
    memoryPressure = 'high';
  }
  
  // WebGL performance test
  const webglPerformance = await testIOSWebGLPerformance();
  
  // Battery impact estimation (based on feature usage)
  const batteryImpact = estimateBatteryImpact();
  
  // Thermal state (simplified detection)
  const thermalState = estimateThermalState();
  
  return {
    memoryPressure,
    webglPerformance,
    batteryImpact,
    thermalState,
  };
}

/**
 * Test iOS WebGL performance
 */
async function testIOSWebGLPerformance(): Promise<IOSPerformanceMetrics['webglPerformance']> {
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl');
  
  let fps = 0;
  let frameDrops = 0;
  let contextSwitches = 0;
  
  if (gl) {
    const startTime = performance.now();
    let frameCount = 0;
    let lastFrameTime = startTime;
    
    const renderFrame = (currentTime: number) => {
      frameCount++;
      
      const frameDelta = currentTime - lastFrameTime;
      if (frameDelta > 20) { // Frame drop (< 50fps)
        frameDrops++;
      }
      
      lastFrameTime = currentTime;
      
      // Simple rendering
      gl.clearColor(Math.random(), Math.random(), Math.random(), 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      
      if (currentTime - startTime < 1000) { // Test for 1 second
        requestAnimationFrame(renderFrame);
      } else {
        fps = frameCount;
      }
    };
    
    await new Promise<void>((resolve) => {
      requestAnimationFrame((time) => {
        renderFrame(time);
        setTimeout(resolve, 1100);
      });
    });
  }
  
  return {
    fps,
    frameDrops,
    contextSwitches,
  };
}

/**
 * Estimate battery impact
 */
function estimateBatteryImpact(): IOSPerformanceMetrics['batteryImpact'] {
  // Simplified battery impact estimation
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl');
  
  if (!gl) return 'low';
  
  // Test GPU-intensive operation
  const startTime = performance.now();
  for (let i = 0; i < 1000; i++) {
    gl.clearColor(Math.random(), Math.random(), Math.random(), 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);
  }
  const duration = performance.now() - startTime;
  
  if (duration > 100) return 'high';
  if (duration > 50) return 'medium';
  return 'low';
}

/**
 * Estimate thermal state
 */
function estimateThermalState(): IOSPerformanceMetrics['thermalState'] {
  // Simplified thermal state detection
  const userAgent = navigator.userAgent;
  
  // Older iOS devices more prone to thermal issues
  if (userAgent.includes('iPhone6') || userAgent.includes('iPhone5')) {
    return 'fair';
  }
  
  return 'nominal';
}

/**
 * Apply iOS-specific compatibility fixes
 */
async function applyIOSCompatibilityFixes(
  browser: IOSBrowserInfo,
  features: IOSFeatureSupport
): Promise<IOSCompatibilityFix[]> {
  const fixes: IOSCompatibilityFix[] = [];
  
  // Fix 1: WebKit backdrop-filter support
  if (!features.css.backdropFilter && features.css.webkitBackdropFilter) {
    const fix = applyWebKitBackdropFilterFix();
    fixes.push(fix);
  }
  
  // Fix 2: iOS viewport handling
  const viewportFix = applyIOSViewportFix(browser);
  fixes.push(viewportFix);
  
  // Fix 3: iOS scroll behavior
  const scrollFix = applyIOSScrollFix();
  fixes.push(scrollFix);
  
  // Fix 4: iOS WebGL context loss handling
  if (features.webgl.supported) {
    const webglFix = applyIOSWebGLFix();
    fixes.push(webglFix);
  }
  
  // Fix 5: iOS touch handling optimizations
  const touchFix = applyIOSTouchFix(features.touch);
  fixes.push(touchFix);
  
  // Fix 6: iOS safe area handling
  if (features.viewport.safeAreaSupport) {
    const safeAreaFix = applyIOSSafeAreaFix();
    fixes.push(safeAreaFix);
  }
  
  return fixes;
}

/**
 * Apply WebKit backdrop-filter fix
 */
function applyWebKitBackdropFilterFix(): IOSCompatibilityFix {
  const cssRules = `
    /* iOS Safari backdrop-filter fix */
    .backdrop-blur {
      -webkit-backdrop-filter: blur(10px);
      backdrop-filter: blur(10px);
    }
    
    .backdrop-blur-sm {
      -webkit-backdrop-filter: blur(4px);
      backdrop-filter: blur(4px);
    }
    
    .backdrop-blur-lg {
      -webkit-backdrop-filter: blur(20px);
      backdrop-filter: blur(20px);
    }
  `;
  
  const applied = applyCSSFix('ios-backdrop-filter', cssRules);
  
  return {
    issue: 'iOS Safari requires -webkit- prefix for backdrop-filter',
    fix: 'Added WebKit prefixed backdrop-filter CSS rules',
    applied,
    cssRules,
  };
}

/**
 * Apply iOS viewport fix
 */
function applyIOSViewportFix(browser: IOSBrowserInfo): IOSCompatibilityFix {
  const cssRules = `
    /* iOS Safari viewport fixes */
    html, body {
      -webkit-overflow-scrolling: touch;
      -webkit-text-size-adjust: 100%;
    }
    
    .ios-viewport-fix {
      /* Fix iOS viewport height issues */
      min-height: 100vh;
      min-height: -webkit-fill-available;
    }
    
    /* iOS safe area support */
    .ios-safe-area {
      padding-top: env(safe-area-inset-top);
      padding-right: env(safe-area-inset-right);
      padding-bottom: env(safe-area-inset-bottom);
      padding-left: env(safe-area-inset-left);
    }
    
    /* iOS standalone mode adjustments */
    @media (display-mode: standalone) {
      .ios-standalone {
        padding-top: env(safe-area-inset-top);
      }
    }
  `;
  
  const applied = applyCSSFix('ios-viewport', cssRules);
  
  return {
    issue: 'iOS Safari viewport and safe area handling',
    fix: 'Applied iOS-specific viewport and safe area CSS fixes',
    applied,
    cssRules,
  };
}

/**
 * Apply iOS scroll behavior fix
 */
function applyIOSScrollFix(): IOSCompatibilityFix {
  const cssRules = `
    /* iOS Safari scroll behavior fixes */
    .ios-scroll-fix {
      -webkit-overflow-scrolling: touch;
      overflow-scrolling: touch;
    }
    
    /* Prevent zoom on input focus */
    input, textarea, select {
      font-size: 16px;
    }
    
    /* Fix iOS scroll momentum */
    .animation-container {
      -webkit-transform: translate3d(0, 0, 0);
      transform: translate3d(0, 0, 0);
      -webkit-backface-visibility: hidden;
      backface-visibility: hidden;
    }
  `;
  
  const applied = applyCSSFix('ios-scroll', cssRules);
  
  return {
    issue: 'iOS Safari scroll behavior and momentum scrolling',
    fix: 'Applied iOS-specific scroll optimizations',
    applied,
    cssRules,
  };
}

/**
 * Apply iOS WebGL fix
 */
function applyIOSWebGLFix(): IOSCompatibilityFix {
  const jsCode = `
    // iOS WebGL context loss handling
    (function() {
      const canvas = document.querySelector('canvas');
      if (canvas) {
        canvas.addEventListener('webglcontextlost', function(event) {
          event.preventDefault();
          console.warn('WebGL context lost on iOS, switching to CSS fallback');
          // Trigger fallback system
          window.dispatchEvent(new CustomEvent('webgl-context-lost', {
            detail: { platform: 'ios', reason: 'context-lost' }
          }));
        });
        
        canvas.addEventListener('webglcontextrestored', function() {
          console.log('WebGL context restored on iOS');
          window.dispatchEvent(new CustomEvent('webgl-context-restored'));
        });
      }
    })();
  `;
  
  const applied = applyJSFix(jsCode);
  
  return {
    issue: 'iOS Safari WebGL context loss handling',
    fix: 'Added WebGL context loss event listeners for iOS',
    applied,
    jsCode,
  };
}

/**
 * Apply iOS touch fix
 */
function applyIOSTouchFix(touchFeatures: IOSFeatureSupport['touch']): IOSCompatibilityFix {
  const cssRules = `
    /* iOS Safari touch optimizations */
    .ios-touch-fix {
      -webkit-tap-highlight-color: transparent;
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      user-select: none;
    }
    
    .touch-action-manipulation {
      touch-action: manipulation;
    }
    
    /* iOS gesture handling */
    .ios-gesture-prevent {
      -webkit-user-select: none;
      user-select: none;
      -webkit-touch-callout: none;
      -webkit-tap-highlight-color: transparent;
    }
    
    /* Improve touch responsiveness */
    .animation-container {
      pointer-events: auto;
    }
    
    .animation-container * {
      pointer-events: none;
    }
  `;
  
  const applied = applyCSSFix('ios-touch', cssRules);
  
  return {
    issue: 'iOS Safari touch event optimization',
    fix: 'Applied iOS-specific touch and gesture handling',
    applied,
    cssRules,
  };
}

/**
 * Apply iOS safe area fix
 */
function applyIOSSafeAreaFix(): IOSCompatibilityFix {
  const cssRules = `
    /* iOS safe area insets */
    :root {
      --safe-area-inset-top: env(safe-area-inset-top);
      --safe-area-inset-right: env(safe-area-inset-right);
      --safe-area-inset-bottom: env(safe-area-inset-bottom);
      --safe-area-inset-left: env(safe-area-inset-left);
    }
    
    .safe-area-padding {
      padding-top: var(--safe-area-inset-top);
      padding-right: var(--safe-area-inset-right);
      padding-bottom: var(--safe-area-inset-bottom);
      padding-left: var(--safe-area-inset-left);
    }
    
    .safe-area-margin {
      margin-top: var(--safe-area-inset-top);
      margin-right: var(--safe-area-inset-right);
      margin-bottom: var(--safe-area-inset-bottom);
      margin-left: var(--safe-area-inset-left);
    }
  `;
  
  const applied = applyCSSFix('ios-safe-area', cssRules);
  
  return {
    issue: 'iOS safe area inset handling',
    fix: 'Added CSS custom properties for safe area insets',
    applied,
    cssRules,
  };
}

/**
 * Apply CSS fix
 */
function applyCSSFix(id: string, cssRules: string): boolean {
  try {
    const existingStyle = document.getElementById(id);
    if (existingStyle) {
      existingStyle.remove();
    }
    
    const styleElement = document.createElement('style');
    styleElement.id = id;
    styleElement.textContent = cssRules;
    document.head.appendChild(styleElement);
    
    return true;
  } catch (error) {
    console.error(`Failed to apply CSS fix ${id}:`, error);
    return false;
  }
}

/**
 * Apply JavaScript fix
 */
function applyJSFix(jsCode: string): boolean {
  try {
    const script = new Function(jsCode);
    script();
    return true;
  } catch (error) {
    console.error('Failed to apply JS fix:', error);
    return false;
  }
}

/**
 * Generate iOS-specific recommendations
 */
function generateIOSRecommendations(
  browser: IOSBrowserInfo,
  features: IOSFeatureSupport,
  performance: IOSPerformanceMetrics
): string[] {
  const recommendations: string[] = [];
  
  if (browser.majorVersion < 13) {
    recommendations.push('Update to iOS 13 or later for better Safari support');
  }
  
  if (!features.webgl.supported) {
    recommendations.push('Enable hardware acceleration in Safari settings');
  }
  
  if (performance.memoryPressure === 'high') {
    recommendations.push('Close other apps to free up memory for better animation performance');
  }
  
  if (performance.batteryImpact === 'high') {
    recommendations.push('Animations will be simplified to preserve battery life');
  }
  
  if (!features.css.backdropFilter && !features.css.webkitBackdropFilter) {
    recommendations.push('Some blur effects may not be available on this iOS version');
  }
  
  if (features.viewport.standaloneMode) {
    recommendations.push('Running in standalone mode - optimizations applied');
  }
  
  return recommendations;
}

/**
 * Calculate iOS compatibility score
 */
function calculateIOSCompatibilityScore(
  browser: IOSBrowserInfo,
  features: IOSFeatureSupport,
  performance: IOSPerformanceMetrics
): number {
  let score = 100;
  
  // Browser version
  if (browser.majorVersion < 13) score -= 40;
  else if (browser.majorVersion < 14) score -= 10;
  
  // WebGL support
  if (!features.webgl.supported) score -= 30;
  else if (features.webgl.extensions.length < 10) score -= 10;
  
  // CSS features
  if (!features.css.backdropFilter && !features.css.webkitBackdropFilter) score -= 15;
  if (!features.css.customProperties) score -= 10;
  if (!features.css.transforms3d) score -= 10;
  
  // Performance impact
  if (performance.memoryPressure === 'high') score -= 20;
  else if (performance.memoryPressure === 'medium') score -= 10;
  
  if (performance.webglPerformance.fps < 20) score -= 20;
  else if (performance.webglPerformance.fps < 30) score -= 10;
  
  return Math.max(0, score);
}

/**
 * Create result for non-iOS platforms
 */
function createNonIOSResult(): IOSCompatibilityResult {
  return {
    platform: 'other',
    safariVersion: 'N/A',
    iosVersion: 'N/A',
    isSupported: false,
    features: {} as IOSFeatureSupport,
    performance: {} as IOSPerformanceMetrics,
    fixes: [],
    recommendations: ['This test is designed for iOS Safari only'],
    score: 0,
  };
}

export default {
  testIOSSafariCompatibility,
};