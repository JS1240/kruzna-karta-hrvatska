/**
 * Enhanced Device Detection System for Low-Performance Device Fallbacks (T5.2)
 * 
 * Provides comprehensive device capability detection including WebGL support,
 * hardware acceleration, performance scoring, and fallback recommendations.
 * 
 * Features:
 * - WebGL support detection with hardware vs software rendering identification
 * - Device performance scoring based on multiple factors
 * - Battery level and connection quality detection
 * - Smart fallback recommendations
 * - Caching for performance optimization
 */

export type WebGLSupport = 'hardware' | 'software' | 'none';
export type ConnectionQuality = 'fast' | 'medium' | 'slow';
export type DeviceClass = 'high-end' | 'mid-range' | 'low-end' | 'very-low-end';
export type MobileBrowser = 'safari' | 'chrome' | 'firefox' | 'edge' | 'samsung' | 'opera' | 'unknown';
export type MobileOS = 'ios' | 'android' | 'unknown';
export type GraphicsAPI = 'metal' | 'opengl-es' | 'vulkan' | 'unknown';

export interface DeviceCapabilities {
  /** WebGL support level */
  webglSupport: WebGLSupport;
  /** Overall performance score (0-100) */
  performanceScore: number;
  /** Estimated available memory in MB */
  memoryEstimate: number;
  /** Estimated CPU cores */
  cores: number;
  /** Is mobile device */
  isMobile: boolean;
  /** Is tablet device */
  isTablet: boolean;
  /** Battery level (0-1) if available */
  batteryLevel?: number;
  /** Is device charging */
  isCharging?: boolean;
  /** Network connection quality */
  connectionQuality: ConnectionQuality;
  /** Device classification */
  deviceClass: DeviceClass;
  /** Screen pixel density */
  pixelRatio: number;
  /** Available screen size */
  screenSize: {
    width: number;
    height: number;
  };
  /** Hardware concurrency (logical processors) */
  hardwareConcurrency: number;
  /** WebGL renderer information */
  renderer?: string;
  /** WebGL vendor information */
  vendor?: string;
  /** Supports hardware acceleration */
  hardwareAcceleration: boolean;
  /** Detection timestamp for caching */
  detectionTime: number;
  /** Mobile-specific capabilities (T5.3) */
  mobileCapabilities?: {
    browser: MobileBrowser;
    os: MobileOS;
    osVersion: string;
    graphicsAPI: GraphicsAPI;
    gpuMemoryMB?: number;
    maxTextureSize?: number;
    supportsWebGL2: boolean;
    supportsHalfFloat: boolean;
    maxVertexTextureImageUnits?: number;
    maxFragmentTextureImageUnits?: number;
    touchSupport: boolean;
    orientationSupport: boolean;
    dataSaverMode?: boolean;
    reducedDataMode?: boolean;
  };
}

export interface FallbackRecommendation {
  /** Recommended animation mode */
  mode: 'webgl' | 'css' | 'static' | 'none';
  /** Recommended CSS animation type if using CSS mode */
  cssAnimationType: 'particles' | 'gradients' | 'minimal';
  /** Recommended static pattern if using static mode */
  staticPatternType: 'geometric' | 'brand' | 'solid';
  /** Should enable smooth transitions */
  enableTransitions: boolean;
  /** Recommended performance settings */
  performanceSettings: {
    particleCount: number;
    maxDistance: number;
    spacing: number;
    opacity: number;
    updateFrequency: number;
  };
  /** Reason for recommendation */
  reason: string;
}

/**
 * Enhanced device detection class
 */
export class DeviceDetector {
  private static instance: DeviceDetector | null = null;
  private cachedCapabilities: DeviceCapabilities | null = null;
  private cacheExpiration = 5 * 60 * 1000; // 5 minutes
  
  private constructor() {}
  
  /**
   * Get singleton instance
   */
  static getInstance(): DeviceDetector {
    if (!DeviceDetector.instance) {
      DeviceDetector.instance = new DeviceDetector();
    }
    return DeviceDetector.instance;
  }
  
  /**
   * Get device capabilities with caching
   */
  async getDeviceCapabilities(forceRefresh = false): Promise<DeviceCapabilities> {
    // Return cached result if valid and not forcing refresh
    if (!forceRefresh && this.cachedCapabilities && 
        Date.now() - this.cachedCapabilities.detectionTime < this.cacheExpiration) {
      return this.cachedCapabilities;
    }
    
    // Detect capabilities
    this.cachedCapabilities = await this.detectCapabilities();
    return this.cachedCapabilities;
  }
  
  /**
   * Get fallback recommendation based on device capabilities
   */
  async getFallbackRecommendation(
    capabilities?: DeviceCapabilities,
    userPreferences?: {
      preferPerformance?: boolean;
      preferQuality?: boolean;
      reducedMotion?: boolean;
    }
  ): Promise<FallbackRecommendation> {
    const caps = capabilities || await this.getDeviceCapabilities();
    const prefs = userPreferences || {};
    
    // Check for reduced motion preference
    if (prefs.reducedMotion || this.prefersReducedMotion()) {
      return {
        mode: 'static',
        cssAnimationType: 'minimal',
        staticPatternType: 'solid',
        enableTransitions: false,
        performanceSettings: {
          particleCount: 0,
          maxDistance: 0,
          spacing: 0,
          opacity: 0.1,
          updateFrequency: 0
        },
        reason: 'User prefers reduced motion'
      };
    }
    
    // High-end devices - full WebGL with hardware acceleration
    if (caps.deviceClass === 'high-end' && caps.webglSupport === 'hardware' && caps.hardwareAcceleration) {
      return {
        mode: 'webgl',
        cssAnimationType: 'particles',
        staticPatternType: 'geometric',
        enableTransitions: true,
        performanceSettings: {
          particleCount: caps.isMobile ? 12 : 16,
          maxDistance: caps.isMobile ? 20 : 25,
          spacing: caps.isMobile ? 18 : 15,
          opacity: 0.4,
          updateFrequency: 60
        },
        reason: 'High-end device with hardware WebGL support'
      };
    }
    
    // Mid-range devices - reduced WebGL or CSS fallback
    if (caps.deviceClass === 'mid-range') {
      if (caps.webglSupport === 'hardware' && caps.performanceScore > 60) {
        return {
          mode: 'webgl',
          cssAnimationType: 'particles',
          staticPatternType: 'geometric',
          enableTransitions: true,
          performanceSettings: {
            particleCount: caps.isMobile ? 8 : 12,
            maxDistance: caps.isMobile ? 15 : 20,
            spacing: caps.isMobile ? 20 : 18,
            opacity: 0.3,
            updateFrequency: caps.isMobile ? 30 : 60
          },
          reason: 'Mid-range device with good WebGL support'
        };
      } else {
        return {
          mode: 'css',
          cssAnimationType: 'particles',
          staticPatternType: 'geometric',
          enableTransitions: true,
          performanceSettings: {
            particleCount: 6,
            maxDistance: 12,
            spacing: 25,
            opacity: 0.25,
            updateFrequency: 30
          },
          reason: 'Mid-range device, using CSS animations for better performance'
        };
      }
    }
    
    // Low-end devices - minimal CSS or static
    if (caps.deviceClass === 'low-end') {
      if (caps.performanceScore > 30) {
        return {
          mode: 'css',
          cssAnimationType: 'gradients',
          staticPatternType: 'brand',
          enableTransitions: false,
          performanceSettings: {
            particleCount: 4,
            maxDistance: 8,
            spacing: 30,
            opacity: 0.2,
            updateFrequency: 15
          },
          reason: 'Low-end device, using minimal CSS animations'
        };
      } else {
        return {
          mode: 'static',
          cssAnimationType: 'minimal',
          staticPatternType: 'brand',
          enableTransitions: false,
          performanceSettings: {
            particleCount: 0,
            maxDistance: 0,
            spacing: 0,
            opacity: 0.15,
            updateFrequency: 0
          },
          reason: 'Low-end device, using static background'
        };
      }
    }
    
    // Very low-end devices - static or none
    return {
      mode: 'static',
      cssAnimationType: 'minimal',
      staticPatternType: 'solid',
      enableTransitions: false,
      performanceSettings: {
        particleCount: 0,
        maxDistance: 0,
        spacing: 0,
        opacity: 0.1,
        updateFrequency: 0
      },
      reason: 'Very low-end device, minimal visual effects'
    };
  }
  
  /**
   * Detect comprehensive device capabilities
   */
  private async detectCapabilities(): Promise<DeviceCapabilities> {
    const webglInfo = this.detectWebGLSupport();
    const deviceInfo = this.detectDeviceInfo();
    const performanceScore = this.calculatePerformanceScore(webglInfo, deviceInfo);
    const deviceClass = this.classifyDevice(performanceScore, deviceInfo);
    
    // Try to get battery information
    let batteryLevel: number | undefined;
    let isCharging: boolean | undefined;
    
    try {
      if ('getBattery' in navigator) {
        const battery = await (navigator as any).getBattery();
        batteryLevel = battery.level;
        isCharging = battery.charging;
      }
    } catch (error) {
      // Battery API not available or blocked
    }
    
    // Detect mobile-specific capabilities (T5.3)
    const mobileCapabilities = deviceInfo.isMobile ? this.detectMobileCapabilities(webglInfo) : undefined;

    return {
      webglSupport: webglInfo.support,
      performanceScore,
      memoryEstimate: this.estimateMemory(),
      cores: navigator.hardwareConcurrency || 4,
      isMobile: deviceInfo.isMobile,
      isTablet: deviceInfo.isTablet,
      batteryLevel,
      isCharging,
      connectionQuality: this.detectConnectionQuality(),
      deviceClass,
      pixelRatio: window.devicePixelRatio || 1,
      screenSize: {
        width: window.screen.width,
        height: window.screen.height
      },
      hardwareConcurrency: navigator.hardwareConcurrency || 4,
      renderer: webglInfo.renderer,
      vendor: webglInfo.vendor,
      hardwareAcceleration: webglInfo.hardwareAcceleration,
      detectionTime: Date.now(),
      mobileCapabilities
    };
  }
  
  /**
   * Detect WebGL support and quality
   */
  private detectWebGLSupport(): {
    support: WebGLSupport;
    renderer?: string;
    vendor?: string;
    hardwareAcceleration: boolean;
  } {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (!gl) {
        return {
          support: 'none',
          hardwareAcceleration: false
        };
      }
      
      // Get renderer info
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      let renderer: string | undefined;
      let vendor: string | undefined;
      
      if (debugInfo) {
        renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      }
      
      // Detect software rendering
      const isSoftwareRenderer = this.isSoftwareRenderer(renderer, vendor);\n      const hardwareAcceleration = !isSoftwareRenderer;\n      \n      return {\n        support: hardwareAcceleration ? 'hardware' : 'software',\n        renderer,\n        vendor,\n        hardwareAcceleration\n      };\n    } catch (error) {\n      return {\n        support: 'none',\n        hardwareAcceleration: false\n      };\n    }\n  }\n  \n  /**\n   * Detect if using software renderer\n   */\n  private isSoftwareRenderer(renderer?: string, vendor?: string): boolean {\n    if (!renderer && !vendor) return false;\n    \n    const softwareIndicators = [\n      'swiftshader',\n      'llvmpipe',\n      'software',\n      'mesa',\n      'microsoft basic render driver',\n      'google inc.',\n      'chromium'\n    ];\n    \n    const rendererLower = (renderer || '').toLowerCase();\n    const vendorLower = (vendor || '').toLowerCase();\n    \n    return softwareIndicators.some(indicator => \n      rendererLower.includes(indicator) || vendorLower.includes(indicator)\n    );\n  }\n  \n  /**\n   * Detect basic device information\n   */\n  private detectDeviceInfo(): {\n    isMobile: boolean;\n    isTablet: boolean;\n    userAgent: string;\n  } {\n    const userAgent = navigator.userAgent;\n    \n    // Mobile detection\n    const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;\n    const isMobile = mobileRegex.test(userAgent);\n    \n    // Tablet detection (more specific)\n    const tabletRegex = /iPad|Android(?=.*\\bMobile\\b)(?!.*\\bPhone\\b)|Tablet/i;\n    const isTablet = tabletRegex.test(userAgent) || \n      (isMobile && Math.min(screen.width, screen.height) >= 768);\n    \n    return {\n      isMobile,\n      isTablet,\n      userAgent\n    };\n  }\n  \n  /**\n   * Calculate overall performance score\n   */\n  private calculatePerformanceScore(\n    webglInfo: { support: WebGLSupport; hardwareAcceleration: boolean },\n    deviceInfo: { isMobile: boolean; isTablet: boolean }\n  ): number {\n    let score = 50; // Base score\n    \n    // WebGL support scoring\n    if (webglInfo.support === 'hardware') {\n      score += 30;\n    } else if (webglInfo.support === 'software') {\n      score += 10;\n    }\n    \n    // Hardware acceleration bonus\n    if (webglInfo.hardwareAcceleration) {\n      score += 15;\n    }\n    \n    // Device type adjustment\n    if (deviceInfo.isMobile) {\n      score -= 15; // Mobile devices typically lower performance\n    }\n    if (deviceInfo.isTablet) {\n      score -= 5; // Tablets usually better than phones\n    }\n    \n    // CPU cores bonus\n    const cores = navigator.hardwareConcurrency || 4;\n    if (cores >= 8) {\n      score += 15;\n    } else if (cores >= 4) {\n      score += 10;\n    } else if (cores >= 2) {\n      score += 5;\n    }\n    \n    // Memory estimation bonus\n    const memory = this.estimateMemory();\n    if (memory >= 8192) {\n      score += 10;\n    } else if (memory >= 4096) {\n      score += 5;\n    }\n    \n    // Screen resolution adjustment\n    const pixelCount = window.screen.width * window.screen.height * (window.devicePixelRatio || 1);\n    if (pixelCount > 4000000) { // 4K+\n      score -= 10;\n    } else if (pixelCount > 2000000) { // 1080p+\n      score -= 5;\n    }\n    \n    return Math.max(0, Math.min(100, score));\n  }\n  \n  /**\n   * Classify device based on performance score\n   */\n  private classifyDevice(\n    performanceScore: number,\n    deviceInfo: { isMobile: boolean; isTablet: boolean }\n  ): DeviceClass {\n    if (performanceScore >= 80) {\n      return 'high-end';\n    } else if (performanceScore >= 60) {\n      return 'mid-range';\n    } else if (performanceScore >= 35) {\n      return 'low-end';\n    } else {\n      return 'very-low-end';\n    }\n  }\n  \n  /**\n   * Estimate available memory\n   */\n  private estimateMemory(): number {\n    // Try to get actual memory info\n    if ('memory' in performance) {\n      const memory = (performance as any).memory;\n      if (memory && memory.jsHeapSizeLimit) {\n        // Convert from bytes to MB and estimate total RAM\n        const heapLimitMB = memory.jsHeapSizeLimit / (1024 * 1024);\n        return Math.round(heapLimitMB * 4); // Rough estimation\n      }\n    }\n    \n    // Fallback estimation based on device characteristics\n    const cores = navigator.hardwareConcurrency || 4;\n    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);\n    \n    if (isMobile) {\n      if (cores >= 8) return 8192; // High-end mobile\n      if (cores >= 6) return 6144; // Mid-high mobile\n      if (cores >= 4) return 4096; // Mid mobile\n      return 2048; // Low-end mobile\n    } else {\n      if (cores >= 16) return 32768; // High-end desktop\n      if (cores >= 8) return 16384; // Mid-high desktop\n      if (cores >= 4) return 8192; // Mid desktop\n      return 4096; // Low-end desktop\n    }\n  }\n  \n  /**\n   * Detect network connection quality\n   */\n  private detectConnectionQuality(): ConnectionQuality {\n    if ('connection' in navigator) {\n      const connection = (navigator as any).connection;\n      if (connection) {\n        const { effectiveType, downlink } = connection;\n        \n        if (effectiveType === '4g' && downlink > 5) {\n          return 'fast';\n        } else if (effectiveType === '4g' || (effectiveType === '3g' && downlink > 1)) {\n          return 'medium';\n        } else {\n          return 'slow';\n        }\n      }\n    }\n    \n    // Fallback: assume medium quality\n    return 'medium';\n  }\n  \n  /**\n   * Check if user prefers reduced motion\n   */\n  private prefersReducedMotion(): boolean {\n    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n  }\n  \n  /**\n   * Check if device is likely low on battery\n   */\n  async isLowBattery(): Promise<boolean> {\n    try {\n      if ('getBattery' in navigator) {\n        const battery = await (navigator as any).getBattery();\n        return battery.level < 0.2 && !battery.charging;\n      }\n    } catch (error) {\n      // Battery API not available\n    }\n    return false;\n  }\n  \n  /**\n   * Get thermal state if available (experimental)\n   */\n  getThermalState(): 'normal' | 'fair' | 'serious' | 'critical' | 'unknown' {\n    if ('thermal' in navigator) {\n      return (navigator as any).thermal?.state || 'unknown';\n    }\n    return 'unknown';\n  }\n  \n  /**\n   * Clear cached capabilities (force re-detection)\n   */\n  clearCache(): void {\n    this.cachedCapabilities = null;\n  }\n}\n\n// Global device detector instance\nexport const deviceDetector = DeviceDetector.getInstance();\n\n/**\n * Convenience functions\n */\nexport const getDeviceCapabilities = (forceRefresh = false): Promise<DeviceCapabilities> => {\n  return deviceDetector.getDeviceCapabilities(forceRefresh);\n};\n\nexport const getFallbackRecommendation = (\n  capabilities?: DeviceCapabilities,\n  userPreferences?: {\n    preferPerformance?: boolean;\n    preferQuality?: boolean;\n    reducedMotion?: boolean;\n  }\n): Promise<FallbackRecommendation> => {\n  return deviceDetector.getFallbackRecommendation(capabilities, userPreferences);\n};\n\nexport const isLowPerformanceDevice = async (): Promise<boolean> => {\n  const capabilities = await getDeviceCapabilities();\n  return capabilities.deviceClass === 'low-end' || capabilities.deviceClass === 'very-low-end';\n};\n\nexport const shouldUseFallback = async (\n  minPerformanceScore = 50,\n  requireHardwareWebGL = false\n): Promise<boolean> => {\n  const capabilities = await getDeviceCapabilities();\n  \n  if (capabilities.performanceScore < minPerformanceScore) {\n    return true;\n  }\n  \n  if (requireHardwareWebGL && capabilities.webglSupport !== 'hardware') {\n    return true;\n  }\n  \n  // Check for low battery\n  const lowBattery = await deviceDetector.isLowBattery();\n  if (lowBattery) {\n    return true;\n  }\n  \n  return false;\n};