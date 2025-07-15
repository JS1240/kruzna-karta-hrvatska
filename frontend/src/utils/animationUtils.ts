import { VantaTopologyManager, createTopologyAnimation } from './vantaUtils';
import { P5Performance, createP5Instance, cleanupP5Instance, P5AnimationConfig } from './p5Utils';
import { BRAND_COLORS, hexToDecimal } from './colorUtils';
import { 
  globalPerformanceMonitor, 
  FrameRateMonitor, 
  type PerformanceMetrics, 
  type PerformanceCallbacks,
  type PerformanceThresholds 
} from './performanceMonitor';

/**
 * Animation initialization utilities
 * Provides unified interface for managing both p5.js and VANTA.js animations
 */

export type AnimationType = 'vanta-topology' | 'p5-custom' | 'none';

export interface AnimationConfig {
  type: AnimationType;
  element: HTMLElement;
  intensity?: 'low' | 'medium' | 'high';
  respectReducedMotion?: boolean;
  enablePerformanceMonitoring?: boolean;
  customOptions?: Record<string, any>;
  /** Performance monitoring callbacks (T5.1) */
  performanceCallbacks?: PerformanceCallbacks;
  /** Custom performance thresholds (T5.1) */
  performanceThresholds?: Partial<PerformanceThresholds>;
  /** Target FPS for performance monitoring (auto-detected if not provided) */
  fpsTarget?: number;
  /** Enable automatic performance adjustment based on FPS */
  autoPerformanceAdjustment?: boolean;
}

export interface AnimationInstance {
  type: AnimationType;
  instance: any;
  element: HTMLElement;
  isActive: boolean;
  destroy: () => void;
  resize: () => void;
  updateConfig: (config: Record<string, any>) => void;
  /** Performance monitor instance (T5.1) */
  performanceMonitor?: FrameRateMonitor;
  /** Get current performance metrics (T5.1) */
  getPerformanceMetrics?: () => PerformanceMetrics | null;
  /** Start performance monitoring (T5.1) */
  startPerformanceMonitoring?: (callbacks?: PerformanceCallbacks) => void;
  /** Stop performance monitoring (T5.1) */
  stopPerformanceMonitoring?: () => void;
}

/**
 * Animation manager class to handle multiple animation instances
 */
export class AnimationManager {
  private animations: Map<string, AnimationInstance> = new Map();
  private legacyPerformanceMonitor: PerformanceMonitor;
  private globalPerformanceCallbacks: PerformanceCallbacks = {};

  constructor() {
    this.legacyPerformanceMonitor = new PerformanceMonitor();
    this.setupGlobalListeners();
    this.setupGlobalPerformanceCallbacks();
  }

  /**
   * Initialize an animation on a given element
   * @param id - Unique identifier for this animation
   * @param config - Animation configuration
   * @returns Promise that resolves to the animation instance
   */
  async initializeAnimation(id: string, config: AnimationConfig): Promise<AnimationInstance | null> {
    try {
      // Check for reduced motion preference
      if (config.respectReducedMotion !== false && this.shouldReduceMotion()) {
        console.log(`Animation ${id} disabled due to reduced motion preference`);
        return null;
      }

      // Cleanup existing animation with this ID
      if (this.animations.has(id)) {
        this.destroyAnimation(id);
      }

      let animationInstance: AnimationInstance;

      switch (config.type) {
        case 'vanta-topology':
          animationInstance = await this.initializeVantaTopology(id, config);
          break;
        case 'p5-custom':
          animationInstance = await this.initializeP5Animation(id, config);
          break;
        case 'none':
          return null;
        default:
          throw new Error(`Unsupported animation type: ${config.type}`);
      }

      this.animations.set(id, animationInstance);

      // Start performance monitoring if enabled (T5.1)
      if (config.enablePerformanceMonitoring) {
        this.startEnhancedPerformanceMonitoring(id, animationInstance, config);
      }

      console.log(`Animation ${id} initialized successfully`);
      return animationInstance;

    } catch (error) {
      console.error(`Failed to initialize animation ${id}:`, error);
      return null;
    }
  }

  /**
   * Initialize VANTA topology animation
   */
  private async initializeVantaTopology(id: string, config: AnimationConfig): Promise<AnimationInstance> {
    const intensitySettings = this.getVantaIntensitySettings(config.intensity || 'medium');
    
    const vantaConfig = {
      ...intensitySettings,
      color: hexToDecimal(BRAND_COLORS.primary),
      backgroundColor: hexToDecimal(BRAND_COLORS.white),
      ...config.customOptions
    };

    const vantaManager = createTopologyAnimation(config.element, vantaConfig);
    vantaManager.init();

    return {
      type: 'vanta-topology',
      instance: vantaManager,
      element: config.element,
      isActive: vantaManager.isActive(),
      destroy: () => vantaManager.destroy(),
      resize: () => vantaManager.resize(),
      updateConfig: (newConfig: Record<string, any>) => vantaManager.updateConfig(newConfig)
    };
  }

  /**
   * Initialize P5.js custom animation
   */
  private async initializeP5Animation(id: string, config: AnimationConfig): Promise<AnimationInstance> {
    const p5Config: P5AnimationConfig = {
      containerElement: config.element,
      backgroundColor: BRAND_COLORS.white,
      ...config.customOptions
    };

    // Create a basic sketch - can be customized via config.customOptions.sketch
    const sketch = config.customOptions?.sketch || ((p: any) => {
      p.setup = () => {
        const canvas = p.createCanvas(config.element.clientWidth, config.element.clientHeight);
        canvas.parent(config.element);
        p.background(BRAND_COLORS.white);
      };

      p.draw = () => {
        // Basic animation - override with custom sketch
        p.background(BRAND_COLORS.white);
        p.fill(BRAND_COLORS.primary);
        p.ellipse(p.mouseX || p.width/2, p.mouseY || p.height/2, 50, 50);
      };

      p.windowResized = () => {
        p.resizeCanvas(config.element.clientWidth, config.element.clientHeight);
      };
    });

    const p5Instance = createP5Instance(p5Config, sketch);

    return {
      type: 'p5-custom',
      instance: p5Instance,
      element: config.element,
      isActive: true,
      destroy: () => cleanupP5Instance(p5Instance),
      resize: () => p5Instance.windowResized?.(),
      updateConfig: () => {
        console.warn('P5.js configuration updates require recreation of the instance');
      }
    };
  }

  /**
   * Get VANTA intensity settings based on intensity level
   */
  private getVantaIntensitySettings(intensity: 'low' | 'medium' | 'high') {
    const baseSettings = {
      low: {
        points: P5Performance.isMobileDevice() ? 4 : 8,
        maxDistance: 10,
        spacing: 25,
        forceAnimate: false
      },
      medium: {
        points: P5Performance.isMobileDevice() ? 6 : 12,
        maxDistance: 15,
        spacing: 20,
        forceAnimate: false
      },
      high: {
        points: P5Performance.isMobileDevice() ? 8 : 16,
        maxDistance: 20,
        spacing: 15,
        forceAnimate: true
      }
    };

    return baseSettings[intensity];
  }

  /**
   * Destroy a specific animation
   */
  destroyAnimation(id: string): boolean {
    const animation = this.animations.get(id);
    if (animation) {
      animation.destroy();
      this.animations.delete(id);
      this.legacyPerformanceMonitor.stopMonitoring(id);
      // Stop enhanced performance monitoring
      globalPerformanceMonitor.stopMonitoring(id);
      console.log(`Animation ${id} destroyed`);
      return true;
    }
    return false;
  }

  /**
   * Destroy all animations
   */
  destroyAllAnimations(): void {
    this.animations.forEach((_, id) => {
      this.destroyAnimation(id);
    });
  }

  /**
   * Get animation instance by ID
   */
  getAnimation(id: string): AnimationInstance | undefined {
    return this.animations.get(id);
  }

  /**
   * Get all active animations
   */
  getAllAnimations(): Map<string, AnimationInstance> {
    return new Map(this.animations);
  }

  /**
   * Check if reduced motion is preferred
   */
  private shouldReduceMotion(): boolean {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * Set up global event listeners
   */
  private setupGlobalListeners(): void {
    if (typeof window === 'undefined') return;

    // Handle window resize
    let resizeTimeout: number;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = window.setTimeout(() => {
        this.animations.forEach(animation => {
          if (animation.isActive) {
            animation.resize();
          }
        });
      }, 250);
    });

    // Handle visibility change (pause animations when tab is hidden)
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.legacyPerformanceMonitor.pauseMonitoring();
        globalPerformanceMonitor.pauseAll();
      } else {
        this.legacyPerformanceMonitor.resumeMonitoring();
        globalPerformanceMonitor.resumeAll();
      }
    });

    // Handle reduced motion preference changes
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    mediaQuery.addEventListener('change', (e) => {
      if (e.matches) {
        // User now prefers reduced motion - destroy all animations
        console.log('Reduced motion preference detected - destroying animations');
        this.destroyAllAnimations();
      }
    });
  }
  
  /**
   * Setup global performance callbacks (T5.1)
   */
  private setupGlobalPerformanceCallbacks(): void {
    this.globalPerformanceCallbacks = {
      onPerformanceModeChange: (mode, metrics) => {
        console.log(`Global performance mode change: ${mode} (${metrics.averageFPS.toFixed(1)} FPS)`);
        
        // Auto-adjust performance for all animations if critical
        if (mode === 'critical') {
          this.handleCriticalPerformance(metrics);
        }
      },
      onPerformanceDrop: (metrics) => {
        console.warn(`Global performance drop detected: ${metrics.averageFPS.toFixed(1)} FPS`);
      },
      onHighMemoryUsage: (metrics) => {
        const memoryMB = metrics.memoryUsage ? Math.round(metrics.memoryUsage.usedJSHeapSize / 1024 / 1024) : 'unknown';
        console.warn(`High memory usage detected: ${memoryMB} MB`);
        
        // Consider reducing animation intensity
        this.handleHighMemoryUsage(metrics);
      }
    };
    
    globalPerformanceMonitor.setGlobalCallbacks(this.globalPerformanceCallbacks);
  }
  
  /**
   * Start enhanced performance monitoring for an animation (T5.1)
   */
  private startEnhancedPerformanceMonitoring(
    id: string, 
    animationInstance: AnimationInstance, 
    config: AnimationConfig
  ): void {
    const combinedCallbacks: PerformanceCallbacks = {
      ...this.globalPerformanceCallbacks,
      ...config.performanceCallbacks
    };
    
    const monitor = globalPerformanceMonitor.startMonitoring(
      id,
      config.performanceThresholds,
      combinedCallbacks
    );
    
    // Enhance animation instance with performance monitoring methods
    animationInstance.performanceMonitor = monitor;
    animationInstance.getPerformanceMetrics = () => globalPerformanceMonitor.getMetrics(id);
    animationInstance.startPerformanceMonitoring = (callbacks) => {
      const newCallbacks = { ...this.globalPerformanceCallbacks, ...callbacks };
      globalPerformanceMonitor.stopMonitoring(id);
      globalPerformanceMonitor.startMonitoring(id, config.performanceThresholds, newCallbacks);
    };
    animationInstance.stopPerformanceMonitoring = () => {
      globalPerformanceMonitor.stopMonitoring(id);
    };
    
    console.log(`Enhanced performance monitoring started for animation: ${id}`);
  }
  
  /**
   * Handle critical performance by reducing animation complexity
   */
  private handleCriticalPerformance(metrics: PerformanceMetrics): void {
    console.warn('Critical performance detected - considering animation adjustments');
    
    // In a real implementation, this could:
    // 1. Reduce particle counts
    // 2. Switch to lower performance modes
    // 3. Pause non-essential animations
    // 4. Switch to static backgrounds
    
    this.animations.forEach((animation, id) => {
      if (animation.type === 'vanta-topology') {
        console.log(`Considering performance reduction for animation: ${id}`);
        // Could implement automatic performance adjustment here
      }
    });
  }
  
  /**
   * Handle high memory usage
   */
  private handleHighMemoryUsage(metrics: PerformanceMetrics): void {
    console.warn('High memory usage detected - considering cleanup');
    
    // In a real implementation, this could:
    // 1. Force garbage collection (if available)
    // 2. Reduce texture quality
    // 3. Limit animation complexity
    // 4. Clean up unused resources
  }
  
  /**
   * Get aggregated performance metrics for all animations (T5.1)
   */
  getAggregatedPerformanceMetrics() {
    return globalPerformanceMonitor.getAggregatedMetrics();
  }
  
  /**
   * Get performance metrics for a specific animation (T5.1)
   */
  getAnimationPerformanceMetrics(id: string): PerformanceMetrics | null {
    return globalPerformanceMonitor.getMetrics(id);
  }
  
  /**
   * Enable performance monitoring for an existing animation (T5.1)
   */
  enablePerformanceMonitoring(
    id: string, 
    callbacks?: PerformanceCallbacks,
    thresholds?: Partial<PerformanceThresholds>
  ): boolean {
    const animation = this.animations.get(id);
    if (!animation) {
      console.warn(`Cannot enable performance monitoring: Animation ${id} not found`);
      return false;
    }
    
    const combinedCallbacks = { ...this.globalPerformanceCallbacks, ...callbacks };
    globalPerformanceMonitor.startMonitoring(id, thresholds, combinedCallbacks);
    
    // Add monitoring methods to animation instance
    animation.getPerformanceMetrics = () => globalPerformanceMonitor.getMetrics(id);
    animation.stopPerformanceMonitoring = () => globalPerformanceMonitor.stopMonitoring(id);
    
    console.log(`Performance monitoring enabled for animation: ${id}`);
    return true;
  }
  
  /**
   * Disable performance monitoring for an animation (T5.1)
   */
  disablePerformanceMonitoring(id: string): boolean {
    return globalPerformanceMonitor.stopMonitoring(id);
  }
}

/**
 * Legacy Performance monitoring for animations
 * @deprecated Use the enhanced PerformanceMonitor from performanceMonitor.ts instead
 */
class PerformanceMonitor {
  private monitoredAnimations: Map<string, {
    instance: AnimationInstance;
    startTime: number;
    frameCount: number;
    lastFPSCheck: number;
  }> = new Map();
  private monitoringActive = true;
  private monitoringInterval: number | null = null;

  startMonitoring(id: string, animation: AnimationInstance): void {
    this.monitoredAnimations.set(id, {
      instance: animation,
      startTime: Date.now(),
      frameCount: 0,
      lastFPSCheck: Date.now()
    });

    if (!this.monitoringInterval) {
      this.startPerformanceLoop();
    }
  }

  stopMonitoring(id: string): void {
    this.monitoredAnimations.delete(id);
    
    if (this.monitoredAnimations.size === 0 && this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  pauseMonitoring(): void {
    this.monitoringActive = false;
  }

  resumeMonitoring(): void {
    this.monitoringActive = true;
  }

  private startPerformanceLoop(): void {
    this.monitoringInterval = window.setInterval(() => {
      if (!this.monitoringActive) return;

      this.monitoredAnimations.forEach((monitor, id) => {
        const now = Date.now();
        const timeSinceLastCheck = now - monitor.lastFPSCheck;
        
        if (timeSinceLastCheck >= 2000) { // Check every 2 seconds
          // Basic performance check - more sophisticated monitoring can be added
          const memoryInfo = (performance as any).memory;
          if (memoryInfo && memoryInfo.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
            console.warn(`High memory usage detected for animation ${id}: ${Math.round(memoryInfo.usedJSHeapSize / 1024 / 1024)}MB`);
          }
          
          monitor.lastFPSCheck = now;
        }
      });
    }, 1000);
  }
}

// Global animation manager instance
export const globalAnimationManager = new AnimationManager();

/**
 * Convenience function to initialize animations
 */
export const initializeAnimation = (id: string, config: AnimationConfig): Promise<AnimationInstance | null> => {
  return globalAnimationManager.initializeAnimation(id, config);
};

/**
 * Convenience function to destroy animations
 */
export const destroyAnimation = (id: string): boolean => {
  return globalAnimationManager.destroyAnimation(id);
};

/**
 * Convenience function to get animation instance
 */
export const getAnimation = (id: string): AnimationInstance | undefined => {
  return globalAnimationManager.getAnimation(id);
};
