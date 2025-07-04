/**
 * Advanced Mobile Performance Monitor (T5.3)
 * 
 * Specialized performance monitoring for mobile devices with
 * touch interaction tracking, thermal management, and mobile-specific
 * performance optimizations.
 */

import type { MobileCapabilities } from './mobileDetection';

export interface MobilePerformanceMetrics {
  // Frame performance
  averageFPS: number;
  frameTimeVariance: number;
  droppedFrames: number;
  frameTimeConsistency: number;
  
  // Touch performance
  touchLatency: number;
  touchThroughput: number;
  touchAccuracy: number;
  scrollPerformance: number;
  
  // Thermal and power
  thermalState: 'normal' | 'fair' | 'serious' | 'critical' | 'unknown';
  cpuThrottling: boolean;
  batteryLevel?: number;
  batteryDrainRate?: number;
  
  // Memory and resources
  memoryUsage: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
    gpuMemoryUsage?: number;
  };
  
  // Network performance
  connectionQuality: 'fast' | 'medium' | 'slow';
  dataUsage: number;
  latency: number;
  
  // Animation performance
  animationFrameDrops: number;
  compositorFrames: number;
  paintTiming: number;
  layoutThrashing: number;
  
  // Mobile-specific metrics
  orientationChanges: number;
  backgroundEvents: number;
  interactionDelay: number;
  visualViewportChanges: number;
}

export interface MobilePerformanceCallbacks {
  onTouchLatencyHigh?: (latency: number) => void;
  onThermalThrottling?: (state: string) => void;
  onBatteryLow?: (level: number) => void;
  onMemoryPressure?: (usage: number) => void;
  onNetworkSlow?: (quality: string) => void;
  onPerformanceDrop?: (metrics: MobilePerformanceMetrics) => void;
  onFrameDrops?: (droppedFrames: number) => void;
  onOrientationChange?: (orientation: string) => void;
}

export interface MobilePerformanceThresholds {
  maxTouchLatency: number;
  minFPS: number;
  maxFrameDrops: number;
  maxMemoryUsage: number;
  minBatteryLevel: number;
  maxDataUsage: number;
  maxInteractionDelay: number;
}

/**
 * Advanced mobile performance monitor
 */
export class MobilePerformanceMonitor {
  private isMonitoring = false;
  private metrics: MobilePerformanceMetrics;
  private callbacks: MobilePerformanceCallbacks = {};
  private thresholds: MobilePerformanceThresholds;
  private mobileCapabilities: MobileCapabilities | null = null;
  
  // Performance tracking
  private frameCount = 0;
  private lastFrameTime = performance.now();
  private frameTimes: number[] = [];
  private touchEvents: number[] = [];
  private droppedFrames = 0;
  private animationFrameId?: number;
  
  // Touch tracking
  private touchStartTimes = new Map<number, number>();
  private touchLatencies: number[] = [];
  private lastTouchTime = 0;
  
  // Thermal tracking
  private thermalCheckInterval?: number;
  private lastThermalCheck = 0;
  
  // Network tracking
  private dataUsageStart = 0;
  private networkLatencies: number[] = [];
  
  // Battery tracking
  private batteryCheckInterval?: number;
  private lastBatteryLevel?: number;
  private batteryCheckTime = 0;
  
  // Orientation tracking
  private orientationChangeCount = 0;
  private lastOrientation = screen.orientation?.angle || 0;
  
  constructor(
    callbacks: MobilePerformanceCallbacks = {},
    thresholds: Partial<MobilePerformanceThresholds> = {}
  ) {
    this.callbacks = callbacks;
    this.thresholds = {
      maxTouchLatency: 50, // ms
      minFPS: 30,
      maxFrameDrops: 5,
      maxMemoryUsage: 0.8, // 80% of available
      minBatteryLevel: 0.15, // 15%
      maxDataUsage: 10 * 1024 * 1024, // 10MB per session
      maxInteractionDelay: 100, // ms
      ...thresholds
    };
    
    this.metrics = this.initializeMetrics();
    this.setupEventListeners();
  }
  
  /**
   * Initialize metrics with default values
   */
  private initializeMetrics(): MobilePerformanceMetrics {
    return {
      averageFPS: 0,
      frameTimeVariance: 0,
      droppedFrames: 0,
      frameTimeConsistency: 0,
      touchLatency: 0,
      touchThroughput: 0,
      touchAccuracy: 0,
      scrollPerformance: 0,
      thermalState: 'unknown',
      cpuThrottling: false,
      batteryLevel: undefined,
      batteryDrainRate: undefined,
      memoryUsage: {
        usedJSHeapSize: 0,
        totalJSHeapSize: 0,
        jsHeapSizeLimit: 0,
        gpuMemoryUsage: undefined
      },
      connectionQuality: 'medium',
      dataUsage: 0,
      latency: 0,
      animationFrameDrops: 0,
      compositorFrames: 0,
      paintTiming: 0,
      layoutThrashing: 0,
      orientationChanges: 0,
      backgroundEvents: 0,
      interactionDelay: 0,
      visualViewportChanges: 0
    };
  }
  
  /**
   * Setup mobile-specific event listeners
   */
  private setupEventListeners(): void {
    // Touch event tracking
    this.setupTouchTracking();
    
    // Orientation change tracking
    this.setupOrientationTracking();
    
    // Visibility change tracking
    this.setupVisibilityTracking();
    
    // Visual viewport tracking
    this.setupVisualViewportTracking();
    
    // Memory pressure tracking
    this.setupMemoryPressureTracking();
  }
  
  /**
   * Setup touch event tracking for latency measurement
   */
  private setupTouchTracking(): void {
    const touchStartHandler = (event: TouchEvent) => {
      const now = performance.now();
      for (let i = 0; i < event.changedTouches.length; i++) {
        const touch = event.changedTouches[i];
        this.touchStartTimes.set(touch.identifier, now);
      }
    };
    
    const touchEndHandler = (event: TouchEvent) => {
      const now = performance.now();
      for (let i = 0; i < event.changedTouches.length; i++) {
        const touch = event.changedTouches[i];
        const startTime = this.touchStartTimes.get(touch.identifier);
        if (startTime) {
          const latency = now - startTime;
          this.touchLatencies.push(latency);
          this.touchStartTimes.delete(touch.identifier);
          
          // Keep only recent latencies
          if (this.touchLatencies.length > 10) {
            this.touchLatencies.shift();
          }
          
          // Check threshold
          if (latency > this.thresholds.maxTouchLatency && this.callbacks.onTouchLatencyHigh) {
            this.callbacks.onTouchLatencyHigh(latency);
          }
        }
      }
      
      this.lastTouchTime = now;
    };
    
    const touchMoveHandler = (event: TouchEvent) => {
      const now = performance.now();
      const timeSinceLastTouch = now - this.lastTouchTime;
      
      // Track touch throughput
      if (timeSinceLastTouch > 0) {
        const throughput = 1000 / timeSinceLastTouch; // touches per second
        this.metrics.touchThroughput = throughput;
      }
    };
    
    // Use passive listeners for better scroll performance
    document.addEventListener('touchstart', touchStartHandler, { passive: true });
    document.addEventListener('touchend', touchEndHandler, { passive: true });
    document.addEventListener('touchmove', touchMoveHandler, { passive: true });
  }
  
  /**
   * Setup orientation change tracking
   */
  private setupOrientationTracking(): void {
    const orientationHandler = () => {
      this.orientationChangeCount++;
      this.metrics.orientationChanges = this.orientationChangeCount;
      
      if (this.callbacks.onOrientationChange) {
        const orientation = screen.orientation?.type || 'unknown';
        this.callbacks.onOrientationChange(orientation);
      }
    };
    
    if (screen.orientation) {
      screen.orientation.addEventListener('change', orientationHandler);
    } else {
      // Fallback for older browsers
      window.addEventListener('orientationchange', orientationHandler);
    }
  }
  
  /**
   * Setup visibility change tracking for background events
   */
  private setupVisibilityTracking(): void {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.metrics.backgroundEvents++;
      }
    });
  }
  
  /**
   * Setup visual viewport tracking for mobile UI changes
   */
  private setupVisualViewportTracking(): void {
    if ('visualViewport' in window) {
      let viewportChangeCount = 0;
      
      window.visualViewport?.addEventListener('resize', () => {
        viewportChangeCount++;
        this.metrics.visualViewportChanges = viewportChangeCount;
      });
    }
  }
  
  /**
   * Setup memory pressure tracking
   */
  private setupMemoryPressureTracking(): void {
    // Modern memory pressure API
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        if (memory) {
          this.metrics.memoryUsage = {
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit,
            gpuMemoryUsage: this.estimateGPUMemoryUsage()
          };
          
          const usageRatio = memory.usedJSHeapSize / memory.jsHeapSizeLimit;\n          if (usageRatio > this.thresholds.maxMemoryUsage && this.callbacks.onMemoryPressure) {\n            this.callbacks.onMemoryPressure(usageRatio);\n          }\n        }\n      }, 5000); // Check every 5 seconds\n    }\n  }\n  \n  /**\n   * Start mobile performance monitoring\n   */\n  async startMonitoring(mobileCapabilities: MobileCapabilities): Promise<void> {\n    if (this.isMonitoring) return;\n    \n    this.isMonitoring = true;\n    this.mobileCapabilities = mobileCapabilities;\n    \n    // Start frame performance monitoring\n    this.startFrameMonitoring();\n    \n    // Start thermal monitoring\n    this.startThermalMonitoring();\n    \n    // Start battery monitoring\n    await this.startBatteryMonitoring();\n    \n    // Start network monitoring\n    this.startNetworkMonitoring();\n    \n    console.log('Mobile performance monitoring started');\n  }\n  \n  /**\n   * Start frame performance monitoring\n   */\n  private startFrameMonitoring(): void {\n    const monitorFrame = (timestamp: number) => {\n      if (!this.isMonitoring) return;\n      \n      this.frameCount++;\n      const frameTime = timestamp - this.lastFrameTime;\n      this.frameTimes.push(frameTime);\n      \n      // Keep only recent frame times\n      if (this.frameTimes.length > 60) {\n        this.frameTimes.shift();\n      }\n      \n      // Calculate FPS\n      if (this.frameTimes.length > 1) {\n        const avgFrameTime = this.frameTimes.reduce((a, b) => a + b) / this.frameTimes.length;\n        this.metrics.averageFPS = 1000 / avgFrameTime;\n        \n        // Calculate frame time variance for consistency measurement\n        const variance = this.frameTimes.reduce((acc, time) => {\n          return acc + Math.pow(time - avgFrameTime, 2);\n        }, 0) / this.frameTimes.length;\n        \n        this.metrics.frameTimeVariance = variance;\n        this.metrics.frameTimeConsistency = 1 / (1 + variance / 100); // Normalized consistency score\n      }\n      \n      // Detect dropped frames (frame time > 33ms for 30fps)\n      if (frameTime > 33.33) {\n        this.droppedFrames++;\n        this.metrics.droppedFrames = this.droppedFrames;\n        \n        if (this.droppedFrames > this.thresholds.maxFrameDrops && this.callbacks.onFrameDrops) {\n          this.callbacks.onFrameDrops(this.droppedFrames);\n        }\n      }\n      \n      // Check performance thresholds\n      if (this.metrics.averageFPS < this.thresholds.minFPS && this.callbacks.onPerformanceDrop) {\n        this.callbacks.onPerformanceDrop(this.metrics);\n      }\n      \n      this.lastFrameTime = timestamp;\n      this.animationFrameId = requestAnimationFrame(monitorFrame);\n    };\n    \n    this.animationFrameId = requestAnimationFrame(monitorFrame);\n  }\n  \n  /**\n   * Start thermal monitoring\n   */\n  private startThermalMonitoring(): void {\n    const checkThermalState = () => {\n      try {\n        if ('thermal' in navigator) {\n          const thermal = (navigator as any).thermal;\n          if (thermal && thermal.state) {\n            this.metrics.thermalState = thermal.state;\n            \n            if (thermal.state !== 'normal' && this.callbacks.onThermalThrottling) {\n              this.callbacks.onThermalThrottling(thermal.state);\n            }\n          }\n        }\n        \n        // Infer thermal state from performance degradation\n        if (this.metrics.averageFPS > 0 && this.frameCount > 60) {\n          const recentFPS = this.frameTimes.slice(-10).reduce((acc, time) => acc + (1000 / time), 0) / 10;\n          const fpsDropRatio = recentFPS / this.metrics.averageFPS;\n          \n          if (fpsDropRatio < 0.7) {\n            this.metrics.cpuThrottling = true;\n            if (this.callbacks.onThermalThrottling) {\n              this.callbacks.onThermalThrottling('inferred');\n            }\n          }\n        }\n      } catch (error) {\n        // Thermal API not available\n      }\n    };\n    \n    // Check thermal state every 10 seconds\n    this.thermalCheckInterval = window.setInterval(checkThermalState, 10000);\n  }\n  \n  /**\n   * Start battery monitoring\n   */\n  private async startBatteryMonitoring(): Promise<void> {\n    try {\n      if ('getBattery' in navigator) {\n        const battery = await (navigator as any).getBattery();\n        \n        const updateBatteryMetrics = () => {\n          const currentLevel = battery.level;\n          const currentTime = Date.now();\n          \n          this.metrics.batteryLevel = currentLevel;\n          \n          // Calculate battery drain rate\n          if (this.lastBatteryLevel !== undefined && this.batteryCheckTime > 0) {\n            const levelChange = this.lastBatteryLevel - currentLevel;\n            const timeChange = (currentTime - this.batteryCheckTime) / 1000 / 60; // minutes\n            \n            if (timeChange > 0 && levelChange > 0) {\n              this.metrics.batteryDrainRate = levelChange / timeChange; // % per minute\n            }\n          }\n          \n          this.lastBatteryLevel = currentLevel;\n          this.batteryCheckTime = currentTime;\n          \n          // Check low battery threshold\n          if (currentLevel < this.thresholds.minBatteryLevel && this.callbacks.onBatteryLow) {\n            this.callbacks.onBatteryLow(currentLevel);\n          }\n        };\n        \n        // Initial check\n        updateBatteryMetrics();\n        \n        // Monitor battery events\n        battery.addEventListener('levelchange', updateBatteryMetrics);\n        battery.addEventListener('chargingchange', updateBatteryMetrics);\n        \n        // Periodic check\n        this.batteryCheckInterval = window.setInterval(updateBatteryMetrics, 30000); // Every 30 seconds\n      }\n    } catch (error) {\n      // Battery API not available\n    }\n  }\n  \n  /**\n   * Start network monitoring\n   */\n  private startNetworkMonitoring(): void {\n    if ('connection' in navigator) {\n      const updateNetworkMetrics = () => {\n        const connection = (navigator as any).connection;\n        if (connection) {\n          const { effectiveType, downlink, rtt } = connection;\n          \n          // Update connection quality\n          if (effectiveType === '4g' && downlink > 5) {\n            this.metrics.connectionQuality = 'fast';\n          } else if (effectiveType === '4g' || (effectiveType === '3g' && downlink > 1)) {\n            this.metrics.connectionQuality = 'medium';\n          } else {\n            this.metrics.connectionQuality = 'slow';\n          }\n          \n          this.metrics.latency = rtt || 0;\n          \n          // Check slow network threshold\n          if (this.metrics.connectionQuality === 'slow' && this.callbacks.onNetworkSlow) {\n            this.callbacks.onNetworkSlow(this.metrics.connectionQuality);\n          }\n        }\n      };\n      \n      // Initial check\n      updateNetworkMetrics();\n      \n      // Monitor network changes\n      const connection = (navigator as any).connection;\n      if (connection) {\n        connection.addEventListener('change', updateNetworkMetrics);\n      }\n    }\n  }\n  \n  /**\n   * Estimate GPU memory usage (approximation)\n   */\n  private estimateGPUMemoryUsage(): number | undefined {\n    if (!this.mobileCapabilities?.gpuMemoryMB) return undefined;\n    \n    // Rough estimation based on frame complexity and texture usage\n    const baseUsage = 50; // MB base usage\n    const frameComplexity = Math.max(0, (60 - this.metrics.averageFPS) / 60); // 0-1 scale\n    const complexityUsage = frameComplexity * 200; // Additional usage based on complexity\n    \n    return Math.min(baseUsage + complexityUsage, this.mobileCapabilities.gpuMemoryMB);\n  }\n  \n  /**\n   * Calculate touch accuracy based on target hitting\n   */\n  measureTouchAccuracy(targetElement: HTMLElement, touchEvent: TouchEvent): void {\n    const touch = touchEvent.touches[0];\n    if (!touch) return;\n    \n    const rect = targetElement.getBoundingClientRect();\n    const touchX = touch.clientX;\n    const touchY = touch.clientY;\n    \n    const centerX = rect.left + rect.width / 2;\n    const centerY = rect.top + rect.height / 2;\n    \n    const distance = Math.sqrt(\n      Math.pow(touchX - centerX, 2) + Math.pow(touchY - centerY, 2)\n    );\n    \n    const maxDistance = Math.sqrt(Math.pow(rect.width / 2, 2) + Math.pow(rect.height / 2, 2));\n    const accuracy = Math.max(0, 1 - (distance / maxDistance));\n    \n    this.metrics.touchAccuracy = accuracy;\n  }\n  \n  /**\n   * Measure scroll performance\n   */\n  measureScrollPerformance(scrollEvent: Event): void {\n    const now = performance.now();\n    const timeSinceLastFrame = now - this.lastFrameTime;\n    \n    // Calculate scroll smoothness (lower is better)\n    const scrollSmoothness = Math.max(0, 1 - (timeSinceLastFrame / 16.67)); // Target 60fps\n    this.metrics.scrollPerformance = scrollSmoothness;\n  }\n  \n  /**\n   * Measure interaction delay\n   */\n  measureInteractionDelay(interactionStart: number): void {\n    const delay = performance.now() - interactionStart;\n    this.metrics.interactionDelay = delay;\n    \n    if (delay > this.thresholds.maxInteractionDelay && this.callbacks.onTouchLatencyHigh) {\n      this.callbacks.onTouchLatencyHigh(delay);\n    }\n  }\n  \n  /**\n   * Get current metrics\n   */\n  getMetrics(): MobilePerformanceMetrics {\n    // Update touch latency from recent measurements\n    if (this.touchLatencies.length > 0) {\n      this.metrics.touchLatency = this.touchLatencies.reduce((a, b) => a + b) / this.touchLatencies.length;\n    }\n    \n    return { ...this.metrics };\n  }\n  \n  /**\n   * Get mobile-specific performance insights\n   */\n  getPerformanceInsights(): {\n    isPerformingWell: boolean;\n    recommendations: string[];\n    criticalIssues: string[];\n  } {\n    const metrics = this.getMetrics();\n    const recommendations: string[] = [];\n    const criticalIssues: string[] = [];\n    \n    // Analyze FPS performance\n    if (metrics.averageFPS < 20) {\n      criticalIssues.push('Very low frame rate detected');\n      recommendations.push('Reduce animation complexity');\n    } else if (metrics.averageFPS < 30) {\n      recommendations.push('Consider reducing particle count for better performance');\n    }\n    \n    // Analyze touch latency\n    if (metrics.touchLatency > 100) {\n      criticalIssues.push('High touch latency detected');\n      recommendations.push('Optimize touch event handlers');\n    } else if (metrics.touchLatency > 50) {\n      recommendations.push('Touch responsiveness could be improved');\n    }\n    \n    // Analyze thermal state\n    if (metrics.thermalState === 'critical') {\n      criticalIssues.push('Device is overheating');\n      recommendations.push('Reduce animation intensity immediately');\n    } else if (metrics.thermalState === 'serious') {\n      recommendations.push('Consider reducing performance to prevent overheating');\n    }\n    \n    // Analyze battery\n    if (metrics.batteryLevel !== undefined && metrics.batteryLevel < 0.15) {\n      recommendations.push('Enable battery saving mode');\n    }\n    \n    // Analyze memory usage\n    const memoryRatio = metrics.memoryUsage.usedJSHeapSize / metrics.memoryUsage.jsHeapSizeLimit;\n    if (memoryRatio > 0.9) {\n      criticalIssues.push('High memory usage detected');\n      recommendations.push('Reduce memory-intensive animations');\n    } else if (memoryRatio > 0.7) {\n      recommendations.push('Monitor memory usage closely');\n    }\n    \n    // Analyze network\n    if (metrics.connectionQuality === 'slow') {\n      recommendations.push('Reduce network-dependent features');\n    }\n    \n    const isPerformingWell = criticalIssues.length === 0 && \n                            metrics.averageFPS >= 30 && \n                            metrics.touchLatency < 50;\n    \n    return {\n      isPerformingWell,\n      recommendations,\n      criticalIssues\n    };\n  }\n  \n  /**\n   * Stop monitoring\n   */\n  stopMonitoring(): void {\n    this.isMonitoring = false;\n    \n    if (this.animationFrameId) {\n      cancelAnimationFrame(this.animationFrameId);\n    }\n    \n    if (this.thermalCheckInterval) {\n      clearInterval(this.thermalCheckInterval);\n    }\n    \n    if (this.batteryCheckInterval) {\n      clearInterval(this.batteryCheckInterval);\n    }\n    \n    console.log('Mobile performance monitoring stopped');\n  }\n  \n  /**\n   * Reset metrics\n   */\n  resetMetrics(): void {\n    this.metrics = this.initializeMetrics();\n    this.frameCount = 0;\n    this.frameTimes = [];\n    this.touchLatencies = [];\n    this.droppedFrames = 0;\n    this.orientationChangeCount = 0;\n  }\n}\n\n/**\n * Create mobile performance monitor with default settings\n */\nexport const createMobilePerformanceMonitor = (\n  callbacks: MobilePerformanceCallbacks = {},\n  thresholds: Partial<MobilePerformanceThresholds> = {}\n): MobilePerformanceMonitor => {\n  return new MobilePerformanceMonitor(callbacks, thresholds);\n};