/**
 * Browser Compatibility Testing Utility
 * 
 * Comprehensive browser detection, feature testing, and compatibility
 * assessment for animations across Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
 */

export interface BrowserInfo {
  name: string;
  version: string;
  majorVersion: number;
  engine: string;
  platform: string;
  isMobile: boolean;
  isSupported: boolean;
}

export interface FeatureSupport {
  webgl: boolean;
  webgl2: boolean;
  webglExtensions: string[];
  css: {
    customProperties: boolean;
    backdropFilter: boolean;
    willChange: boolean;
    transform3d: boolean;
    animations: boolean;
    transitions: boolean;
    gridLayout: boolean;
    flexbox: boolean;
  };
  javascript: {
    requestAnimationFrame: boolean;
    performanceMemory: boolean;
    intersectionObserver: boolean;
    resizeObserver: boolean;
    matchMedia: boolean;
    getComputedStyle: boolean;
    webWorkers: boolean;
    serviceWorker: boolean;
  };
  media: {
    prefersReducedMotion: boolean;
    prefersColorScheme: boolean;
    orientation: boolean;
    hover: boolean;
  };
  performance: {
    performanceAPI: boolean;
    performanceObserver: boolean;
    performanceTiming: boolean;
    highResTime: boolean;
  };
}

export interface BrowserCompatibility {
  browser: BrowserInfo;
  features: FeatureSupport;
  score: number;
  warnings: string[];
  recommendations: string[];
  fallbacksNeeded: string[];
}

/**
 * Detect browser information
 */
export function detectBrowser(): BrowserInfo {
  const userAgent = navigator.userAgent;
  const platform = navigator.platform;
  
  let name = 'Unknown';
  let version = '0';
  let engine = 'Unknown';
  
  // Chrome detection
  if (userAgent.includes('Chrome') && !userAgent.includes('Edg')) {
    name = 'Chrome';
    const match = userAgent.match(/Chrome\/(\d+\.\d+)/);
    version = match ? match[1] : '0';
    engine = 'Blink';
  }
  // Edge (Chromium-based) detection
  else if (userAgent.includes('Edg')) {
    name = 'Edge';
    const match = userAgent.match(/Edg\/(\d+\.\d+)/);
    version = match ? match[1] : '0';
    engine = 'Blink';
  }
  // Firefox detection
  else if (userAgent.includes('Firefox')) {
    name = 'Firefox';
    const match = userAgent.match(/Firefox\/(\d+\.\d+)/);
    version = match ? match[1] : '0';
    engine = 'Gecko';
  }
  // Safari detection
  else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
    name = 'Safari';
    const match = userAgent.match(/Version\/(\d+\.\d+)/);
    version = match ? match[1] : '0';
    engine = 'WebKit';
  }
  
  const majorVersion = parseInt(version.split('.')[0]);
  const isMobile = /iPhone|iPad|iPod|Android|Mobile/i.test(userAgent);
  
  // Check if browser version meets minimum requirements
  const isSupported = checkMinimumVersionSupport(name, majorVersion);
  
  return {
    name,
    version,
    majorVersion,
    engine,
    platform,
    isMobile,
    isSupported,
  };
}

/**
 * Check minimum version support
 */
function checkMinimumVersionSupport(browserName: string, majorVersion: number): boolean {
  const minimumVersions = {
    'Chrome': 80,
    'Firefox': 75,
    'Safari': 13,
    'Edge': 80,
  };
  
  return majorVersion >= (minimumVersions[browserName as keyof typeof minimumVersions] || 0);
}

/**
 * Test WebGL capabilities
 */
function testWebGLSupport(): { webgl: boolean; webgl2: boolean; extensions: string[] } {
  const canvas = document.createElement('canvas');
  
  try {
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    const gl2 = canvas.getContext('webgl2');
    
    const extensions: string[] = [];
    
    if (gl) {
      const supportedExtensions = gl.getSupportedExtensions();
      if (supportedExtensions) {
        extensions.push(...supportedExtensions);
      }
    }
    
    return {
      webgl: !!gl,
      webgl2: !!gl2,
      extensions,
    };
  } catch (error) {
    return {
      webgl: false,
      webgl2: false,
      extensions: [],
    };
  }
}

/**
 * Test CSS feature support
 */
function testCSSSupport(): FeatureSupport['css'] {
  const testElement = document.createElement('div');
  const computedStyle = window.getComputedStyle(testElement);
  
  return {
    customProperties: CSS.supports('(--foo: red)'),
    backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)') || CSS.supports('-webkit-backdrop-filter', 'blur(10px)'),
    willChange: CSS.supports('will-change', 'transform'),
    transform3d: CSS.supports('transform', 'translate3d(0, 0, 0)'),
    animations: CSS.supports('animation', 'test 1s linear'),
    transitions: CSS.supports('transition', 'all 1s ease'),
    gridLayout: CSS.supports('display', 'grid'),
    flexbox: CSS.supports('display', 'flex'),
  };
}

/**
 * Test JavaScript API support
 */
function testJavaScriptSupport(): FeatureSupport['javascript'] {
  return {
    requestAnimationFrame: typeof requestAnimationFrame !== 'undefined',
    performanceMemory: 'memory' in performance,
    intersectionObserver: typeof IntersectionObserver !== 'undefined',
    resizeObserver: typeof ResizeObserver !== 'undefined',
    matchMedia: typeof window.matchMedia !== 'undefined',
    getComputedStyle: typeof window.getComputedStyle !== 'undefined',
    webWorkers: typeof Worker !== 'undefined',
    serviceWorker: 'serviceWorker' in navigator,
  };
}

/**
 * Test media query support
 */
function testMediaSupport(): FeatureSupport['media'] {
  return {
    prefersReducedMotion: window.matchMedia('(prefers-reduced-motion)').media !== 'not all',
    prefersColorScheme: window.matchMedia('(prefers-color-scheme)').media !== 'not all',
    orientation: window.matchMedia('(orientation)').media !== 'not all',
    hover: window.matchMedia('(hover)').media !== 'not all',
  };
}

/**
 * Test performance API support
 */
function testPerformanceSupport(): FeatureSupport['performance'] {
  return {
    performanceAPI: typeof performance !== 'undefined',
    performanceObserver: typeof PerformanceObserver !== 'undefined',
    performanceTiming: 'timing' in performance,
    highResTime: typeof performance.now !== 'undefined',
  };
}

/**
 * Run comprehensive browser compatibility test
 */
export function runCompatibilityTest(): BrowserCompatibility {
  const browser = detectBrowser();
  const webglInfo = testWebGLSupport();
  
  const features: FeatureSupport = {
    webgl: webglInfo.webgl,
    webgl2: webglInfo.webgl2,
    webglExtensions: webglInfo.extensions,
    css: testCSSSupport(),
    javascript: testJavaScriptSupport(),
    media: testMediaSupport(),
    performance: testPerformanceSupport(),
  };
  
  const { score, warnings, recommendations, fallbacksNeeded } = analyzeCompatibility(browser, features);
  
  return {
    browser,
    features,
    score,
    warnings,
    recommendations,
    fallbacksNeeded,
  };
}

/**
 * Analyze compatibility and generate recommendations
 */
function analyzeCompatibility(
  browser: BrowserInfo,
  features: FeatureSupport
): {
  score: number;
  warnings: string[];
  recommendations: string[];
  fallbacksNeeded: string[];
} {
  const warnings: string[] = [];
  const recommendations: string[] = [];
  const fallbacksNeeded: string[] = [];
  let score = 100;
  
  // Browser version checks
  if (!browser.isSupported) {
    warnings.push(`${browser.name} ${browser.version} is below minimum supported version`);
    score -= 20;
    recommendations.push('Please update to a newer browser version');
  }
  
  // WebGL checks
  if (!features.webgl) {
    warnings.push('WebGL is not supported');
    score -= 30;
    fallbacksNeeded.push('CSS-based animations');
    recommendations.push('Enable hardware acceleration in browser settings');
  } else if (!features.webgl2) {
    warnings.push('WebGL 2.0 is not supported');
    score -= 10;
  }
  
  // Critical WebGL extensions
  const criticalExtensions = ['OES_vertex_array_object', 'WEBGL_lose_context'];
  criticalExtensions.forEach(ext => {
    if (!features.webglExtensions.includes(ext)) {
      warnings.push(`Missing WebGL extension: ${ext}`);
      score -= 5;
    }
  });
  
  // CSS feature checks
  if (!features.css.backdropFilter) {
    warnings.push('backdrop-filter is not supported');
    score -= 10;
    fallbacksNeeded.push('Alternative blur effects');
    if (browser.name === 'Safari') {
      recommendations.push('Consider using -webkit-backdrop-filter prefix');
    }
  }
  
  if (!features.css.customProperties) {
    warnings.push('CSS custom properties are not supported');
    score -= 15;
    fallbacksNeeded.push('Static CSS values');
  }
  
  if (!features.css.willChange) {
    warnings.push('will-change property is not supported');
    score -= 5;
    recommendations.push('Performance may be suboptimal');
  }
  
  // JavaScript API checks
  if (!features.javascript.requestAnimationFrame) {
    warnings.push('requestAnimationFrame is not supported');
    score -= 20;
    fallbacksNeeded.push('setTimeout-based animations');
  }
  
  if (!features.javascript.intersectionObserver) {
    warnings.push('IntersectionObserver is not supported');
    score -= 10;
    fallbacksNeeded.push('Scroll event-based visibility detection');
  }
  
  if (!features.javascript.performanceMemory) {
    if (browser.name !== 'Chrome') {
      // This is expected for non-Chrome browsers
      recommendations.push('Memory usage monitoring not available');
    }
  }
  
  // Media query checks
  if (!features.media.prefersReducedMotion) {
    warnings.push('prefers-reduced-motion is not supported');
    score -= 10;
    fallbacksNeeded.push('Manual motion preferences');
  }
  
  // Performance API checks
  if (!features.performance.performanceAPI) {
    warnings.push('Performance API is not supported');
    score -= 15;
    fallbacksNeeded.push('Basic timing measurements');
  }
  
  // Browser-specific recommendations
  if (browser.name === 'Safari' && browser.isMobile) {
    recommendations.push('Consider reducing animation complexity on iOS Safari');
    if (browser.majorVersion < 14) {
      warnings.push('iOS Safari version may have WebGL limitations');
      score -= 5;
    }
  }
  
  if (browser.name === 'Firefox') {
    recommendations.push('Firefox may have different WebGL performance characteristics');
  }
  
  if (browser.isMobile) {
    recommendations.push('Enable battery-aware animation management');
    recommendations.push('Consider reduced particle counts for mobile devices');
  }
  
  return {
    score: Math.max(0, score),
    warnings,
    recommendations,
    fallbacksNeeded,
  };
}

/**
 * Generate browser compatibility report
 */
export function generateCompatibilityReport(compatibility: BrowserCompatibility): string {
  const { browser, features, score, warnings, recommendations, fallbacksNeeded } = compatibility;
  
  let report = `# Browser Compatibility Report\n\n`;
  
  // Browser Information
  report += `## Browser Information\n`;
  report += `- **Name**: ${browser.name}\n`;
  report += `- **Version**: ${browser.version}\n`;
  report += `- **Engine**: ${browser.engine}\n`;
  report += `- **Platform**: ${browser.platform}\n`;
  report += `- **Mobile**: ${browser.isMobile ? 'Yes' : 'No'}\n`;
  report += `- **Supported**: ${browser.isSupported ? 'Yes' : 'No'}\n\n`;
  
  // Compatibility Score
  report += `## Compatibility Score: ${score}/100\n\n`;
  
  if (score >= 90) {
    report += `✅ **Excellent** - Full feature support\n\n`;
  } else if (score >= 70) {
    report += `⚠️ **Good** - Minor limitations or missing features\n\n`;
  } else if (score >= 50) {
    report += `🔶 **Fair** - Some important features missing\n\n`;
  } else {
    report += `❌ **Poor** - Major compatibility issues\n\n`;
  }
  
  // Feature Support
  report += `## Feature Support\n\n`;
  
  // WebGL
  report += `### WebGL\n`;
  report += `- WebGL 1.0: ${features.webgl ? '✅' : '❌'}\n`;
  report += `- WebGL 2.0: ${features.webgl2 ? '✅' : '❌'}\n`;
  report += `- Extensions: ${features.webglExtensions.length} available\n\n`;
  
  // CSS
  report += `### CSS Features\n`;
  report += `- Custom Properties: ${features.css.customProperties ? '✅' : '❌'}\n`;
  report += `- Backdrop Filter: ${features.css.backdropFilter ? '✅' : '❌'}\n`;
  report += `- Will Change: ${features.css.willChange ? '✅' : '❌'}\n`;
  report += `- Transform 3D: ${features.css.transform3d ? '✅' : '❌'}\n`;
  report += `- Animations: ${features.css.animations ? '✅' : '❌'}\n`;
  report += `- Transitions: ${features.css.transitions ? '✅' : '❌'}\n\n`;
  
  // JavaScript
  report += `### JavaScript APIs\n`;
  report += `- requestAnimationFrame: ${features.javascript.requestAnimationFrame ? '✅' : '❌'}\n`;
  report += `- IntersectionObserver: ${features.javascript.intersectionObserver ? '✅' : '❌'}\n`;
  report += `- ResizeObserver: ${features.javascript.resizeObserver ? '✅' : '❌'}\n`;
  report += `- Performance Memory: ${features.javascript.performanceMemory ? '✅' : '❌'}\n\n`;
  
  // Media Queries
  report += `### Media Queries\n`;
  report += `- prefers-reduced-motion: ${features.media.prefersReducedMotion ? '✅' : '❌'}\n`;
  report += `- prefers-color-scheme: ${features.media.prefersColorScheme ? '✅' : '❌'}\n\n`;
  
  // Warnings
  if (warnings.length > 0) {
    report += `## ⚠️ Warnings\n\n`;
    warnings.forEach(warning => {
      report += `- ${warning}\n`;
    });
    report += `\n`;
  }
  
  // Recommendations
  if (recommendations.length > 0) {
    report += `## 💡 Recommendations\n\n`;
    recommendations.forEach(recommendation => {
      report += `- ${recommendation}\n`;
    });
    report += `\n`;
  }
  
  // Fallbacks Needed
  if (fallbacksNeeded.length > 0) {
    report += `## 🔄 Fallbacks Needed\n\n`;
    fallbacksNeeded.forEach(fallback => {
      report += `- ${fallback}\n`;
    });
    report += `\n`;
  }
  
  return report;
}

/**
 * Test animation performance across browsers
 */
export async function testAnimationPerformance(): Promise<{
  averageFPS: number;
  frameDrops: number;
  memoryUsage: number;
  testDuration: number;
}> {
  return new Promise((resolve) => {
    const startTime = performance.now();
    let frameCount = 0;
    let frameDrops = 0;
    let lastFrameTime = startTime;
    const testDuration = 5000; // 5 seconds
    
    function measureFrame(currentTime: number) {
      frameCount++;
      
      const frameDelta = currentTime - lastFrameTime;
      if (frameDelta > 20) { // More than 20ms = frame drop (< 50fps)
        frameDrops++;
      }
      
      lastFrameTime = currentTime;
      
      if (currentTime - startTime < testDuration) {
        requestAnimationFrame(measureFrame);
      } else {
        const averageFPS = (frameCount / testDuration) * 1000;
        const memoryUsage = 'memory' in performance 
          ? (performance as any).memory.usedJSHeapSize / (1024 * 1024)
          : 0;
        
        resolve({
          averageFPS,
          frameDrops,
          memoryUsage,
          testDuration,
        });
      }
    }
    
    requestAnimationFrame(measureFrame);
  });
}

export default {
  detectBrowser,
  runCompatibilityTest,
  generateCompatibilityReport,
  testAnimationPerformance,
};