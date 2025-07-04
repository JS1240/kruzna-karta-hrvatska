/**
 * Chrome Mobile 80+ Compatibility Testing and Optimization
 * 
 * Comprehensive Chrome Mobile compatibility testing with automatic optimizations
 * and performance tuning for Chrome Mobile 80+ specific features
 */

import { detectMobileBrowser, type AndroidBrowserInfo } from './enhancedMobileBrowserDetection';

export interface ChromeMobileCompatibilityResult {
  platform: 'android' | 'other';
  chromeVersion: string;
  androidVersion: string;
  isSupported: boolean;
  features: ChromeMobileFeatureSupport;
  performance: ChromeMobilePerformanceMetrics;
  optimizations: ChromeMobileOptimization[];
  recommendations: string[];
  score: number;
}

export interface ChromeMobileFeatureSupport {
  webgl: {
    webgl1: boolean;
    webgl2: boolean;
    extensions: string[];
    maxTextureSize: number;
    maxVertexAttribs: number;
    floatTextures: boolean;
    depthTextures: boolean;
    instancedRendering: boolean;
  };
  css: {
    customProperties: boolean;
    backdropFilter: boolean;
    gridLayout: boolean;
    flexbox: boolean;
    containment: boolean;
    willChange: boolean;
    transforms3d: boolean;
    clipPath: boolean;
  };
  javascript: {
    es6Modules: boolean;
    intersectionObserver: boolean;
    resizeObserver: boolean;
    performanceObserver: boolean;
    mutationObserver: boolean;
    requestIdleCallback: boolean;
    webWorkers: boolean;
    serviceWorkers: boolean;
    webAssembly: boolean;
  };
  device: {
    deviceMemoryAPI: boolean;
    hardwareConcurrency: boolean;
    networkInformation: boolean;
    batteryAPI: boolean;
    sensorAPIs: boolean;
    geolocation: boolean;
  };
  graphics: {
    offscreenCanvas: boolean;
    canvasFilters: boolean;
    webGPU: boolean;
    imageCapture: boolean;
    webCodecs: boolean;
  };
  performance: {
    performanceMemory: boolean;
    performanceMark: boolean;
    performanceMeasure: boolean;
    performanceNavigation: boolean;
    performanceTiming: boolean;
    userTiming: boolean;
  };
}

export interface ChromeMobilePerformanceMetrics {
  renderingPerformance: {
    fps: number;
    frameDrops: number;
    averageFrameTime: number;
    jankScore: number;
  };
  memoryUsage: {
    jsHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
    pressureLevel: 'low' | 'medium' | 'high';
  };
  gpuPerformance: {
    webglContexts: number;
    maxTextureUnits: number;
    shaderCompileTime: number;
    drawCallOverhead: number;
  };
  networkPerformance: {
    effectiveType: string;
    downlink: number;
    rtt: number;
    saveData: boolean;
  };
  batteryImpact: {
    estimatedUsage: 'low' | 'medium' | 'high';
    optimizationsApplied: string[];
  };
}

export interface ChromeMobileOptimization {
  category: 'performance' | 'memory' | 'battery' | 'graphics' | 'network';
  name: string;
  description: string;
  applied: boolean;
  impact: 'low' | 'medium' | 'high';
  cssRules?: string;
  jsCode?: string;
}

/**
 * Run comprehensive Chrome Mobile compatibility test
 */
export async function testChromeMobileCompatibility(): Promise<ChromeMobileCompatibilityResult> {
  const browser = detectMobileBrowser();
  
  if (browser.platform !== 'android' || !browser.name.includes('Chrome')) {
    return createNonChromeResult();
  }
  
  const chromeBrowser = browser as AndroidBrowserInfo;
  const isSupported = chromeBrowser.majorVersion >= 80;
  
  // Test all Chrome Mobile-specific features
  const features = await testChromeMobileFeatures();
  const performance = await testChromeMobilePerformance();
  const optimizations = await applyChromeMobileOptimizations(chromeBrowser, features, performance);
  const recommendations = generateChromeMobileRecommendations(chromeBrowser, features, performance);
  const score = calculateChromeMobileCompatibilityScore(chromeBrowser, features, performance);
  
  return {
    platform: 'android',
    chromeVersion: chromeBrowser.version,
    androidVersion: chromeBrowser.androidVersion,
    isSupported,
    features,
    performance,
    optimizations,
    recommendations,
    score,
  };
}

/**
 * Test Chrome Mobile-specific features
 */
async function testChromeMobileFeatures(): Promise<ChromeMobileFeatureSupport> {
  const webgl = await testChromeMobileWebGL();
  const css = testChromeMobileCSS();
  const javascript = testChromeMobileJavaScript();
  const device = testChromeMobileDevice();
  const graphics = testChromeMobileGraphics();
  const performance = testChromeMobilePerformanceAPIs();
  
  return {
    webgl,
    css,
    javascript,
    device,
    graphics,
    performance,
  };
}

/**
 * Test Chrome Mobile WebGL capabilities
 */
async function testChromeMobileWebGL(): Promise<ChromeMobileFeatureSupport['webgl']> {
  const canvas = document.createElement('canvas');
  
  let webgl1 = false;
  let webgl2 = false;
  let extensions: string[] = [];
  let maxTextureSize = 0;
  let maxVertexAttribs = 0;
  let floatTextures = false;
  let depthTextures = false;
  let instancedRendering = false;
  
  try {
    // Test WebGL 1.0
    const gl1 = canvas.getContext('webgl', {
      powerPreference: 'high-performance',
      antialias: true,
      alpha: false,
      depth: true,
      stencil: false,
      premultipliedAlpha: false,
      preserveDrawingBuffer: false,
    });
    
    if (gl1) {
      webgl1 = true;
      extensions = gl1.getSupportedExtensions() || [];
      maxTextureSize = gl1.getParameter(gl1.MAX_TEXTURE_SIZE);
      maxVertexAttribs = gl1.getParameter(gl1.MAX_VERTEX_ATTRIBS);
      
      // Test for float texture support
      floatTextures = !!gl1.getExtension('OES_texture_float');
      
      // Test for depth texture support
      depthTextures = !!gl1.getExtension('WEBGL_depth_texture');
      
      // Test for instanced rendering
      instancedRendering = !!gl1.getExtension('ANGLE_instanced_arrays');
    }
    
    // Test WebGL 2.0
    const gl2 = canvas.getContext('webgl2');
    if (gl2) {
      webgl2 = true;
    }
    
  } catch (error) {
    console.warn('Chrome Mobile WebGL test failed:', error);
  }
  
  return {
    webgl1,
    webgl2,
    extensions,
    maxTextureSize,
    maxVertexAttribs,
    floatTextures,
    depthTextures,
    instancedRendering,
  };
}

/**
 * Test Chrome Mobile CSS features
 */
function testChromeMobileCSS(): ChromeMobileFeatureSupport['css'] {
  return {
    customProperties: CSS.supports('(--foo: red)'),
    backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)'),
    gridLayout: CSS.supports('display', 'grid'),
    flexbox: CSS.supports('display', 'flex'),
    containment: CSS.supports('contain', 'layout style paint'),
    willChange: CSS.supports('will-change', 'transform'),
    transforms3d: CSS.supports('transform', 'translate3d(0, 0, 0)'),
    clipPath: CSS.supports('clip-path', 'circle(50%)'),
  };
}

/**
 * Test Chrome Mobile JavaScript features
 */
function testChromeMobileJavaScript(): ChromeMobileFeatureSupport['javascript'] {
  return {
    es6Modules: typeof Symbol !== 'undefined' && typeof Symbol.iterator !== 'undefined',
    intersectionObserver: typeof IntersectionObserver !== 'undefined',
    resizeObserver: typeof ResizeObserver !== 'undefined',
    performanceObserver: typeof PerformanceObserver !== 'undefined',
    mutationObserver: typeof MutationObserver !== 'undefined',
    requestIdleCallback: typeof requestIdleCallback !== 'undefined',
    webWorkers: typeof Worker !== 'undefined',
    serviceWorkers: 'serviceWorker' in navigator,
    webAssembly: typeof WebAssembly !== 'undefined',
  };
}

/**
 * Test Chrome Mobile device APIs
 */
function testChromeMobileDevice(): ChromeMobileFeatureSupport['device'] {
  return {
    deviceMemoryAPI: 'deviceMemory' in navigator,
    hardwareConcurrency: 'hardwareConcurrency' in navigator,
    networkInformation: 'connection' in navigator,
    batteryAPI: 'getBattery' in navigator,
    sensorAPIs: 'DeviceOrientationEvent' in window,
    geolocation: 'geolocation' in navigator,
  };
}

/**
 * Test Chrome Mobile graphics features
 */
function testChromeMobileGraphics(): ChromeMobileFeatureSupport['graphics'] {
  return {
    offscreenCanvas: typeof OffscreenCanvas !== 'undefined',
    canvasFilters: CSS.supports('filter', 'blur(5px)'),
    webGPU: 'gpu' in navigator,
    imageCapture: 'ImageCapture' in window,
    webCodecs: 'VideoEncoder' in window,
  };
}

/**
 * Test Chrome Mobile performance APIs
 */
function testChromeMobilePerformanceAPIs(): ChromeMobileFeatureSupport['performance'] {
  return {
    performanceMemory: 'memory' in performance,
    performanceMark: 'mark' in performance,
    performanceMeasure: 'measure' in performance,
    performanceNavigation: 'navigation' in performance,
    performanceTiming: 'timing' in performance,
    userTiming: typeof PerformanceObserver !== 'undefined',
  };
}

/**
 * Test Chrome Mobile performance metrics
 */
async function testChromeMobilePerformance(): Promise<ChromeMobilePerformanceMetrics> {
  const renderingPerformance = await testRenderingPerformance();
  const memoryUsage = testMemoryUsage();
  const gpuPerformance = await testGPUPerformance();
  const networkPerformance = testNetworkPerformance();
  const batteryImpact = estimateBatteryImpact();
  
  return {
    renderingPerformance,
    memoryUsage,
    gpuPerformance,
    networkPerformance,
    batteryImpact,
  };
}

/**
 * Test rendering performance
 */
async function testRenderingPerformance(): Promise<ChromeMobilePerformanceMetrics['renderingPerformance']> {
  return new Promise((resolve) => {
    let frameCount = 0;
    let frameDrops = 0;
    let totalFrameTime = 0;
    let jankCount = 0;
    const startTime = performance.now();
    let lastFrameTime = startTime;
    
    const testFrame = (currentTime: number) => {
      frameCount++;
      const frameDelta = currentTime - lastFrameTime;
      totalFrameTime += frameDelta;
      
      // Count frame drops (> 16.67ms = below 60fps)
      if (frameDelta > 16.67) {
        frameDrops++;
      }
      
      // Count jank (> 50ms frame time)
      if (frameDelta > 50) {
        jankCount++;
      }
      
      lastFrameTime = currentTime;
      
      if (currentTime - startTime < 2000) { // Test for 2 seconds
        requestAnimationFrame(testFrame);
      } else {
        const fps = (frameCount / 2); // frames per second
        const averageFrameTime = totalFrameTime / frameCount;
        const jankScore = (jankCount / frameCount) * 100;
        
        resolve({
          fps,
          frameDrops,
          averageFrameTime,
          jankScore,
        });
      }
    };
    
    requestAnimationFrame(testFrame);
  });
}

/**
 * Test memory usage
 */
function testMemoryUsage(): ChromeMobilePerformanceMetrics['memoryUsage'] {
  let jsHeapSize = 0;
  let totalJSHeapSize = 0;
  let jsHeapSizeLimit = 0;
  let pressureLevel: 'low' | 'medium' | 'high' = 'low';
  
  if ('memory' in performance) {
    const memInfo = (performance as any).memory;
    jsHeapSize = memInfo.usedJSHeapSize;
    totalJSHeapSize = memInfo.totalJSHeapSize;
    jsHeapSizeLimit = memInfo.jsHeapSizeLimit;
    
    // Calculate pressure level
    const usageRatio = jsHeapSize / jsHeapSizeLimit;
    if (usageRatio > 0.8) pressureLevel = 'high';
    else if (usageRatio > 0.5) pressureLevel = 'medium';
  }
  
  return {
    jsHeapSize,
    totalJSHeapSize,
    jsHeapSizeLimit,
    pressureLevel,
  };
}

/**
 * Test GPU performance
 */
async function testGPUPerformance(): Promise<ChromeMobilePerformanceMetrics['gpuPerformance']> {
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl');
  
  let webglContexts = 1;
  let maxTextureUnits = 0;
  let shaderCompileTime = 0;
  let drawCallOverhead = 0;
  
  if (gl) {
    maxTextureUnits = gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS);
    
    // Test shader compile time
    const startCompileTime = performance.now();
    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    if (vertexShader) {
      gl.shaderSource(vertexShader, `
        attribute vec4 position;
        void main() {
          gl_Position = position;
        }
      `);
      gl.compileShader(vertexShader);
    }
    shaderCompileTime = performance.now() - startCompileTime;
    
    // Test draw call overhead
    const startDrawTime = performance.now();
    for (let i = 0; i < 100; i++) {
      gl.clear(gl.COLOR_BUFFER_BIT);
    }
    drawCallOverhead = (performance.now() - startDrawTime) / 100;
  }
  
  return {
    webglContexts,
    maxTextureUnits,
    shaderCompileTime,
    drawCallOverhead,
  };
}

/**
 * Test network performance
 */
function testNetworkPerformance(): ChromeMobilePerformanceMetrics['networkPerformance'] {
  const connection = (navigator as any).connection || 
                    (navigator as any).mozConnection || 
                    (navigator as any).webkitConnection;
  
  return {
    effectiveType: connection?.effectiveType || 'unknown',
    downlink: connection?.downlink || 0,
    rtt: connection?.rtt || 0,
    saveData: connection?.saveData || false,
  };
}

/**
 * Estimate battery impact
 */
function estimateBatteryImpact(): ChromeMobilePerformanceMetrics['batteryImpact'] {
  const optimizationsApplied: string[] = [];
  let estimatedUsage: 'low' | 'medium' | 'high' = 'low';
  
  // Simple heuristics for battery impact
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl');
  
  if (gl) {
    // Test GPU usage impact
    const startTime = performance.now();
    for (let i = 0; i < 1000; i++) {
      gl.clear(gl.COLOR_BUFFER_BIT);
    }
    const duration = performance.now() - startTime;
    
    if (duration > 100) {
      estimatedUsage = 'high';
      optimizationsApplied.push('GPU usage reduction');
    } else if (duration > 50) {
      estimatedUsage = 'medium';
      optimizationsApplied.push('Moderate GPU optimization');
    }
  }
  
  // Check device memory for battery optimization
  const deviceMemory = (navigator as any).deviceMemory;
  if (deviceMemory && deviceMemory <= 4) {
    optimizationsApplied.push('Low memory device optimization');
  }
  
  return {
    estimatedUsage,
    optimizationsApplied,
  };
}

/**
 * Apply Chrome Mobile optimizations
 */
async function applyChromeMobileOptimizations(
  browser: AndroidBrowserInfo,
  features: ChromeMobileFeatureSupport,
  performance: ChromeMobilePerformanceMetrics
): Promise<ChromeMobileOptimization[]> {
  const optimizations: ChromeMobileOptimization[] = [];
  
  // Performance optimizations
  optimizations.push(await applyPerformanceOptimizations(performance));
  
  // Memory optimizations
  optimizations.push(await applyMemoryOptimizations(performance.memoryUsage));
  
  // Graphics optimizations
  optimizations.push(await applyGraphicsOptimizations(features.webgl));
  
  // Network optimizations
  optimizations.push(await applyNetworkOptimizations(performance.networkPerformance));
  
  // Battery optimizations
  optimizations.push(await applyBatteryOptimizations(performance.batteryImpact));
  
  return optimizations.filter(opt => opt.applied);
}

/**
 * Apply performance optimizations
 */
async function applyPerformanceOptimizations(
  performance: ChromeMobilePerformanceMetrics['renderingPerformance']
): Promise<ChromeMobileOptimization> {
  const cssRules = `
    /* Chrome Mobile performance optimizations */
    .chrome-mobile-optimized {
      contain: layout style paint;
      will-change: transform;
    }
    
    .animation-container {
      transform: translateZ(0);
      backface-visibility: hidden;
    }
    
    /* Reduce repaints and reflows */
    .fallback-particle {
      contain: strict;
      will-change: transform, opacity;
    }
    
    /* GPU acceleration for animations */
    .gpu-accelerated {
      transform: translate3d(0, 0, 0);
      will-change: transform;
    }
  `;
  
  const applied = applyCSSOptimization('chrome-performance', cssRules);
  
  return {
    category: 'performance',
    name: 'Chrome Mobile Performance Optimization',
    description: 'Applied CSS containment and GPU acceleration for better performance',
    applied,
    impact: performance.fps < 30 ? 'high' : performance.fps < 45 ? 'medium' : 'low',
    cssRules,
  };
}

/**
 * Apply memory optimizations
 */
async function applyMemoryOptimizations(
  memoryUsage: ChromeMobilePerformanceMetrics['memoryUsage']
): Promise<ChromeMobileOptimization> {
  const jsCode = `
    // Chrome Mobile memory optimization
    (function() {
      if ('memory' in performance) {
        const checkMemoryPressure = () => {
          const memInfo = performance.memory;
          const usageRatio = memInfo.usedJSHeapSize / memInfo.jsHeapSizeLimit;
          
          if (usageRatio > 0.8) {
            // High memory pressure - trigger cleanup
            window.dispatchEvent(new CustomEvent('memory-pressure-high', {
              detail: { usageRatio, memInfo }
            }));
          } else if (usageRatio > 0.5) {
            // Medium memory pressure
            window.dispatchEvent(new CustomEvent('memory-pressure-medium', {
              detail: { usageRatio, memInfo }
            }));
          }
        };
        
        // Check memory every 10 seconds
        setInterval(checkMemoryPressure, 10000);
        checkMemoryPressure(); // Initial check
      }
    })();
  `;
  
  const applied = applyJSOptimization(jsCode);
  
  return {
    category: 'memory',
    name: 'Chrome Mobile Memory Monitoring',
    description: 'Added memory pressure monitoring and cleanup triggers',
    applied,
    impact: memoryUsage.pressureLevel === 'high' ? 'high' : 'medium',
    jsCode,
  };
}

/**
 * Apply graphics optimizations
 */
async function applyGraphicsOptimizations(
  webglFeatures: ChromeMobileFeatureSupport['webgl']
): Promise<ChromeMobileOptimization> {
  const jsCode = `
    // Chrome Mobile WebGL optimizations
    (function() {
      const originalGetContext = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(contextId, options) {
        if (contextId === 'webgl' || contextId === 'webgl2') {
          // Chrome Mobile optimized WebGL context
          const optimizedOptions = {
            alpha: false,
            antialias: ${webglFeatures.webgl2 ? 'true' : 'false'},
            depth: true,
            stencil: false,
            premultipliedAlpha: false,
            preserveDrawingBuffer: false,
            powerPreference: 'high-performance',
            ...options
          };
          
          return originalGetContext.call(this, contextId, optimizedOptions);
        }
        
        return originalGetContext.call(this, contextId, options);
      };
    })();
  `;
  
  const applied = applyJSOptimization(jsCode);
  
  return {
    category: 'graphics',
    name: 'Chrome Mobile WebGL Optimization',
    description: 'Optimized WebGL context creation for Chrome Mobile',
    applied,
    impact: webglFeatures.webgl1 ? 'medium' : 'low',
    jsCode,
  };
}

/**
 * Apply network optimizations
 */
async function applyNetworkOptimizations(
  networkPerformance: ChromeMobilePerformanceMetrics['networkPerformance']
): Promise<ChromeMobileOptimization> {
  const cssRules = `
    /* Chrome Mobile network optimizations */
    ${networkPerformance.saveData || networkPerformance.effectiveType === 'slow-2g' || networkPerformance.effectiveType === '2g' ? `
    .network-optimized .fallback-particle {
      display: none !important;
    }
    
    .network-optimized .vanta-canvas {
      display: none !important;
    }
    
    .network-optimized .animation-container {
      background: linear-gradient(135deg, #3674B5 0%, #578FCA 100%) !important;
    }
    ` : ''}
    
    /* Reduce animations on slow connections */
    @media (prefers-reduced-data: reduce) {
      .fallback-gradient-animation {
        animation: none !important;
      }
    }
  `;
  
  const applied = applyCSSOptimization('chrome-network', cssRules);
  
  return {
    category: 'network',
    name: 'Chrome Mobile Network Optimization',
    description: 'Applied optimizations for slow network connections',
    applied,
    impact: networkPerformance.saveData || ['slow-2g', '2g'].includes(networkPerformance.effectiveType) ? 'high' : 'low',
    cssRules,
  };
}

/**
 * Apply battery optimizations
 */
async function applyBatteryOptimizations(
  batteryImpact: ChromeMobilePerformanceMetrics['batteryImpact']
): Promise<ChromeMobileOptimization> {
  const jsCode = `
    // Chrome Mobile battery optimizations
    (function() {
      if ('getBattery' in navigator) {
        navigator.getBattery().then(function(battery) {
          const updateBatteryOptimization = () => {
            const isCharging = battery.charging;
            const batteryLevel = battery.level;
            
            if (!isCharging && batteryLevel < 0.2) {
              // Low battery - aggressive optimization
              window.dispatchEvent(new CustomEvent('battery-optimization-aggressive'));
            } else if (!isCharging && batteryLevel < 0.5) {
              // Medium battery - moderate optimization
              window.dispatchEvent(new CustomEvent('battery-optimization-moderate'));
            }
          };
          
          battery.addEventListener('chargingchange', updateBatteryOptimization);
          battery.addEventListener('levelchange', updateBatteryOptimization);
          updateBatteryOptimization();
        });
      }
    })();
  `;
  
  const applied = applyJSOptimization(jsCode);
  
  return {
    category: 'battery',
    name: 'Chrome Mobile Battery Optimization',
    description: 'Added battery-aware optimization controls',
    applied,
    impact: batteryImpact.estimatedUsage === 'high' ? 'high' : 'medium',
    jsCode,
  };
}

/**
 * Apply CSS optimization
 */
function applyCSSOptimization(id: string, cssRules: string): boolean {
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
    console.error(`Failed to apply CSS optimization ${id}:`, error);
    return false;
  }
}

/**
 * Apply JavaScript optimization
 */
function applyJSOptimization(jsCode: string): boolean {
  try {
    const script = new Function(jsCode);
    script();
    return true;
  } catch (error) {
    console.error('Failed to apply JS optimization:', error);
    return false;
  }
}

/**
 * Generate Chrome Mobile recommendations
 */
function generateChromeMobileRecommendations(
  browser: AndroidBrowserInfo,
  features: ChromeMobileFeatureSupport,
  performance: ChromeMobilePerformanceMetrics
): string[] {
  const recommendations: string[] = [];
  
  if (browser.majorVersion < 80) {
    recommendations.push('Update Chrome to version 80 or later for better compatibility');
  }
  
  if (!features.webgl.webgl2) {
    recommendations.push('WebGL 2.0 not supported - some advanced graphics features may be limited');
  }
  
  if (performance.memoryUsage.pressureLevel === 'high') {
    recommendations.push('High memory usage detected - close other apps for better performance');
  }
  
  if (performance.renderingPerformance.fps < 30) {
    recommendations.push('Low rendering performance - animations will be simplified');
  }
  
  if (performance.networkPerformance.saveData) {
    recommendations.push('Data saver mode detected - animations will be reduced');
  }
  
  if (performance.batteryImpact.estimatedUsage === 'high') {
    recommendations.push('High battery usage expected - enabling power saving optimizations');
  }
  
  if (!features.device.deviceMemoryAPI) {
    recommendations.push('Device Memory API not available - using conservative memory settings');
  }
  
  return recommendations;
}

/**
 * Calculate Chrome Mobile compatibility score
 */
function calculateChromeMobileCompatibilityScore(
  browser: AndroidBrowserInfo,
  features: ChromeMobileFeatureSupport,
  performance: ChromeMobilePerformanceMetrics
): number {
  let score = 100;
  
  // Browser version
  if (browser.majorVersion < 80) score -= 40;
  else if (browser.majorVersion < 90) score -= 5;
  
  // WebGL support
  if (!features.webgl.webgl1) score -= 30;
  else if (!features.webgl.webgl2) score -= 10;
  
  if (features.webgl.extensions.length < 15) score -= 5;
  
  // CSS features
  if (!features.css.backdropFilter) score -= 10;
  if (!features.css.customProperties) score -= 15;
  if (!features.css.containment) score -= 10;
  
  // JavaScript features
  if (!features.javascript.intersectionObserver) score -= 10;
  if (!features.javascript.performanceObserver) score -= 5;
  if (!features.javascript.webWorkers) score -= 5;
  
  // Performance impact
  if (performance.memoryUsage.pressureLevel === 'high') score -= 20;
  else if (performance.memoryUsage.pressureLevel === 'medium') score -= 10;
  
  if (performance.renderingPerformance.fps < 30) score -= 20;
  else if (performance.renderingPerformance.fps < 45) score -= 10;
  
  if (performance.renderingPerformance.jankScore > 10) score -= 10;
  
  // Network impact
  if (performance.networkPerformance.saveData) score -= 5;
  if (['slow-2g', '2g'].includes(performance.networkPerformance.effectiveType)) score -= 10;
  
  return Math.max(0, score);
}

/**
 * Create result for non-Chrome platforms
 */
function createNonChromeResult(): ChromeMobileCompatibilityResult {
  return {
    platform: 'other',
    chromeVersion: 'N/A',
    androidVersion: 'N/A',
    isSupported: false,
    features: {} as ChromeMobileFeatureSupport,
    performance: {} as ChromeMobilePerformanceMetrics,
    optimizations: [],
    recommendations: ['This test is designed for Chrome Mobile only'],
    score: 0,
  };
}

export default {
  testChromeMobileCompatibility,
};