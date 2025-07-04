/**
 * Fallback Animation Manager
 * 
 * Intelligently manages animation fallbacks based on browser capabilities,
 * performance monitoring, and user preferences
 */

import { detectBrowser, runCompatibilityTest, type BrowserCompatibility } from './browserCompatibility';
import { loadPolyfills, type PolyfillStatus } from './polyfills';
import { detectMobileCapabilities, applyMobileOptimizations, type MobileCapabilities } from './mobileOptimizations';
import { applyBrowserOptimizations } from './browserOptimizations';

export type AnimationLevel = 'none' | 'minimal' | 'reduced' | 'standard' | 'enhanced';
export type FallbackStrategy = 'auto' | 'force-webgl' | 'force-css' | 'force-static';

export interface FallbackConfig {
  strategy: FallbackStrategy;
  minCompatibilityScore: number;
  minFPS: number;
  maxMemoryUsage: number; // MB
  enableAdaptiveQuality: boolean;
  enablePerformanceMonitoring: boolean;
  fallbackTimeout: number; // ms
  debug: boolean;
}

export interface AnimationCapabilities {
  level: AnimationLevel;
  supportsWebGL: boolean;
  supportsCSS: boolean;
  supportsParticles: boolean;
  supportsComplexGradients: boolean;
  supportsBackdropFilter: boolean;
  maxParticleCount: number;
  recommendedFPS: number;
  shouldUseReducedMotion: boolean;
}

export interface FallbackDecision {
  animationType: 'webgl' | 'css-animated' | 'css-static' | 'none';
  animationLevel: AnimationLevel;
  reason: string;
  capabilities: AnimationCapabilities;
  compatibility: BrowserCompatibility;
  polyfillStatus: PolyfillStatus;
  mobileCapabilities?: MobileCapabilities;
}

let currentDecision: FallbackDecision | null = null;
let performanceMonitorActive = false;
let adaptiveQualityEnabled = false;

/**
 * Main fallback manager class
 */
export class FallbackManager {
  private config: FallbackConfig;
  private compatibility: BrowserCompatibility | null = null;
  private polyfillStatus: PolyfillStatus | null = null;
  private performanceHistory: Array<{ fps: number; memory: number; timestamp: number }> = [];

  constructor(config: Partial<FallbackConfig> = {}) {
    this.config = {
      strategy: 'auto',
      minCompatibilityScore: 70,
      minFPS: 30,
      maxMemoryUsage: 100, // 100MB
      enableAdaptiveQuality: true,
      enablePerformanceMonitoring: true,
      fallbackTimeout: 5000,
      debug: false,
      ...config,
    };
  }

  /**
   * Initialize the fallback manager and make animation decision
   */
  async initialize(): Promise<FallbackDecision> {
    if (this.config.debug) {
      console.log('Initializing fallback manager with config:', this.config);
    }

    // Run compatibility test
    this.compatibility = runCompatibilityTest();
    
    // Load necessary polyfills
    this.polyfillStatus = await loadPolyfills({
      debug: this.config.debug,
    });

    // Detect mobile capabilities
    const mobileCapabilities = await detectMobileCapabilities();

    // Apply browser optimizations
    await applyBrowserOptimizations({
      debug: this.config.debug,
    });

    // Apply mobile optimizations if on mobile device
    if (mobileCapabilities.isMobile || mobileCapabilities.isTablet) {
      await applyMobileOptimizations({
        debug: this.config.debug,
        aggressivePowerSaving: mobileCapabilities.isLowEndDevice,
      });
    }

    // Make initial decision
    const decision = this.makeAnimationDecision(mobileCapabilities);
    currentDecision = decision;

    // Start performance monitoring if enabled
    if (this.config.enablePerformanceMonitoring) {
      this.startPerformanceMonitoring();
    }

    // Enable adaptive quality if configured
    if (this.config.enableAdaptiveQuality) {
      adaptiveQualityEnabled = true;
    }

    if (this.config.debug) {
      console.log('Fallback decision:', decision);
    }

    return decision;
  }

  /**
   * Make animation decision based on capabilities and strategy
   */
  private makeAnimationDecision(mobileCapabilities?: MobileCapabilities): FallbackDecision {
    if (!this.compatibility || !this.polyfillStatus) {
      throw new Error('Fallback manager not initialized');
    }

    const capabilities = this.analyzeCapabilities(mobileCapabilities);
    let animationType: FallbackDecision['animationType'] = 'none';
    let reason = '';

    // Apply fallback strategy
    switch (this.config.strategy) {
      case 'force-webgl':
        if (capabilities.supportsWebGL) {
          animationType = 'webgl';
          reason = 'Forced WebGL strategy';
        } else {
          animationType = 'css-animated';
          reason = 'WebGL not supported, fallback to CSS';
        }
        break;

      case 'force-css':
        animationType = capabilities.supportsCSS ? 'css-animated' : 'css-static';
        reason = 'Forced CSS strategy';
        break;

      case 'force-static':
        animationType = 'css-static';
        reason = 'Forced static strategy';
        break;

      case 'auto':
      default:
        const decision = this.makeAutomaticDecision(capabilities, mobileCapabilities);
        animationType = decision.type;
        reason = decision.reason;
        break;
    }

    // Override if reduced motion is preferred
    if (capabilities.shouldUseReducedMotion) {
      if (animationType === 'webgl' || animationType === 'css-animated') {
        animationType = 'css-static';
        reason += ' (reduced motion preferred)';
      }
    }

    return {
      animationType,
      animationLevel: capabilities.level,
      reason,
      capabilities,
      compatibility: this.compatibility,
      polyfillStatus: this.polyfillStatus,
      mobileCapabilities,
    };
  }

  /**
   * Make automatic decision based on capabilities
   */
  private makeAutomaticDecision(
    capabilities: AnimationCapabilities,
    mobileCapabilities?: MobileCapabilities
  ): { type: FallbackDecision['animationType'], reason: string } {
    const score = this.compatibility!.score;
    const browser = this.compatibility!.browser;

    // Mobile-specific decision logic
    if (mobileCapabilities?.isMobile || mobileCapabilities?.isTablet) {
      return this.makeMobileDecision(capabilities, mobileCapabilities, score);
    }

    // Desktop decision logic
    // High-end devices with excellent compatibility
    if (score >= 90 && capabilities.supportsWebGL) {
      return { type: 'webgl', reason: 'Excellent compatibility, high-end desktop device' };
    }

    // Good compatibility but medium-performance device
    if (score >= this.config.minCompatibilityScore && capabilities.supportsWebGL) {
      return { type: 'webgl', reason: 'Good compatibility, WebGL supported' };
    }

    // Moderate compatibility, prefer CSS animations
    if (score >= 50 && capabilities.supportsCSS) {
      return { type: 'css-animated', reason: 'Moderate compatibility, CSS animations preferred' };
    }

    // Poor compatibility, use static backgrounds
    if (score >= 30) {
      return { type: 'css-static', reason: 'Poor compatibility, using static patterns' };
    }

    // Very poor compatibility
    return { type: 'none', reason: 'Very poor browser compatibility' };
  }

  /**
   * Make mobile-specific animation decision
   */
  private makeMobileDecision(
    capabilities: AnimationCapabilities,
    mobileCapabilities: MobileCapabilities,
    score: number
  ): { type: FallbackDecision['animationType'], reason: string } {
    const { isLowEndDevice, platform, deviceMemory, connectionType, reducedData } = mobileCapabilities;

    // Low-end device or poor network - use static only
    if (isLowEndDevice || connectionType === 'slow-2g' || connectionType === '2g' || reducedData) {
      return { type: 'css-static', reason: 'Low-end device or poor network connection' };
    }

    // High-end mobile devices with good compatibility
    if (score >= 85 && capabilities.supportsWebGL && deviceMemory >= 6) {
      if (platform === 'ios') {
        // iOS Safari has good WebGL support on newer devices
        return { type: 'webgl', reason: 'High-end iOS device with good WebGL support' };
      } else if (platform === 'android' && deviceMemory >= 8) {
        // High-end Android devices
        return { type: 'webgl', reason: 'High-end Android device with sufficient memory' };
      }
    }

    // Medium performance mobile devices
    if (score >= this.config.minCompatibilityScore && capabilities.supportsCSS) {
      if (deviceMemory >= 4) {
        return { type: 'css-animated', reason: 'Medium performance mobile device, using CSS animations' };
      } else {
        return { type: 'css-static', reason: 'Limited memory mobile device' };
      }
    }

    // Low performance mobile devices
    if (score >= 40 && capabilities.supportsCSS) {
      return { type: 'css-static', reason: 'Low performance mobile device' };
    }

    // Very poor mobile compatibility
    return { type: 'none', reason: 'Very poor mobile browser compatibility' };
  }

  /**
   * Analyze browser capabilities and determine animation level
   */
  private analyzeCapabilities(mobileCapabilities?: MobileCapabilities): AnimationCapabilities {
    if (!this.compatibility) {
      throw new Error('Compatibility not available');
    }

    const { browser, features, score } = this.compatibility;
    
    // Determine reduced motion preference
    let shouldUseReducedMotion = false;
    try {
      // This will be overridden by the actual hook in components
      shouldUseReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch {}

    // Base capabilities
    const supportsWebGL = features.webgl && score >= this.config.minCompatibilityScore;
    const supportsCSS = features.css.animations && features.css.transitions;
    const supportsParticles = features.webgl || features.css.animations;
    const supportsComplexGradients = features.css.backdropFilter || features.webgl;
    const supportsBackdropFilter = features.css.backdropFilter;

    // Determine animation level with mobile considerations
    let level: AnimationLevel = 'none';
    let maxParticleCount = 0;
    let recommendedFPS = 30;

    if (shouldUseReducedMotion) {
      level = 'none';
    } else if (mobileCapabilities) {
      // Use mobile-specific settings
      const settings = mobileCapabilities.recommendedSettings;
      maxParticleCount = settings.maxParticles;
      recommendedFPS = settings.maxFPS;
      
      if (settings.enableWebGL && supportsWebGL && score >= 85) {
        level = 'enhanced';
      } else if (settings.enableComplexAnimations && supportsCSS && score >= 70) {
        level = 'standard';
      } else if (supportsCSS && score >= 50) {
        level = 'reduced';
      } else if (score >= 30) {
        level = 'minimal';
      }
    } else {
      // Desktop capabilities
      if (score >= 90 && supportsWebGL) {
        level = 'enhanced';
        maxParticleCount = 100;
        recommendedFPS = 60;
      } else if (score >= 70 && supportsWebGL) {
        level = 'standard';
        maxParticleCount = 60;
        recommendedFPS = 60;
      } else if (score >= 50 && supportsCSS) {
        level = 'reduced';
        maxParticleCount = 20;
        recommendedFPS = 30;
      } else if (score >= 30) {
        level = 'minimal';
        maxParticleCount = 10;
        recommendedFPS = 30;
      }
    }

    return {
      level,
      supportsWebGL,
      supportsCSS,
      supportsParticles,
      supportsComplexGradients,
      supportsBackdropFilter,
      maxParticleCount,
      recommendedFPS,
      shouldUseReducedMotion,
    };
  }

  /**
   * Start performance monitoring to adapt quality
   */
  private startPerformanceMonitoring(): void {
    if (performanceMonitorActive) return;
    
    performanceMonitorActive = true;
    
    const monitorPerformance = () => {
      if (!performanceMonitorActive) return;

      // Simple FPS measurement
      let frameCount = 0;
      let startTime = performance.now();
      
      const measureFrame = (currentTime: number) => {
        frameCount++;
        
        if (currentTime - startTime >= 1000) {
          const fps = frameCount;
          const memory = 'memory' in performance ? (performance as any).memory.usedJSHeapSize / (1024 * 1024) : 0;
          
          this.performanceHistory.push({
            fps,
            memory,
            timestamp: currentTime,
          });

          // Keep only last 10 measurements
          if (this.performanceHistory.length > 10) {
            this.performanceHistory.shift();
          }

          // Check if adaptation is needed
          if (adaptiveQualityEnabled) {
            this.adaptQualityIfNeeded(fps, memory);
          }

          frameCount = 0;
          startTime = currentTime;
        }

        if (performanceMonitorActive) {
          requestAnimationFrame(measureFrame);
        }
      };

      requestAnimationFrame(measureFrame);
    };

    // Start monitoring after a delay to let animations stabilize
    setTimeout(monitorPerformance, 2000);
  }

  /**
   * Adapt animation quality based on performance
   */
  private adaptQualityIfNeeded(fps: number, memory: number): void {
    if (!currentDecision) return;

    const needsDowngrade = fps < this.config.minFPS || memory > this.config.maxMemoryUsage;
    const canUpgrade = fps > this.config.minFPS * 1.5 && memory < this.config.maxMemoryUsage * 0.5;

    if (needsDowngrade && currentDecision.animationType === 'webgl') {
      if (this.config.debug) {
        console.log('Performance degraded, switching to CSS animations', { fps, memory });
      }
      
      // Trigger fallback to CSS
      this.triggerFallback('css-animated', 'Performance degradation detected');
      
    } else if (canUpgrade && currentDecision.animationType === 'css-animated' && 
               currentDecision.capabilities.supportsWebGL) {
      if (this.config.debug) {
        console.log('Performance improved, considering WebGL upgrade', { fps, memory });
      }
      
      // Could potentially upgrade back to WebGL, but be conservative
      // This would require more sophisticated logic to avoid oscillation
    }
  }

  /**
   * Trigger a fallback to a different animation type
   */
  triggerFallback(newType: FallbackDecision['animationType'], reason: string): void {
    if (!currentDecision) return;

    const previousType = currentDecision.animationType;
    currentDecision.animationType = newType;
    currentDecision.reason = `${currentDecision.reason} → ${reason}`;

    if (this.config.debug) {
      console.log(`Animation fallback: ${previousType} → ${newType}`, reason);
    }

    // Dispatch custom event for components to react
    window.dispatchEvent(new CustomEvent('animation-fallback', {
      detail: {
        previousType,
        newType,
        reason,
        decision: currentDecision,
      },
    }));
  }

  /**
   * Stop performance monitoring
   */
  stopPerformanceMonitoring(): void {
    performanceMonitorActive = false;
  }

  /**
   * Get current decision
   */
  getCurrentDecision(): FallbackDecision | null {
    return currentDecision;
  }

  /**
   * Get performance history
   */
  getPerformanceHistory(): Array<{ fps: number; memory: number; timestamp: number }> {
    return [...this.performanceHistory];
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<FallbackConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    if (this.config.debug) {
      console.log('Fallback manager config updated:', this.config);
    }
  }
}

/**
 * Global fallback manager instance
 */
let globalFallbackManager: FallbackManager | null = null;

/**
 * Initialize global fallback manager
 */
export async function initializeFallbackManager(config?: Partial<FallbackConfig>): Promise<FallbackDecision> {
  globalFallbackManager = new FallbackManager(config);
  return await globalFallbackManager.initialize();
}

/**
 * Get current fallback decision
 */
export function getCurrentFallbackDecision(): FallbackDecision | null {
  return currentDecision;
}

/**
 * Get global fallback manager
 */
export function getFallbackManager(): FallbackManager | null {
  return globalFallbackManager;
}

/**
 * Utility function to determine if WebGL should be used
 */
export function shouldUseWebGL(): boolean {
  return currentDecision?.animationType === 'webgl';
}

/**
 * Utility function to determine if CSS animations should be used
 */
export function shouldUseCSSAnimations(): boolean {
  return currentDecision?.animationType === 'css-animated';
}

/**
 * Utility function to determine if static backgrounds should be used
 */
export function shouldUseStaticBackground(): boolean {
  return currentDecision?.animationType === 'css-static';
}

/**
 * Get recommended animation settings based on current decision
 */
export function getRecommendedAnimationSettings(): {
  particleCount: number;
  animationSpeed: number;
  quality: 'low' | 'medium' | 'high';
  enableBlur: boolean;
  enableComplexEffects: boolean;
} {
  if (!currentDecision) {
    return {
      particleCount: 0,
      animationSpeed: 0,
      quality: 'low',
      enableBlur: false,
      enableComplexEffects: false,
    };
  }

  const { capabilities, animationLevel } = currentDecision;

  return {
    particleCount: capabilities.maxParticleCount,
    animationSpeed: capabilities.recommendedFPS / 60,
    quality: animationLevel === 'enhanced' ? 'high' : animationLevel === 'standard' ? 'medium' : 'low',
    enableBlur: capabilities.supportsBackdropFilter,
    enableComplexEffects: capabilities.supportsComplexGradients && animationLevel !== 'minimal',
  };
}

export default FallbackManager;