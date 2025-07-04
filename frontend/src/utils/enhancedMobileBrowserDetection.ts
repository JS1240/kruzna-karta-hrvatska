/**
 * Enhanced Mobile Browser Detection
 * 
 * Specialized browser detection for mobile devices with focus on
 * iOS Safari 13+ and Chrome Mobile 80+ precise version detection
 */

export interface MobileBrowserInfo {
  name: string;
  version: string;
  majorVersion: number;
  minorVersion: number;
  patchVersion: number;
  engine: string;
  platform: 'ios' | 'android' | 'unknown';
  deviceType: 'phone' | 'tablet' | 'desktop' | 'unknown';
  osVersion?: string;
  isSupported: boolean;
  supportDetails: {
    meetsMinimumVersion: boolean;
    hasWebGLSupport: boolean;
    hasTouchSupport: boolean;
    hasModernCSS: boolean;
  };
}

export interface IOSBrowserInfo extends MobileBrowserInfo {
  platform: 'ios';
  iosVersion: string;
  isSafari: boolean;
  isWKWebView: boolean;
  isStandalone: boolean;
  deviceModel?: string;
}

export interface AndroidBrowserInfo extends MobileBrowserInfo {
  platform: 'android';
  androidVersion: string;
  isChrome: boolean;
  isWebView: boolean;
  brandInfo?: string[];
}

/**
 * Enhanced mobile browser detection with precise version identification
 */
export function detectMobileBrowser(): MobileBrowserInfo {
  const userAgent = navigator.userAgent;
  const platform = detectPlatform(userAgent);
  
  if (platform === 'ios') {
    return detectIOSBrowser(userAgent);
  } else if (platform === 'android') {
    return detectAndroidBrowser(userAgent);
  }
  
  // Fallback for unknown mobile platforms
  return createFallbackBrowserInfo(userAgent);
}

/**
 * Detect platform from user agent
 */
function detectPlatform(userAgent: string): 'ios' | 'android' | 'unknown' {
  if (/iPhone|iPad|iPod/.test(userAgent)) return 'ios';
  if (/Android/.test(userAgent)) return 'android';
  return 'unknown';
}

/**
 * Detect iOS browser with enhanced Safari detection
 */
function detectIOSBrowser(userAgent: string): IOSBrowserInfo {
  const iosVersionMatch = userAgent.match(/OS (\d+)_(\d+)(?:_(\d+))?/);
  const iosVersion = iosVersionMatch 
    ? `${iosVersionMatch[1]}.${iosVersionMatch[2]}${iosVersionMatch[3] ? '.' + iosVersionMatch[3] : ''}`
    : 'unknown';
  
  const majorIOSVersion = iosVersionMatch ? parseInt(iosVersionMatch[1]) : 0;
  
  // Safari version detection on iOS
  let browserVersion = '13.0.0'; // Default fallback
  let browserMajorVersion = 13;
  let browserMinorVersion = 0;
  let browserPatchVersion = 0;
  
  // iOS Safari version mapping (approximate)
  // iOS 13.x typically runs Safari 13.x
  // iOS 14.x typically runs Safari 14.x, etc.
  if (iosVersionMatch) {
    browserMajorVersion = parseInt(iosVersionMatch[1]);
    browserMinorVersion = parseInt(iosVersionMatch[2]) || 0;
    browserPatchVersion = parseInt(iosVersionMatch[3]) || 0;
    browserVersion = `${browserMajorVersion}.${browserMinorVersion}.${browserPatchVersion}`;
  }
  
  // Check if it's Safari or WKWebView
  const isSafari = !userAgent.includes('CriOS') && 
                   !userAgent.includes('FxiOS') && 
                   !userAgent.includes('EdgiOS');
  
  const isWKWebView = userAgent.includes('AppleWebKit') && 
                      !userAgent.includes('Safari') && 
                      !userAgent.includes('CriOS');
  
  const isStandalone = (navigator as any).standalone === true;
  
  // Device type detection
  const deviceType = userAgent.includes('iPad') ? 'tablet' : 'phone';
  
  // Device model detection (simplified)
  let deviceModel: string | undefined;
  if (userAgent.includes('iPhone')) {
    deviceModel = 'iPhone';
  } else if (userAgent.includes('iPad')) {
    deviceModel = 'iPad';
  } else if (userAgent.includes('iPod')) {
    deviceModel = 'iPod';
  }
  
  const isSupported = checkIOSSupport(browserMajorVersion);
  
  return {
    name: isSafari ? 'Safari' : 'Safari (WKWebView)',
    version: browserVersion,
    majorVersion: browserMajorVersion,
    minorVersion: browserMinorVersion,
    patchVersion: browserPatchVersion,
    engine: 'WebKit',
    platform: 'ios',
    deviceType,
    osVersion: iosVersion,
    iosVersion,
    isSafari,
    isWKWebView,
    isStandalone,
    deviceModel,
    isSupported,
    supportDetails: {
      meetsMinimumVersion: browserMajorVersion >= 13,
      hasWebGLSupport: testWebGLSupport(),
      hasTouchSupport: testTouchSupport(),
      hasModernCSS: testModernCSSSupport(),
    },
  };
}

/**
 * Detect Android browser with Chrome Mobile detection
 */
function detectAndroidBrowser(userAgent: string): AndroidBrowserInfo {
  const androidVersionMatch = userAgent.match(/Android (\d+)\.(\d+)(?:\.(\d+))?/);
  const androidVersion = androidVersionMatch 
    ? `${androidVersionMatch[1]}.${androidVersionMatch[2]}${androidVersionMatch[3] ? '.' + androidVersionMatch[3] : ''}`
    : 'unknown';
  
  let browserName = 'Android Browser';
  let browserVersion = '80.0.0'; // Default fallback
  let browserMajorVersion = 80;
  let browserMinorVersion = 0;
  let browserPatchVersion = 0;
  let engine = 'WebKit';
  let isChrome = false;
  let isWebView = false;
  
  // Chrome Mobile detection
  const chromeMatch = userAgent.match(/Chrome\/(\d+)\.(\d+)\.(\d+)\.(\d+)/);
  if (chromeMatch) {
    browserName = 'Chrome';
    browserMajorVersion = parseInt(chromeMatch[1]);
    browserMinorVersion = parseInt(chromeMatch[2]);
    browserPatchVersion = parseInt(chromeMatch[3]);
    browserVersion = `${browserMajorVersion}.${browserMinorVersion}.${browserPatchVersion}`;
    engine = 'Blink';
    isChrome = true;
    
    // Detect if it's a WebView
    isWebView = userAgent.includes('wv') || 
                userAgent.includes('Version/') && userAgent.includes('Chrome');
  }
  
  // Firefox Mobile detection
  else if (userAgent.includes('Firefox')) {
    const firefoxMatch = userAgent.match(/Firefox\/(\d+)\.(\d+)/);
    if (firefoxMatch) {
      browserName = 'Firefox';
      browserMajorVersion = parseInt(firefoxMatch[1]);
      browserMinorVersion = parseInt(firefoxMatch[2]);
      browserVersion = `${browserMajorVersion}.${browserMinorVersion}.0`;
      engine = 'Gecko';
    }
  }
  
  // Samsung Internet detection
  else if (userAgent.includes('SamsungBrowser')) {
    const samsungMatch = userAgent.match(/SamsungBrowser\/(\d+)\.(\d+)/);
    if (samsungMatch) {
      browserName = 'Samsung Internet';
      browserMajorVersion = parseInt(samsungMatch[1]);
      browserMinorVersion = parseInt(samsungMatch[2]);
      browserVersion = `${browserMajorVersion}.${browserMinorVersion}.0`;
      engine = 'Blink';
    }
  }
  
  // Device type detection
  const deviceType = userAgent.includes('Mobile') ? 'phone' : 'tablet';
  
  // Brand info from User-Agent Client Hints (if available)
  let brandInfo: string[] | undefined;
  try {
    const navigatorUA = (navigator as any).userAgentData;
    if (navigatorUA?.brands) {
      brandInfo = navigatorUA.brands.map((brand: any) => `${brand.brand} ${brand.version}`);
    }
  } catch {}
  
  const isSupported = checkAndroidChromeSupport(browserMajorVersion, isChrome);
  
  return {
    name: browserName,
    version: browserVersion,
    majorVersion: browserMajorVersion,
    minorVersion: browserMinorVersion,
    patchVersion: browserPatchVersion,
    engine,
    platform: 'android',
    deviceType,
    osVersion: androidVersion,
    androidVersion,
    isChrome,
    isWebView,
    brandInfo,
    isSupported,
    supportDetails: {
      meetsMinimumVersion: isChrome ? browserMajorVersion >= 80 : browserMajorVersion >= 75,
      hasWebGLSupport: testWebGLSupport(),
      hasTouchSupport: testTouchSupport(),
      hasModernCSS: testModernCSSSupport(),
    },
  };
}

/**
 * Create fallback browser info for unknown platforms
 */
function createFallbackBrowserInfo(userAgent: string): MobileBrowserInfo {
  // Try to extract basic browser info
  let browserName = 'Unknown';
  let browserVersion = '0.0.0';
  let browserMajorVersion = 0;
  let engine = 'Unknown';
  
  // Check for common mobile browsers
  if (userAgent.includes('Chrome')) {
    const chromeMatch = userAgent.match(/Chrome\/(\d+)\.(\d+)\.(\d+)/);
    if (chromeMatch) {
      browserName = 'Chrome';
      browserMajorVersion = parseInt(chromeMatch[1]);
      browserVersion = `${chromeMatch[1]}.${chromeMatch[2]}.${chromeMatch[3]}`;
      engine = 'Blink';
    }
  } else if (userAgent.includes('Firefox')) {
    const firefoxMatch = userAgent.match(/Firefox\/(\d+)\.(\d+)/);
    if (firefoxMatch) {
      browserName = 'Firefox';
      browserMajorVersion = parseInt(firefoxMatch[1]);
      browserVersion = `${firefoxMatch[1]}.${firefoxMatch[2]}.0`;
      engine = 'Gecko';
    }
  } else if (userAgent.includes('Safari')) {
    browserName = 'Safari';
    engine = 'WebKit';
    // Try to extract version
    const versionMatch = userAgent.match(/Version\/(\d+)\.(\d+)/);
    if (versionMatch) {
      browserMajorVersion = parseInt(versionMatch[1]);
      browserVersion = `${versionMatch[1]}.${versionMatch[2]}.0`;
    }
  }
  
  const deviceType = userAgent.includes('Mobile') ? 'phone' : 
                     userAgent.includes('Tablet') ? 'tablet' : 'unknown';
  
  return {
    name: browserName,
    version: browserVersion,
    majorVersion: browserMajorVersion,
    minorVersion: 0,
    patchVersion: 0,
    engine,
    platform: 'unknown',
    deviceType,
    isSupported: false,
    supportDetails: {
      meetsMinimumVersion: false,
      hasWebGLSupport: testWebGLSupport(),
      hasTouchSupport: testTouchSupport(),
      hasModernCSS: testModernCSSSupport(),
    },
  };
}

/**
 * Check iOS Safari support
 */
function checkIOSSupport(majorVersion: number): boolean {
  return majorVersion >= 13;
}

/**
 * Check Android Chrome support
 */
function checkAndroidChromeSupport(majorVersion: number, isChrome: boolean): boolean {
  if (isChrome) {
    return majorVersion >= 80;
  }
  // For other Android browsers, use a lower threshold
  return majorVersion >= 75;
}

/**
 * Test WebGL support
 */
function testWebGLSupport(): boolean {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    return !!gl;
  } catch {
    return false;
  }
}

/**
 * Test touch support
 */
function testTouchSupport(): boolean {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

/**
 * Test modern CSS support
 */
function testModernCSSSupport(): boolean {
  try {
    return CSS.supports('backdrop-filter', 'blur(10px)') ||
           CSS.supports('-webkit-backdrop-filter', 'blur(10px)');
  } catch {
    return false;
  }
}

/**
 * Get detailed browser capabilities for mobile devices
 */
export function getMobileBrowserCapabilities(): {
  browser: MobileBrowserInfo;
  features: {
    webgl: boolean;
    webgl2: boolean;
    cssGrid: boolean;
    cssFlexbox: boolean;
    cssCustomProperties: boolean;
    backdropFilter: boolean;
    intersectionObserver: boolean;
    resizeObserver: boolean;
    touchEvents: boolean;
    orientationAPI: boolean;
    deviceMemoryAPI: boolean;
    networkInformationAPI: boolean;
    batteryAPI: boolean;
    visualViewportAPI: boolean;
    performanceObserver: boolean;
  };
  performance: {
    deviceMemory: number;
    hardwareConcurrency: number;
    connectionType: string;
    maxTouchPoints: number;
  };
} {
  const browser = detectMobileBrowser();
  
  // Test features
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl');
  const gl2 = canvas.getContext('webgl2');
  
  const features = {
    webgl: !!gl,
    webgl2: !!gl2,
    cssGrid: CSS.supports('display', 'grid'),
    cssFlexbox: CSS.supports('display', 'flex'),
    cssCustomProperties: CSS.supports('(--foo: red)'),
    backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)') || 
                   CSS.supports('-webkit-backdrop-filter', 'blur(10px)'),
    intersectionObserver: typeof IntersectionObserver !== 'undefined',
    resizeObserver: typeof ResizeObserver !== 'undefined',
    touchEvents: 'ontouchstart' in window,
    orientationAPI: 'orientation' in screen || 'orientation' in window,
    deviceMemoryAPI: 'deviceMemory' in navigator,
    networkInformationAPI: 'connection' in navigator,
    batteryAPI: 'getBattery' in navigator,
    visualViewportAPI: 'visualViewport' in window,
    performanceObserver: typeof PerformanceObserver !== 'undefined',
  };
  
  // Get performance info
  const connection = (navigator as any).connection || 
                    (navigator as any).mozConnection || 
                    (navigator as any).webkitConnection;
  
  const performance = {
    deviceMemory: (navigator as any).deviceMemory || 4,
    hardwareConcurrency: navigator.hardwareConcurrency || 2,
    connectionType: connection?.effectiveType || 'unknown',
    maxTouchPoints: navigator.maxTouchPoints || 0,
  };
  
  return {
    browser,
    features,
    performance,
  };
}

/**
 * Check if current browser meets mobile compatibility requirements
 */
export function checkMobileCompatibility(): {
  isCompatible: boolean;
  issues: string[];
  recommendations: string[];
  score: number;
} {
  const browser = detectMobileBrowser();
  const capabilities = getMobileBrowserCapabilities();
  
  const issues: string[] = [];
  const recommendations: string[] = [];
  let score = 100;
  
  // Check minimum browser version
  if (!browser.isSupported) {
    issues.push(`${browser.name} ${browser.version} is below minimum supported version`);
    score -= 40;
    
    if (browser.platform === 'ios') {
      recommendations.push('Update to iOS 13 or later for Safari 13+ support');
    } else if (browser.platform === 'android' && browser.name === 'Chrome') {
      recommendations.push('Update Chrome to version 80 or later');
    }
  }
  
  // Check WebGL support
  if (!capabilities.features.webgl) {
    issues.push('WebGL is not supported');
    score -= 30;
    recommendations.push('Enable hardware acceleration in browser settings');
  }
  
  // Check touch support
  if (!capabilities.features.touchEvents) {
    issues.push('Touch events are not supported');
    score -= 20;
  }
  
  // Check modern CSS features
  if (!capabilities.features.cssCustomProperties) {
    issues.push('CSS Custom Properties are not supported');
    score -= 15;
  }
  
  if (!capabilities.features.backdropFilter) {
    issues.push('CSS backdrop-filter is not supported');
    score -= 10;
    if (browser.platform === 'ios') {
      recommendations.push('Some blur effects may not work on older iOS versions');
    }
  }
  
  // Check device capabilities
  if (capabilities.performance.deviceMemory < 2) {
    issues.push('Low device memory detected');
    score -= 10;
    recommendations.push('Animations will be simplified for better performance');
  }
  
  const isCompatible = score >= 70;
  
  return {
    isCompatible,
    issues,
    recommendations,
    score: Math.max(0, score),
  };
}

export default {
  detectMobileBrowser,
  getMobileBrowserCapabilities,
  checkMobileCompatibility,
};