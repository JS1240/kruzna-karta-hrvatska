/**
 * Enhanced Mobile Device Detection for Animation Optimization (T5.3)
 * 
 * Advanced mobile-specific detection capabilities for optimizing
 * animation intensity based on mobile device characteristics.
 */

import type { MobileBrowser, MobileOS, GraphicsAPI, WebGLSupport } from './deviceDetection';

export interface MobileCapabilities {
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
  deviceModel?: string;
  cpuArchitecture?: string;
  supportsPWA: boolean;
  supportsServiceWorker: boolean;
  supportsWebAssembly: boolean;
  viewportSize: {
    width: number;
    height: number;
  };
  safeAreaInsets?: {
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
}

export interface MobileOptimizationSettings {
  // Animation settings
  maxParticleCount: number;
  preferredFrameRate: number;
  enableMotionReduce: boolean;
  
  // Performance settings
  enableCPUThrottling: boolean;
  enableGPUMemoryLimit: boolean;
  maxTextureResolution: number;
  
  // Battery optimizations
  enableBatteryAwareness: boolean;
  lowBatteryThreshold: number;
  
  // Network optimizations
  enableDataSaving: boolean;
  preloadAnimations: boolean;
  
  // Visual optimizations
  enableHDRSupport: boolean;
  maxPixelDensity: number;
  preferredColorSpace: string;
}

/**
 * Enhanced mobile device detector
 */
export class EnhancedMobileDetector {
  private static instance: EnhancedMobileDetector;
  private cachedCapabilities: MobileCapabilities | null = null;
  
  private constructor() {}
  
  static getInstance(): EnhancedMobileDetector {
    if (!this.instance) {
      this.instance = new EnhancedMobileDetector();
    }
    return this.instance;
  }
  
  /**
   * Get comprehensive mobile capabilities
   */
  async getMobileCapabilities(forceRefresh = false): Promise<MobileCapabilities> {
    if (!forceRefresh && this.cachedCapabilities) {
      return this.cachedCapabilities;
    }
    
    const userAgent = navigator.userAgent;
    
    // Basic mobile detection
    const browser = this.detectMobileBrowser(userAgent);
    const { os, osVersion } = this.detectMobileOS(userAgent);
    
    // Device model detection
    const deviceModel = this.detectDeviceModel(userAgent, os);
    
    // CPU architecture detection
    const cpuArchitecture = this.detectCPUArchitecture(userAgent, os);
    
    // Graphics API detection
    const graphicsAPI = this.detectGraphicsAPI(os, browser);
    
    // WebGL capabilities
    const webglCapabilities = this.detectWebGLCapabilities();
    
    // Touch and interaction support
    const touchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const orientationSupport = 'orientation' in window || 'onorientationchange' in window;
    
    // Modern web capabilities
    const supportsPWA = this.detectPWASupport();
    const supportsServiceWorker = 'serviceWorker' in navigator;
    const supportsWebAssembly = typeof WebAssembly === 'object';
    
    // Data saving detection
    const dataSaverMode = this.detectDataSaverMode();
    
    // Viewport and safe area detection
    const viewportSize = this.getViewportSize();
    const safeAreaInsets = this.getSafeAreaInsets();
    
    this.cachedCapabilities = {
      browser,
      os,
      osVersion,
      deviceModel,
      cpuArchitecture,
      graphicsAPI,
      ...webglCapabilities,
      touchSupport,
      orientationSupport,
      supportsPWA,
      supportsServiceWorker,
      supportsWebAssembly,
      dataSaverMode,
      reducedDataMode: dataSaverMode,
      viewportSize,
      safeAreaInsets
    };
    
    return this.cachedCapabilities;
  }
  
  /**
   * Detect mobile browser type with enhanced detection
   */
  private detectMobileBrowser(userAgent: string): MobileBrowser {
    const ua = userAgent.toLowerCase();
    
    // Samsung Browser detection (before Chrome check)
    if (ua.includes('samsungbrowser')) return 'samsung';
    
    // Chrome detection (most common)
    if (ua.includes('chrome') && !ua.includes('edge') && !ua.includes('opr')) return 'chrome';
    
    // Safari detection (iOS)
    if (ua.includes('safari') && !ua.includes('chrome')) return 'safari';
    
    // Firefox detection
    if (ua.includes('firefox') || ua.includes('fxios')) return 'firefox';
    
    // Edge detection
    if (ua.includes('edge') || ua.includes('edgios')) return 'edge';
    
    // Opera detection
    if (ua.includes('opera') || ua.includes('opr') || ua.includes('opios')) return 'opera';
    
    return 'unknown';
  }
  
  /**
   * Detect mobile OS and version with enhanced parsing
   */
  private detectMobileOS(userAgent: string): { os: MobileOS; osVersion: string } {
    const ua = userAgent.toLowerCase();
    
    // iOS detection with version parsing
    if (ua.includes('iphone') || ua.includes('ipad') || ua.includes('ipod')) {
      const iosMatch = ua.match(/os (\d+)[._](\d+)[._]?(\d+)?/) || 
                      ua.match(/version\/(\d+)\.(\d+)\.?(\d+)?/);
      if (iosMatch) {
        const version = `${iosMatch[1]}.${iosMatch[2]}${iosMatch[3] ? '.' + iosMatch[3] : ''}`;
        return { os: 'ios', osVersion: version };
      }
      return { os: 'ios', osVersion: 'unknown' };
    }
    
    // Android detection with enhanced version parsing
    if (ua.includes('android')) {
      const androidMatch = ua.match(/android (\d+)\.(\d+)\.?(\d+)?/) ||
                          ua.match(/android\/(\d+)\.(\d+)\.?(\d+)?/);
      if (androidMatch) {
        const version = `${androidMatch[1]}.${androidMatch[2]}${androidMatch[3] ? '.' + androidMatch[3] : ''}`;
        return { os: 'android', osVersion: version };
      }
      return { os: 'android', osVersion: 'unknown' };
    }
    
    return { os: 'unknown', osVersion: 'unknown' };
  }
  
  /**
   * Detect device model for better optimization
   */
  private detectDeviceModel(userAgent: string, os: MobileOS): string | undefined {
    const ua = userAgent.toLowerCase();
    
    if (os === 'ios') {
      // iPhone models
      if (ua.includes('iphone')) {
        if (ua.includes('iphone15')) return 'iPhone 15';
        if (ua.includes('iphone14')) return 'iPhone 14';
        if (ua.includes('iphone13')) return 'iPhone 13';
        if (ua.includes('iphone12')) return 'iPhone 12';
        if (ua.includes('iphone11')) return 'iPhone 11';
        if (ua.includes('iphonex')) return 'iPhone X';
        return 'iPhone';
      }
      
      // iPad models
      if (ua.includes('ipad')) {
        if (ua.includes('ipad13')) return 'iPad Pro';
        if (ua.includes('ipad12')) return 'iPad Pro';
        return 'iPad';
      }
    }
    
    if (os === 'android') {
      // Samsung devices
      if (ua.includes('samsung') || ua.includes('sm-')) {
        if (ua.includes('galaxy s24')) return 'Galaxy S24';
        if (ua.includes('galaxy s23')) return 'Galaxy S23';
        if (ua.includes('galaxy s22')) return 'Galaxy S22';
        if (ua.includes('galaxy')) return 'Samsung Galaxy';
        return 'Samsung';
      }
      
      // Google Pixel
      if (ua.includes('pixel')) {
        const pixelMatch = ua.match(/pixel (\d+)/);
        if (pixelMatch) return `Pixel ${pixelMatch[1]}`;
        return 'Google Pixel';
      }
      
      // OnePlus
      if (ua.includes('oneplus')) return 'OnePlus';
      
      // Xiaomi
      if (ua.includes('xiaomi') || ua.includes('mi ')) return 'Xiaomi';
    }
    
    return undefined;
  }
  
  /**
   * Detect CPU architecture
   */
  private detectCPUArchitecture(userAgent: string, os: MobileOS): string | undefined {
    const ua = userAgent.toLowerCase();
    
    if (os === 'ios') {
      // iOS devices use Apple Silicon
      if (ua.includes('iphone15') || ua.includes('iphone14')) return 'A16/A17';
      if (ua.includes('iphone13') || ua.includes('iphone12')) return 'A15/A14';
      if (ua.includes('ipad13') || ua.includes('ipad12')) return 'M1/M2';
      return 'Apple Silicon';
    }
    
    if (os === 'android') {
      // Common Android architectures
      if (ua.includes('arm64') || ua.includes('aarch64')) return 'ARM64';
      if (ua.includes('armv7') || ua.includes('armv8')) return 'ARM';
      if (ua.includes('x86_64')) return 'x86_64';
      if (ua.includes('x86')) return 'x86';
      return 'ARM'; // Most Android devices are ARM
    }
    
    return undefined;
  }
  
  /**
   * Detect graphics API with enhanced detection
   */
  private detectGraphicsAPI(os: MobileOS, browser: MobileBrowser): GraphicsAPI {
    if (os === 'ios') {
      // iOS uses Metal for everything (WebGL is translated to Metal)
      return 'metal';
    }
    
    if (os === 'android') {
      // Modern Android devices may support Vulkan
      // Check for indicators in user agent or capabilities
      return 'opengl-es'; // Default for Android
    }
    
    return 'unknown';
  }
  
  /**
   * Detect WebGL capabilities with mobile-specific optimizations
   */
  private detectWebGLCapabilities(): {
    gpuMemoryMB?: number;
    maxTextureSize?: number;
    supportsWebGL2: boolean;
    supportsHalfFloat: boolean;
    maxVertexTextureImageUnits?: number;
    maxFragmentTextureImageUnits?: number;
  } {
    const result = {
      supportsWebGL2: false,
      supportsHalfFloat: false,
      gpuMemoryMB: undefined as number | undefined,
      maxTextureSize: undefined as number | undefined,
      maxVertexTextureImageUnits: undefined as number | undefined,
      maxFragmentTextureImageUnits: undefined as number | undefined
    };
    
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      const gl2 = canvas.getContext('webgl2');
      
      result.supportsWebGL2 = !!gl2;
      
      if (gl) {
        // Get WebGL parameters
        result.maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
        result.maxVertexTextureImageUnits = gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS);
        result.maxFragmentTextureImageUnits = gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS);
        
        // Check for half float support (important for mobile performance)
        const halfFloatExt = gl.getExtension('OES_texture_half_float') || 
                           gl.getExtension('EXT_color_buffer_half_float');
        result.supportsHalfFloat = !!halfFloatExt;
        
        // Estimate GPU memory based on texture capabilities
        const maxTexture = result.maxTextureSize || 2048;
        if (maxTexture >= 16384) {
          result.gpuMemoryMB = 4096; // Very high-end mobile GPU
        } else if (maxTexture >= 8192) {
          result.gpuMemoryMB = 2048; // High-end mobile GPU
        } else if (maxTexture >= 4096) {
          result.gpuMemoryMB = 1024; // Mid-range mobile GPU
        } else if (maxTexture >= 2048) {
          result.gpuMemoryMB = 512; // Low-end mobile GPU
        } else {
          result.gpuMemoryMB = 256; // Very low-end mobile GPU
        }
        
        // Try to detect specific GPU models from renderer string
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
          const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
          const gpuMemory = this.parseGPUMemoryFromRenderer(renderer);
          if (gpuMemory) {
            result.gpuMemoryMB = gpuMemory;
          }
        }
      }
      
      return result;
    } catch (error) {
      return result;
    }
  }
  
  /**
   * Parse GPU memory from renderer string
   */
  private parseGPUMemoryFromRenderer(renderer: string): number | undefined {
    if (!renderer) return undefined;
    
    const rendererLower = renderer.toLowerCase();
    
    // Look for memory indicators in renderer string
    const memoryPatterns = [
      /(\d+)\s*gb/i,
      /(\d+)\s*mb/i,
      /memory[:\s]*(\d+)/i
    ];
    
    for (const pattern of memoryPatterns) {
      const match = rendererLower.match(pattern);
      if (match) {
        const value = parseInt(match[1]);
        if (rendererLower.includes('gb')) {
          return value * 1024;
        } else {
          return value;
        }
      }
    }
    
    // Known GPU models and their typical memory
    if (rendererLower.includes('adreno')) {
      if (rendererLower.includes('740') || rendererLower.includes('750')) return 2048;
      if (rendererLower.includes('730') || rendererLower.includes('660')) return 1024;
      if (rendererLower.includes('640') || rendererLower.includes('630')) return 512;
      return 256;
    }
    
    if (rendererLower.includes('mali')) {
      if (rendererLower.includes('g78') || rendererLower.includes('g77')) return 1024;
      if (rendererLower.includes('g76') || rendererLower.includes('g71')) return 512;
      return 256;
    }
    
    if (rendererLower.includes('apple')) {
      if (rendererLower.includes('a17') || rendererLower.includes('a16')) return 2048;
      if (rendererLower.includes('a15') || rendererLower.includes('a14')) return 1024;
      return 512;
    }
    
    return undefined;
  }
  
  /**
   * Detect PWA support
   */
  private detectPWASupport(): boolean {
    return 'serviceWorker' in navigator && 
           'PushManager' in window && 
           'Notification' in window;
  }
  
  /**
   * Enhanced data saver mode detection
   */
  private detectDataSaverMode(): boolean {
    // Chrome's Data Saver API
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection?.saveData) {
        return true;
      }
      
      // Infer data saving from very slow connections
      if (connection?.effectiveType === '2g' || 
          (connection?.effectiveType === '3g' && connection?.downlink < 0.5)) {
        return true;
      }
    }
    
    // Opera Mini detection
    if ('operaMini' in window || navigator.userAgent.includes('Opera Mini')) {
      return true;
    }
    
    // UC Browser data compression
    if (navigator.userAgent.includes('UCBrowser')) {
      return true;
    }
    
    return false;
  }
  
  /**
   * Get current viewport size
   */
  private getViewportSize(): { width: number; height: number } {
    return {
      width: window.innerWidth || document.documentElement.clientWidth,
      height: window.innerHeight || document.documentElement.clientHeight
    };
  }
  
  /**
   * Get safe area insets for devices with notches/cutouts
   */
  private getSafeAreaInsets(): { top: number; bottom: number; left: number; right: number } | undefined {
    try {
      const computedStyle = getComputedStyle(document.documentElement);
      
      const safeAreaInsetTop = computedStyle.getPropertyValue('env(safe-area-inset-top)') ||
                              computedStyle.getPropertyValue('constant(safe-area-inset-top)');
      const safeAreaInsetBottom = computedStyle.getPropertyValue('env(safe-area-inset-bottom)') ||
                                 computedStyle.getPropertyValue('constant(safe-area-inset-bottom)');
      const safeAreaInsetLeft = computedStyle.getPropertyValue('env(safe-area-inset-left)') ||
                               computedStyle.getPropertyValue('constant(safe-area-inset-left)');
      const safeAreaInsetRight = computedStyle.getPropertyValue('env(safe-area-inset-right)') ||
                                computedStyle.getPropertyValue('constant(safe-area-inset-right)');
      
      if (safeAreaInsetTop || safeAreaInsetBottom || safeAreaInsetLeft || safeAreaInsetRight) {
        return {
          top: parseInt(safeAreaInsetTop) || 0,
          bottom: parseInt(safeAreaInsetBottom) || 0,
          left: parseInt(safeAreaInsetLeft) || 0,
          right: parseInt(safeAreaInsetRight) || 0
        };
      }
    } catch (error) {
      // Safe area insets not supported
    }
    
    return undefined;
  }
  
  /**
   * Generate mobile-optimized animation settings
   */
  generateMobileOptimizations(capabilities: MobileCapabilities): MobileOptimizationSettings {
    const settings: MobileOptimizationSettings = {
      // Default values
      maxParticleCount: 8,
      preferredFrameRate: 30,
      enableMotionReduce: false,
      enableCPUThrottling: true,
      enableGPUMemoryLimit: true,
      maxTextureResolution: 2048,
      enableBatteryAwareness: true,
      lowBatteryThreshold: 0.2,
      enableDataSaving: false,
      preloadAnimations: true,
      enableHDRSupport: false,
      maxPixelDensity: 2.0,
      preferredColorSpace: 'srgb'
    };
    
    // Optimize based on OS
    if (capabilities.os === 'ios') {
      settings.preferredFrameRate = 60; // iOS typically handles 60fps better
      settings.enableHDRSupport = true; // iOS has better HDR support
      settings.preferredColorSpace = 'display-p3';
    }
    
    // Optimize based on GPU memory
    if (capabilities.gpuMemoryMB) {
      if (capabilities.gpuMemoryMB >= 2048) {
        settings.maxParticleCount = 16;
        settings.maxTextureResolution = 4096;
        settings.preferredFrameRate = 60;
      } else if (capabilities.gpuMemoryMB >= 1024) {
        settings.maxParticleCount = 12;
        settings.maxTextureResolution = 2048;
        settings.preferredFrameRate = 45;
      } else if (capabilities.gpuMemoryMB < 512) {
        settings.maxParticleCount = 4;
        settings.maxTextureResolution = 1024;
        settings.preferredFrameRate = 20;
      }
    }
    
    // Optimize for data saving
    if (capabilities.dataSaverMode) {
      settings.enableDataSaving = true;
      settings.preloadAnimations = false;
      settings.maxParticleCount = Math.min(settings.maxParticleCount, 4);
      settings.preferredFrameRate = Math.min(settings.preferredFrameRate, 30);
    }
    
    // Optimize for small screens
    if (capabilities.viewportSize.width < 414) { // iPhone Plus size
      settings.maxParticleCount = Math.min(settings.maxParticleCount, 6);
      settings.maxTextureResolution = Math.min(settings.maxTextureResolution, 1024);
    }
    
    // Optimize for older devices
    if (capabilities.os === 'ios' && capabilities.osVersion.startsWith('12')) {
      settings.preferredFrameRate = 30;
      settings.maxParticleCount = Math.min(settings.maxParticleCount, 6);
    }
    
    if (capabilities.os === 'android' && parseInt(capabilities.osVersion) < 9) {
      settings.preferredFrameRate = 30;
      settings.maxParticleCount = Math.min(settings.maxParticleCount, 6);
      settings.enableCPUThrottling = true;
    }
    
    return settings;
  }
  
  /**
   * Clear cached capabilities
   */
  clearCache(): void {
    this.cachedCapabilities = null;
  }
}

// Global enhanced mobile detector instance
export const enhancedMobileDetector = EnhancedMobileDetector.getInstance();

/**
 * Convenience functions
 */
export const getMobileCapabilities = (forceRefresh = false): Promise<MobileCapabilities> => {
  return enhancedMobileDetector.getMobileCapabilities(forceRefresh);
};

export const getMobileOptimizations = async (): Promise<MobileOptimizationSettings> => {
  const capabilities = await getMobileCapabilities();
  return enhancedMobileDetector.generateMobileOptimizations(capabilities);
};

export const isMobileHighEnd = async (): Promise<boolean> => {
  const capabilities = await getMobileCapabilities();
  return (capabilities.gpuMemoryMB || 0) >= 1024 && 
         capabilities.supportsWebGL2 && 
         capabilities.maxTextureSize && capabilities.maxTextureSize >= 4096;
};

export const shouldUseMobileOptimizations = async (): Promise<boolean> => {
  const capabilities = await getMobileCapabilities();
  return capabilities.dataSaverMode || 
         (capabilities.gpuMemoryMB || 0) < 512 ||
         capabilities.viewportSize.width < 414;
};