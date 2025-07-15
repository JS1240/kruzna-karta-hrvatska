/**
 * Animation Library Loader
 * 
 * Implements lazy loading and code splitting for heavy animation libraries
 * to minimize initial bundle size and improve loading performance.
 */

// Type definitions for lazy-loaded animation libraries
export interface ThreeJSModule {
  Scene: any;
  PerspectiveCamera: any;
  WebGLRenderer: any;
  Mesh: any;
  BoxGeometry: any;
  MeshBasicMaterial: any;
  [key: string]: any;
}

export interface VantaModule {
  TOPOLOGY: any;
  NET: any;
  CLOUDS: any;
  WAVES: any;
  [key: string]: any;
}

export interface P5Module {
  default: any;
  p5: any;
}

/**
 * Animation library loader class
 */
export class AnimationLibraryLoader {
  private static instance: AnimationLibraryLoader;
  private loadedLibraries: Map<string, any> = new Map();
  private loadingPromises: Map<string, Promise<any>> = new Map();
  private featureFlags: {
    enableThreeJS: boolean;
    enableVanta: boolean;
    enableP5: boolean;
    enableWebGL: boolean;
  };
  
  private constructor() {
    this.featureFlags = {
      enableThreeJS: true,
      enableVanta: true,
      enableP5: false, // Disabled by default due to size
      enableWebGL: this.detectWebGLSupport(),
    };
  }
  
  static getInstance(): AnimationLibraryLoader {
    if (!this.instance) {
      this.instance = new AnimationLibraryLoader();
    }
    return this.instance;
  }
  
  /**
   * Detect WebGL support
   */
  private detectWebGLSupport(): boolean {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      return !!gl;
    } catch (error) {
      return false;
    }
  }
  
  /**
   * Check if animation libraries should be loaded
   */
  shouldLoadAnimationLibraries(): boolean {
    // Don't load heavy animation libraries on low-end devices
    const hardwareConcurrency = navigator.hardwareConcurrency || 4;
    const connection = (navigator as any).connection;
    
    // Skip animations on very slow connections
    if (connection && connection.effectiveType === '2g') {
      return false;
    }
    
    // Skip animations on very low-end devices
    if (hardwareConcurrency < 2) {
      return false;
    }
    
    // Skip if WebGL is not supported
    if (!this.featureFlags.enableWebGL) {
      return false;
    }
    
    // Check for data saver mode
    if (connection && connection.saveData) {
      return false;
    }
    
    return true;
  }
  
  /**
   * Lazy load Three.js
   */
  async loadThreeJS(): Promise<ThreeJSModule | null> {
    if (!this.featureFlags.enableThreeJS || !this.shouldLoadAnimationLibraries()) {
      console.log('Three.js loading skipped due to feature flags or device limitations');
      return null;
    }
    
    const libraryKey = 'threejs';
    
    if (this.loadedLibraries.has(libraryKey)) {
      return this.loadedLibraries.get(libraryKey);
    }
    
    if (this.loadingPromises.has(libraryKey)) {
      return this.loadingPromises.get(libraryKey);
    }
    
    console.log('Loading Three.js...');
    
    const loadPromise = this.loadThreeJSModule();
    this.loadingPromises.set(libraryKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedLibraries.set(libraryKey, module);
      this.loadingPromises.delete(libraryKey);
      console.log('Three.js loaded successfully');
      return module;
    } catch (error) {
      this.loadingPromises.delete(libraryKey);
      console.warn('Failed to load Three.js:', error);
      return null;
    }
  }
  
  /**
   * Load Three.js module dynamically
   */
  private async loadThreeJSModule(): Promise<ThreeJSModule> {
    const threeModule = await import('three');
    return threeModule;
  }
  
  /**
   * Lazy load Vanta.js
   */
  async loadVanta(): Promise<VantaModule | null> {
    if (!this.featureFlags.enableVanta || !this.shouldLoadAnimationLibraries()) {
      console.log('Vanta.js loading skipped due to feature flags or device limitations');
      return null;
    }
    
    const libraryKey = 'vanta';
    
    if (this.loadedLibraries.has(libraryKey)) {
      return this.loadedLibraries.get(libraryKey);
    }
    
    if (this.loadingPromises.has(libraryKey)) {
      return this.loadingPromises.get(libraryKey);
    }
    
    console.log('Loading Vanta.js...');
    
    const loadPromise = this.loadVantaModule();
    this.loadingPromises.set(libraryKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedLibraries.set(libraryKey, module);
      this.loadingPromises.delete(libraryKey);
      console.log('Vanta.js loaded successfully');
      return module;
    } catch (error) {
      this.loadingPromises.delete(libraryKey);
      console.warn('Failed to load Vanta.js:', error);
      return null;
    }
  }
  
  /**
   * Load Vanta.js module dynamically
   */
  private async loadVantaModule(): Promise<VantaModule> {
    const vantaModule = await import('vanta');
    return vantaModule as any;
  }
  
  /**
   * Lazy load p5.js (optional, large library)
   */
  async loadP5(): Promise<P5Module | null> {
    if (!this.featureFlags.enableP5 || !this.shouldLoadAnimationLibraries()) {
      console.log('p5.js loading skipped due to feature flags or device limitations');
      return null;
    }
    
    const libraryKey = 'p5';
    
    if (this.loadedLibraries.has(libraryKey)) {
      return this.loadedLibraries.get(libraryKey);
    }
    
    if (this.loadingPromises.has(libraryKey)) {
      return this.loadingPromises.get(libraryKey);
    }
    
    console.log('Loading p5.js...');
    
    const loadPromise = this.loadP5Module();
    this.loadingPromises.set(libraryKey, loadPromise);
    
    try {
      const module = await loadPromise;
      this.loadedLibraries.set(libraryKey, module);
      this.loadingPromises.delete(libraryKey);
      console.log('p5.js loaded successfully');
      return module;
    } catch (error) {
      this.loadingPromises.delete(libraryKey);
      console.warn('Failed to load p5.js:', error);
      return null;
    }
  }
  
  /**
   * Load p5.js module dynamically
   */
  private async loadP5Module(): Promise<P5Module> {
    const p5Module = await import('p5');
    return p5Module;
  }
  
  /**
   * Load all required animation libraries based on usage
   */
  async loadRequiredLibraries(requirements: {
    needsThreeJS?: boolean;
    needsVanta?: boolean;
    needsP5?: boolean;
  }): Promise<{
    threeJS?: ThreeJSModule;
    vanta?: VantaModule;
    p5?: P5Module;
  }> {
    const results: any = {};
    const promises: Promise<void>[] = [];
    
    if (requirements.needsThreeJS) {
      promises.push(
        this.loadThreeJS().then(module => {
          if (module) results.threeJS = module;
        })
      );
    }
    
    if (requirements.needsVanta) {
      promises.push(
        this.loadVanta().then(module => {
          if (module) results.vanta = module;
        })
      );
    }
    
    if (requirements.needsP5) {
      promises.push(
        this.loadP5().then(module => {
          if (module) results.p5 = module;
        })
      );
    }
    
    await Promise.all(promises);
    return results;
  }
  
  /**
   * Preload libraries based on priority
   */
  async preloadLibraries(priority: 'high' | 'medium' | 'low' = 'medium'): Promise<void> {
    if (!this.shouldLoadAnimationLibraries()) {
      console.log('Animation library preloading skipped');
      return;
    }
    
    const promises: Promise<any>[] = [];
    
    // High priority: Always preload Three.js and Vanta for smooth UX
    if (priority === 'high') {
      promises.push(this.loadThreeJS());
      promises.push(this.loadVanta());
    }
    
    // Medium priority: Preload Three.js only
    else if (priority === 'medium') {
      promises.push(this.loadThreeJS());
    }
    
    // Low priority: Don't preload, wait for on-demand
    
    if (promises.length > 0) {
      try {
        await Promise.all(promises);
        console.log(`Animation libraries preloaded (priority: ${priority})`);
      } catch (error) {
        console.warn('Some animation libraries failed to preload:', error);
      }
    }
  }
  
  /**
   * Update feature flags
   */
  updateFeatureFlags(flags: Partial<{
    enableThreeJS: boolean;
    enableVanta: boolean;
    enableP5: boolean;
    enableWebGL: boolean;
  }>): void {
    this.featureFlags = { ...this.featureFlags, ...flags };
  }
  
  /**
   * Check if library is loaded
   */
  isLibraryLoaded(library: 'threejs' | 'vanta' | 'p5'): boolean {
    return this.loadedLibraries.has(library);
  }
  
  /**
   * Get loading status
   */
  getLoadingStatus(): {
    loaded: string[];
    loading: string[];
    available: string[];
  } {
    return {
      loaded: Array.from(this.loadedLibraries.keys()),
      loading: Array.from(this.loadingPromises.keys()),
      available: Object.entries(this.featureFlags)
        .filter(([key, enabled]) => enabled && key !== 'enableWebGL')
        .map(([key]) => key.replace('enable', '').toLowerCase()),
    };
  }
  
  /**
   * Get estimated library sizes (in KB)
   */
  getLibrarySizes(): { [key: string]: number } {
    return {
      threejs: 600, // ~600KB
      vanta: 100,   // ~100KB
      p5: 1200,     // ~1.2MB (very large)
    };
  }
  
  /**
   * Check bundle size impact
   */
  getBundleImpact(): {
    currentSize: number;
    potentialSize: number;
    recommendations: string[];
  } {
    const sizes = this.getLibrarySizes();
    const loadedLibraries = Array.from(this.loadedLibraries.keys());
    
    const currentSize = loadedLibraries.reduce((total, lib) => {
      return total + (sizes[lib] || 0);
    }, 0);
    
    const potentialSize = Object.entries(this.featureFlags)
      .filter(([key, enabled]) => enabled && key !== 'enableWebGL')
      .reduce((total, [key]) => {
        const libName = key.replace('enable', '').toLowerCase();
        return total + (sizes[libName] || 0);
      }, 0);
    
    const recommendations: string[] = [];
    
    if (potentialSize > 500) {
      recommendations.push('Consider disabling p5.js to reduce bundle size');
    }
    
    if (currentSize > 300 && !this.featureFlags.enableWebGL) {
      recommendations.push('WebGL not supported, consider using CSS animations instead');
    }
    
    if (loadedLibraries.includes('p5') && !loadedLibraries.includes('threejs')) {
      recommendations.push('p5.js loaded without Three.js - consider using Three.js instead');
    }
    
    return {
      currentSize,
      potentialSize,
      recommendations,
    };
  }
  
  /**
   * Cleanup loaded libraries
   */
  cleanup(): void {
    this.loadedLibraries.clear();
    this.loadingPromises.clear();
  }
}

// Global animation library loader instance
export const animationLibraryLoader = AnimationLibraryLoader.getInstance();

/**
 * Convenience functions for lazy loading
 */

/**
 * Load animation libraries conditionally
 */
export const loadAnimationLibraries = async (requirements: {
  needsThreeJS?: boolean;
  needsVanta?: boolean;
  needsP5?: boolean;
}): Promise<any> => {
  return animationLibraryLoader.loadRequiredLibraries(requirements);
};

/**
 * Preload animation libraries
 */
export const preloadAnimationLibraries = async (priority: 'high' | 'medium' | 'low' = 'medium'): Promise<void> => {
  return animationLibraryLoader.preloadLibraries(priority);
};

/**
 * Check if should load animations
 */
export const shouldLoadAnimations = (): boolean => {
  return animationLibraryLoader.shouldLoadAnimationLibraries();
};

/**
 * Get animation library loading status
 */
export const getAnimationLoadingStatus = () => {
  return animationLibraryLoader.getLoadingStatus();
};

/**
 * Get bundle size impact
 */
export const getAnimationBundleImpact = () => {
  return animationLibraryLoader.getBundleImpact();
};