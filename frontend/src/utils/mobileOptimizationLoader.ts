/**
 * Mobile Optimization Loader
 * 
 * Implements lazy loading and conditional imports for mobile optimization
 * features to minimize bundle size impact and improve performance.
 */

import type { MobileCapabilities, MobileOptimizationSettings } from './mobileDetection';

// Type definitions for lazy-loaded modules
export interface MobileDetectionModule {
  enhancedMobileDetector: any;
  getMobileCapabilities: (forceRefresh?: boolean) => Promise<MobileCapabilities>;
  getMobileOptimizations: () => Promise<MobileOptimizationSettings>;
  isMobileHighEnd: () => Promise<boolean>;
  shouldUseMobileOptimizations: () => Promise<boolean>;
}

export interface MobilePerformanceModule {
  MobilePerformanceMonitor: any;
  createMobilePerformanceMonitor: (callbacks?: any, thresholds?: any) => any;
}

export interface ConnectionOptimizerModule {
  connectionAwareOptimizer: any;
  getCurrentConnectionProfile: () => any;
  optimizeForConnection: (baseSettings: MobileOptimizationSettings) => MobileOptimizationSettings;
  shouldEnableConnectionFeature: (feature: string) => boolean;
  getConnectionQuality: () => 'excellent' | 'good' | 'fair' | 'poor';
}

export interface TouchOptimizerModule {
  createMobileTouchOptimizer: (settings?: any) => any;
}

/**
 * Mobile optimization feature flags
 */
export interface MobileFeatureFlags {
  enableDeviceDetection: boolean;
  enablePerformanceMonitoring: boolean;
  enableConnectionOptimization: boolean;
  enableTouchOptimization: boolean;
  enableAdvancedFeatures: boolean;
}

/**
 * Mobile optimization loader class
 */
export class MobileOptimizationLoader {
  private static instance: MobileOptimizationLoader;
  private loadedModules: Map<string, any> = new Map();
  private loadingPromises: Map<string, Promise<any>> = new Map();
  private featureFlags: MobileFeatureFlags;
  private isMobileDevice: boolean = false;
  private deviceCapabilities: MobileCapabilities | null = null;
  
  private constructor() {
    this.featureFlags = this.getDefaultFeatureFlags();
    this.detectMobileDevice();
  }
  
  static getInstance(): MobileOptimizationLoader {
    if (!this.instance) {
      this.instance = new MobileOptimizationLoader();
    }
    return this.instance;
  }
  
  /**
   * Get default feature flags
   */
  private getDefaultFeatureFlags(): MobileFeatureFlags {
    return {
      enableDeviceDetection: true,
      enablePerformanceMonitoring: false, // Load only when needed
      enableConnectionOptimization: false, // Load only when needed
      enableTouchOptimization: false, // Load only when needed
      enableAdvancedFeatures: false, // Load only for high-end devices
    };
  }
  
  /**
   * Basic mobile device detection (lightweight)
   */
  private detectMobileDevice(): void {
    const userAgent = navigator.userAgent.toLowerCase();
    this.isMobileDevice = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent) ||
                      window.innerWidth <= 768 ||
                      ('ontouchstart' in window) ||
                      (navigator.maxTouchPoints > 0);
  }
  
  /**
   * Update feature flags based on conditions
   */
  updateFeatureFlags(flags: Partial<MobileFeatureFlags>): void {
    this.featureFlags = { ...this.featureFlags, ...flags };
  }
  
  /**
   * Check if mobile optimizations should be loaded
   */
  shouldLoadMobileOptimizations(): boolean {
    return this.isMobileDevice || 
           window.innerWidth <= 1024 || // Include tablets
           this.hasLowPerformanceIndicators();
  }
  
  /**
   * Basic performance indicators check
   */
  private hasLowPerformanceIndicators(): boolean {
    // Check for basic performance indicators
    const hardwareConcurrency = navigator.hardwareConcurrency || 4;
    const connection = (navigator as any).connection;
    
    // Low CPU cores
    if (hardwareConcurrency < 4) return true;
    
    // Slow connection
    if (connection && connection.effectiveType === '2g') return true;
    
    // Data saver mode
    if (connection && connection.saveData) return true;
    
    // Low memory (if available)
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      if (memory && memory.jsHeapSizeLimit < 1024 * 1024 * 1024) { // < 1GB
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * Lazy load mobile detection module
   */
  async loadMobileDetection(): Promise<MobileDetectionModule | null> {
    if (!this.featureFlags.enableDeviceDetection) {
      return null;
    }
    
    const moduleKey = 'mobileDetection';
    
    if (this.loadedModules.has(moduleKey)) {
      return this.loadedModules.get(moduleKey);
    }
    
    if (this.loadingPromises.has(moduleKey)) {
      return this.loadingPromises.get(moduleKey);
    }
    
    const loadPromise = this.loadMobileDetectionModule();
    this.loadingPromises.set(moduleKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedModules.set(moduleKey, module);
      this.loadingPromises.delete(moduleKey);
      return module;
    } catch (error) {
      this.loadingPromises.delete(moduleKey);
      console.warn('Failed to load mobile detection module:', error);
      return null;
    }
  }
  
  /**
   * Load mobile detection module dynamically
   */
  private async loadMobileDetectionModule(): Promise<MobileDetectionModule> {
    const module = await import('./mobileDetection');
    
    // Get initial device capabilities
    this.deviceCapabilities = await module.getMobileCapabilities();
    
    // Update feature flags based on device capabilities
    this.updateFeatureFlagsBasedOnDevice();
    
    return module;
  }
  
  /**
   * Update feature flags based on detected device capabilities
   */
  private updateFeatureFlagsBasedOnDevice(): void {
    if (!this.deviceCapabilities) return;
    
    const { gpuMemoryMB, supportsWebGL2, maxTextureSize } = this.deviceCapabilities;
    
    // Enable advanced features for high-end devices
    if (gpuMemoryMB && gpuMemoryMB >= 1024 && supportsWebGL2) {
      this.featureFlags.enableAdvancedFeatures = true;
    }
    
    // Enable performance monitoring for devices that can handle it
    if (maxTextureSize && maxTextureSize >= 2048) {
      this.featureFlags.enablePerformanceMonitoring = true;
    }
    
    // Always enable connection optimization for mobile
    if (this.isMobileDevice) {
      this.featureFlags.enableConnectionOptimization = true;
      this.featureFlags.enableTouchOptimization = true;
    }
  }
  
  /**
   * Lazy load performance monitoring module
   */
  async loadPerformanceMonitoring(): Promise<MobilePerformanceModule | null> {
    if (!this.featureFlags.enablePerformanceMonitoring) {
      return null;
    }
    
    const moduleKey = 'performanceMonitoring';
    
    if (this.loadedModules.has(moduleKey)) {
      return this.loadedModules.get(moduleKey);
    }
    
    if (this.loadingPromises.has(moduleKey)) {
      return this.loadingPromises.get(moduleKey);
    }
    
    const loadPromise = import('./mobilePerformanceMonitor');
    this.loadingPromises.set(moduleKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedModules.set(moduleKey, module);
      this.loadingPromises.delete(moduleKey);
      return module;
    } catch (error) {
      this.loadingPromises.delete(moduleKey);
      console.warn('Failed to load performance monitoring module:', error);
      return null;
    }
  }
  
  /**
   * Lazy load connection optimization module
   */
  async loadConnectionOptimization(): Promise<ConnectionOptimizerModule | null> {
    if (!this.featureFlags.enableConnectionOptimization) {
      return null;
    }
    
    const moduleKey = 'connectionOptimization';
    
    if (this.loadedModules.has(moduleKey)) {
      return this.loadedModules.get(moduleKey);
    }
    
    if (this.loadingPromises.has(moduleKey)) {
      return this.loadingPromises.get(moduleKey);
    }
    
    const loadPromise = import('./connectionAwareOptimizer');
    this.loadingPromises.set(moduleKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedModules.set(moduleKey, module);
      this.loadingPromises.delete(moduleKey);
      return module;
    } catch (error) {
      this.loadingPromises.delete(moduleKey);
      console.warn('Failed to load connection optimization module:', error);
      return null;
    }
  }
  
  /**
   * Lazy load touch optimization module
   */
  async loadTouchOptimization(): Promise<TouchOptimizerModule | null> {
    if (!this.featureFlags.enableTouchOptimization || !this.isMobileDevice) {
      return null;
    }
    
    const moduleKey = 'touchOptimization';
    
    if (this.loadedModules.has(moduleKey)) {
      return this.loadedModules.get(moduleKey);
    }
    
    if (this.loadingPromises.has(moduleKey)) {
      return this.loadingPromises.get(moduleKey);
    }
    
    const loadPromise = import('./mobileTouchOptimizer');
    this.loadingPromises.set(moduleKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedModules.set(moduleKey, module);
      this.loadingPromises.delete(moduleKey);
      return module;
    } catch (error) {
      this.loadingPromises.delete(moduleKey);
      console.warn('Failed to load touch optimization module:', error);
      return null;
    }
  }
  
  /**
   * Load all applicable mobile optimizations
   */
  async loadApplicableOptimizations(): Promise<{
    mobileDetection?: MobileDetectionModule;
    performanceMonitoring?: MobilePerformanceModule;
    connectionOptimization?: ConnectionOptimizerModule;
    touchOptimization?: TouchOptimizerModule;
  }> {
    const results: any = {};
    
    // Always try to load mobile detection first
    results.mobileDetection = await this.loadMobileDetection();
    
    // Load other modules based on feature flags and device capabilities
    const promises = [];
    
    if (this.shouldLoadMobileOptimizations()) {
      if (this.featureFlags.enablePerformanceMonitoring) {
        promises.push(
          this.loadPerformanceMonitoring().then(module => {
            if (module) results.performanceMonitoring = module;
          })
        );
      }
      
      if (this.featureFlags.enableConnectionOptimization) {
        promises.push(
          this.loadConnectionOptimization().then(module => {
            if (module) results.connectionOptimization = module;
          })
        );
      }
      
      if (this.featureFlags.enableTouchOptimization) {
        promises.push(
          this.loadTouchOptimization().then(module => {
            if (module) results.touchOptimization = module;
          })
        );
      }
    }
    
    // Wait for all applicable modules to load
    await Promise.all(promises);
    
    return results;
  }
  
  /**
   * Get basic mobile optimization settings (lightweight)
   */
  getBasicMobileSettings(): MobileOptimizationSettings {
    return {
      maxParticleCount: this.isMobileDevice ? 6 : 12,
      preferredFrameRate: this.isMobileDevice ? 30 : 60,
      enableMotionReduce: false,
      enableCPUThrottling: this.isMobileDevice,
      enableGPUMemoryLimit: this.isMobileDevice,
      maxTextureResolution: this.isMobileDevice ? 1024 : 2048,
      enableBatteryAwareness: this.isMobileDevice,
      lowBatteryThreshold: 0.2,
      enableDataSaving: false,
      preloadAnimations: !this.isMobileDevice,
      enableHDRSupport: false,
      maxPixelDensity: this.isMobileDevice ? 2.0 : 3.0,
      preferredColorSpace: 'srgb'
    };
  }
  
  /**
   * Check if module is loaded
   */
  isModuleLoaded(moduleKey: string): boolean {
    return this.loadedModules.has(moduleKey);
  }
  
  /**
   * Get loaded modules info
   */
  getLoadedModulesInfo(): { [key: string]: boolean } {
    return {
      mobileDetection: this.isModuleLoaded('mobileDetection'),
      performanceMonitoring: this.isModuleLoaded('performanceMonitoring'),
      connectionOptimization: this.isModuleLoaded('connectionOptimization'),
      touchOptimization: this.isModuleLoaded('touchOptimization'),
    };
  }
  
  /**
   * Get feature flags
   */
  getFeatureFlags(): MobileFeatureFlags {
    return { ...this.featureFlags };
  }
  
  /**
   * Get device capabilities (if loaded)
   */
  getDeviceCapabilities(): MobileCapabilities | null {
    return this.deviceCapabilities;
  }
  
  /**
   * Check if is mobile device
   */
  isMobile(): boolean {
    return this.isMobileDevice;
  }
  
  /**
   * Cleanup loaded modules
   */
  cleanup(): void {
    this.loadedModules.clear();
    this.loadingPromises.clear();
  }
}

// Global mobile optimization loader instance
export const mobileOptimizationLoader = MobileOptimizationLoader.getInstance();

/**
 * Convenience functions for conditional loading
 */

/**
 * Load mobile optimizations conditionally
 */
export const loadMobileOptimizations = async (): Promise<any> => {
  return mobileOptimizationLoader.loadApplicableOptimizations();
};

/**
 * Get basic mobile settings without loading heavy modules
 */
export const getBasicMobileSettings = (): MobileOptimizationSettings => {
  return mobileOptimizationLoader.getBasicMobileSettings();
};

/**
 * Check if mobile optimizations should be enabled
 */
export const shouldEnableMobileOptimizations = (): boolean => {
  return mobileOptimizationLoader.shouldLoadMobileOptimizations();
};

/**
 * Load mobile detection only
 */
export const loadMobileDetectionOnly = async () => {
  return mobileOptimizationLoader.loadMobileDetection();
};

/**
 * Load performance monitoring conditionally
 */
export const loadPerformanceMonitoring = async () => {
  return mobileOptimizationLoader.loadPerformanceMonitoring();
};

/**
 * Load connection optimization conditionally
 */
export const loadConnectionOptimization = async () => {
  return mobileOptimizationLoader.loadConnectionOptimization();
};

/**
 * Load touch optimization conditionally
 */
export const loadTouchOptimization = async () => {
  return mobileOptimizationLoader.loadTouchOptimization();
};