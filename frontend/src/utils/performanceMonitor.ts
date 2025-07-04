/**
 * Real-time Performance Monitor
 * 
 * Provides continuous monitoring of animation performance
 * to maintain 60fps on desktop and 30fps minimum on mobile.
 */

export interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  memoryUsage: number;
  cpuUsage: number;
  frameDrops: number;
  timestamp: number;
  // Motion preference awareness
  motionPreference?: 'no-preference' | 'reduce';
  animationCount?: number;
  reducedMotionCompliance?: number; // Percentage of animations respecting motion preference
}

export interface PerformanceThresholds {
  targetFPS: number;
  minFPS: number;
  maxFrameTime: number;
  maxMemoryMB: number;
  maxFrameDrops: number;
}

export interface PerformanceAlert {
  id: string;
  type: 'warning' | 'critical';
  message: string;
  metrics: PerformanceMetrics;
  timestamp: number;
  resolved?: boolean;
}

export interface PerformanceReport {
  summary: {
    averageFPS: number;
    minFPS: number;
    maxFPS: number;
    averageFrameTime: number;
    totalFrameDrops: number;
    memoryPeak: number;
    testDuration: number;
    // Motion preference metrics
    motionPreference?: 'no-preference' | 'reduce';
    averageAnimationCount?: number;
    reducedMotionComplianceScore?: number;
    accessibilityScore?: number;
  };
  alerts: PerformanceAlert[];
  recommendations: string[];
  deviceInfo: any;
  timestamp: number;
}

/**
 * Real-time Performance Monitor
 */
export class RealTimePerformanceMonitor {
  private isMonitoring: boolean = false;
  private frameMetrics: PerformanceMetrics[] = [];
  private alerts: PerformanceAlert[] = [];
  private thresholds: PerformanceThresholds;
  private callbacks: {
    onMetrics?: (metrics: PerformanceMetrics) => void;
    onAlert?: (alert: PerformanceAlert) => void;
    onReport?: (report: PerformanceReport) => void;
  } = {};
  
  private lastFrameTime: number = 0;
  private frameCount: number = 0;
  private monitoringStartTime: number = 0;
  private animationFrame: number | null = null;
  private reportInterval: number | null = null;
  
  // Motion preference tracking
  private motionPreference: 'no-preference' | 'reduce' = 'no-preference';
  private animationElements: Set<Element> = new Set();
  private motionObserver: MutationObserver | null = null;
  
  constructor(
    thresholds?: Partial<PerformanceThresholds>,
    callbacks?: {
      onMetrics?: (metrics: PerformanceMetrics) => void;
      onAlert?: (alert: PerformanceAlert) => void;
      onReport?: (report: PerformanceReport) => void;
    }
  ) {
    // Set device-appropriate thresholds
    const deviceType = this.getDeviceType();
    this.thresholds = {
      targetFPS: deviceType === 'mobile' ? 30 : deviceType === 'tablet' ? 45 : 60,
      minFPS: deviceType === 'mobile' ? 25 : deviceType === 'tablet' ? 35 : 50,
      maxFrameTime: deviceType === 'mobile' ? 33.33 : deviceType === 'tablet' ? 22.22 : 16.67, // ms
      maxMemoryMB: deviceType === 'mobile' ? 256 : 512,
      maxFrameDrops: 10,
      ...thresholds,
    };
    
    this.callbacks = callbacks || {};
    
    // Initialize motion preference detection
    this.detectMotionPreference();
    
    // Bind methods
    this.measureFrame = this.measureFrame.bind(this);
  }
  
  /**
   * Detect user's motion preference
   */
  private detectMotionPreference(): void {
    if (typeof window === 'undefined') return;
    
    try {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      this.motionPreference = mediaQuery.matches ? 'reduce' : 'no-preference';
      
      // Listen for changes
      const updatePreference = () => {
        this.motionPreference = mediaQuery.matches ? 'reduce' : 'no-preference';
        console.log(`🎭 Motion preference changed to: ${this.motionPreference}`);
      };
      
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', updatePreference);
      } else if (mediaQuery.addListener) {
        mediaQuery.addListener(updatePreference);
      }
    } catch (error) {
      console.warn('Error detecting motion preference:', error);
    }
  }
  
  /**
   * Start tracking animation elements
   */
  private startAnimationTracking(): void {
    if (typeof document === 'undefined') return;
    
    // Initial scan for animation elements
    this.scanForAnimations();
    
    // Set up mutation observer to track new animations
    this.motionObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              this.scanElementForAnimations(node as Element);
            }
          });
        } else if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          if (mutation.target.nodeType === Node.ELEMENT_NODE) {
            this.scanElementForAnimations(mutation.target as Element);
          }
        }
      });
    });
    
    this.motionObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'style']
    });
  }
  
  /**
   * Scan for animation elements in the DOM
   */
  private scanForAnimations(): void {
    if (typeof document === 'undefined') return;
    
    // Look for elements with animation classes
    const animationSelectors = [
      '[class*="animate-"]',
      '[class*="transition-"]',
      '[style*="animation"]',
      '[style*="transition"]',
      '[data-motion-preference]'
    ];
    
    animationSelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        this.animationElements.add(element);
      });
    });
  }
  
  /**
   * Scan a specific element for animations
   */
  private scanElementForAnimations(element: Element): void {
    const classList = element.className;
    const style = element.getAttribute('style') || '';
    
    if (classList.includes('animate-') || 
        classList.includes('transition-') || 
        style.includes('animation') || 
        style.includes('transition') ||
        element.hasAttribute('data-motion-preference')) {
      this.animationElements.add(element);
    }
    
    // Scan children
    element.querySelectorAll('[class*="animate-"], [class*="transition-"], [style*="animation"], [style*="transition"]').forEach(child => {
      this.animationElements.add(child);
    });
  }
  
  /**
   * Calculate reduced motion compliance
   */
  private calculateReducedMotionCompliance(): number {
    if (this.animationElements.size === 0) return 100;
    
    let compliantElements = 0;
    
    this.animationElements.forEach(element => {
      const motionPreference = element.getAttribute('data-motion-preference');
      const classList = element.className;
      
      // Check if element respects motion preferences
      if (this.motionPreference === 'reduce') {
        if (motionPreference === 'reduce' ||
            classList.includes('motion-reduce-') ||
            classList.includes('motion-safe-') ||
            !classList.includes('animate-')) {
          compliantElements++;
        }
      } else {
        // For no-preference, all elements are considered compliant
        compliantElements++;
      }
    });
    
    return (compliantElements / this.animationElements.size) * 100;
  }
  
  /**
   * Calculate overall accessibility score
   */
  private calculateAccessibilityScore(complianceScores: number[]): number {
    if (complianceScores.length === 0) return 100;
    
    const averageCompliance = this.calculateAverage(complianceScores);
    const consistencyScore = this.calculateConsistency(complianceScores);
    
    // Weighted score: 70% compliance, 30% consistency
    return averageCompliance * 0.7 + consistencyScore * 0.3;
  }
  
  /**
   * Calculate consistency score for compliance
   */
  private calculateConsistency(scores: number[]): number {
    if (scores.length <= 1) return 100;
    
    const average = this.calculateAverage(scores);
    const variance = scores.reduce((sum, score) => {
      return sum + Math.pow(score - average, 2);
    }, 0) / scores.length;
    
    const standardDeviation = Math.sqrt(variance);
    
    // Convert to consistency score (lower deviation = higher consistency)
    // Assuming max reasonable deviation is 25 points
    return Math.max(0, 100 - (standardDeviation / 25) * 100);
  }
  
  /**
   * Start performance monitoring
   */
  startMonitoring(): void {
    if (this.isMonitoring) {
      console.warn('Performance monitoring is already active');
      return;
    }
    
    console.log('🎮 Starting real-time performance monitoring...');
    console.log('Thresholds:', this.thresholds);
    
    this.isMonitoring = true;
    this.monitoringStartTime = performance.now();
    this.frameMetrics = [];
    this.alerts = [];
    this.frameCount = 0;
    this.lastFrameTime = performance.now();
    
    // Start animation tracking
    this.startAnimationTracking();
    
    // Start frame measurement
    this.animationFrame = requestAnimationFrame(this.measureFrame);
    
    // Start periodic reporting
    this.reportInterval = window.setInterval(() => {
      this.generateReport();
    }, 5000); // Report every 5 seconds
  }
  
  /**
   * Stop performance monitoring
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) {
      console.warn('Performance monitoring is not active');
      return;
    }
    
    console.log('⏹️ Stopping performance monitoring...');
    
    this.isMonitoring = false;
    
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    
    if (this.reportInterval) {
      clearInterval(this.reportInterval);
      this.reportInterval = null;
    }
    
    // Stop animation tracking
    if (this.motionObserver) {
      this.motionObserver.disconnect();
      this.motionObserver = null;
    }
    
    // Generate final report
    const finalReport = this.generateReport();
    console.log('📊 Final performance report:', finalReport);
  }
  
  /**
   * Measure frame performance
   */
  private measureFrame(): void {
    if (!this.isMonitoring) return;
    
    const currentTime = performance.now();
    const frameTime = currentTime - this.lastFrameTime;
    
    if (frameTime > 0) {
      const fps = 1000 / frameTime;
      const memoryUsage = this.getCurrentMemoryUsage();
      const cpuUsage = this.estimateCPUUsage(frameTime);
      
      const metrics: PerformanceMetrics = {
        fps,
        frameTime,
        memoryUsage,
        cpuUsage,
        frameDrops: this.calculateFrameDrops(fps),
        timestamp: currentTime,
        // Motion preference metrics
        motionPreference: this.motionPreference,
        animationCount: this.animationElements.size,
        reducedMotionCompliance: this.calculateReducedMotionCompliance(),
      };
      
      this.frameMetrics.push(metrics);
      
      // Keep only recent metrics (last 1000 frames)
      if (this.frameMetrics.length > 1000) {
        this.frameMetrics.shift();
      }
      
      // Check for alerts
      this.checkForAlerts(metrics);
      
      // Call metrics callback
      if (this.callbacks.onMetrics) {
        this.callbacks.onMetrics(metrics);
      }
      
      this.frameCount++;
    }
    
    this.lastFrameTime = currentTime;
    
    if (this.isMonitoring) {
      this.animationFrame = requestAnimationFrame(this.measureFrame);
    }
  }
  
  /**
   * Get current memory usage
   */
  private getCurrentMemoryUsage(): number {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / (1024 * 1024); // Convert to MB
    }
    return 0;
  }
  
  /**
   * Estimate CPU usage based on frame time
   */
  private estimateCPUUsage(frameTime: number): number {
    // Rough estimation: frame time relative to target
    const targetFrameTime = 1000 / this.thresholds.targetFPS;
    return Math.min(100, (frameTime / targetFrameTime) * 100);
  }
  
  /**
   * Calculate frame drops for current FPS
   */
  private calculateFrameDrops(currentFPS: number): number {
    return currentFPS < this.thresholds.minFPS ? 1 : 0;
  }
  
  /**
   * Check for performance alerts
   */
  private checkForAlerts(metrics: PerformanceMetrics): void {
    const alerts: PerformanceAlert[] = [];
    
    // FPS too low
    if (metrics.fps < this.thresholds.minFPS) {
      alerts.push({
        id: `fps-low-${Date.now()}`,
        type: metrics.fps < this.thresholds.minFPS * 0.7 ? 'critical' : 'warning',
        message: `FPS dropped to ${metrics.fps.toFixed(1)} (target: ${this.thresholds.targetFPS})`,
        metrics,
        timestamp: metrics.timestamp,
      });
    }
    
    // Frame time too high
    if (metrics.frameTime > this.thresholds.maxFrameTime * 1.5) {
      alerts.push({
        id: `frametime-high-${Date.now()}`,
        type: metrics.frameTime > this.thresholds.maxFrameTime * 2 ? 'critical' : 'warning',
        message: `Frame time is ${metrics.frameTime.toFixed(1)}ms (target: <${this.thresholds.maxFrameTime.toFixed(1)}ms)`,
        metrics,
        timestamp: metrics.timestamp,
      });
    }
    
    // Memory usage too high
    if (metrics.memoryUsage > this.thresholds.maxMemoryMB) {
      alerts.push({
        id: `memory-high-${Date.now()}`,
        type: metrics.memoryUsage > this.thresholds.maxMemoryMB * 1.5 ? 'critical' : 'warning',
        message: `Memory usage is ${metrics.memoryUsage.toFixed(1)}MB (limit: ${this.thresholds.maxMemoryMB}MB)`,
        metrics,
        timestamp: metrics.timestamp,
      });
    }
    
    // Add alerts and trigger callbacks
    alerts.forEach(alert => {
      this.alerts.push(alert);
      
      if (this.callbacks.onAlert) {
        this.callbacks.onAlert(alert);
      }
      
      console.warn(`🚨 Performance Alert [${alert.type.toUpperCase()}]: ${alert.message}`);
    });
  }
  
  /**
   * Generate performance report
   */
  generateReport(): PerformanceReport {
    if (this.frameMetrics.length === 0) {
      throw new Error('No performance data available');
    }
    
    const fpsValues = this.frameMetrics.map(m => m.fps);
    const frameTimeValues = this.frameMetrics.map(m => m.frameTime);
    const memoryValues = this.frameMetrics.map(m => m.memoryUsage);
    const animationCounts = this.frameMetrics.map(m => m.animationCount || 0);
    const complianceScores = this.frameMetrics.map(m => m.reducedMotionCompliance || 100);
    
    const summary = {
      averageFPS: this.calculateAverage(fpsValues),
      minFPS: Math.min(...fpsValues),
      maxFPS: Math.max(...fpsValues),
      averageFrameTime: this.calculateAverage(frameTimeValues),
      totalFrameDrops: this.frameMetrics.reduce((sum, m) => sum + m.frameDrops, 0),
      memoryPeak: Math.max(...memoryValues),
      testDuration: performance.now() - this.monitoringStartTime,
      // Motion preference metrics
      motionPreference: this.motionPreference,
      averageAnimationCount: this.calculateAverage(animationCounts),
      reducedMotionComplianceScore: this.calculateAverage(complianceScores),
      accessibilityScore: this.calculateAccessibilityScore(complianceScores),
    };
    
    const recommendations = this.generateRecommendations(summary);
    
    const report: PerformanceReport = {
      summary,
      alerts: [...this.alerts],
      recommendations,
      deviceInfo: this.getDeviceInfo(),
      timestamp: Date.now(),
    };
    
    if (this.callbacks.onReport) {
      this.callbacks.onReport(report);
    }
    
    return report;
  }
  
  /**
   * Generate performance recommendations
   */
  private generateRecommendations(summary: any): string[] {
    const recommendations: string[] = [];
    
    if (summary.averageFPS < this.thresholds.targetFPS * 0.9) {
      recommendations.push(`Average FPS (${summary.averageFPS.toFixed(1)}) is below target. Consider reducing animation complexity.`);
    }
    
    if (summary.minFPS < this.thresholds.minFPS) {
      recommendations.push(`Minimum FPS (${summary.minFPS.toFixed(1)}) indicates significant frame drops. Enable adaptive quality settings.`);
    }
    
    if (summary.averageFrameTime > this.thresholds.maxFrameTime) {
      recommendations.push(`Frame time (${summary.averageFrameTime.toFixed(1)}ms) is above target. Optimize rendering pipeline.`);
    }
    
    if (summary.memoryPeak > this.thresholds.maxMemoryMB) {
      recommendations.push(`Memory usage peaked at ${summary.memoryPeak.toFixed(1)}MB. Check for memory leaks and optimize textures.`);
    }
    
    if (summary.totalFrameDrops > this.thresholds.maxFrameDrops) {
      recommendations.push(`${summary.totalFrameDrops} frame drops detected. Consider enabling performance mode.`);
    }
    
    // Motion preference recommendations
    if (summary.motionPreference === 'reduce' && summary.reducedMotionComplianceScore < 80) {
      recommendations.push(`Reduced motion compliance is ${summary.reducedMotionComplianceScore.toFixed(1)}%. Improve accessibility by implementing proper motion-safe animations.`);
    }
    
    if (summary.accessibilityScore < 70) {
      recommendations.push(`Accessibility score is ${summary.accessibilityScore.toFixed(1)}%. Review motion preference implementation for better user experience.`);
    }
    
    if (summary.averageAnimationCount > 20 && summary.averageFPS < this.thresholds.targetFPS) {
      recommendations.push(`High animation count (${summary.averageAnimationCount.toFixed(0)}) may be affecting performance. Consider reducing concurrent animations.`);
    }
    
    if (summary.motionPreference === 'reduce' && summary.averageAnimationCount > 10) {
      recommendations.push('User prefers reduced motion but many animations are active. Consider implementing stricter motion reduction.');
    }
    
    // Device-specific recommendations
    const deviceType = this.getDeviceType();
    if (deviceType === 'mobile' && summary.averageFPS > 35) {
      recommendations.push('Mobile device performing well. Consider enabling enhanced visual effects.');
    }
    
    if (recommendations.length === 0) {
      recommendations.push('Performance and accessibility are within acceptable limits. No specific optimizations needed.');
    }
    
    return recommendations;
  }
  
  /**
   * Get current performance metrics
   */
  getCurrentMetrics(): PerformanceMetrics | null {
    return this.frameMetrics.length > 0 ? this.frameMetrics[this.frameMetrics.length - 1] : null;
  }
  
  /**
   * Get performance history
   */
  getPerformanceHistory(count: number = 100): PerformanceMetrics[] {
    return this.frameMetrics.slice(-count);
  }
  
  /**
   * Get active alerts
   */
  getActiveAlerts(): PerformanceAlert[] {
    return this.alerts.filter(alert => !alert.resolved);
  }
  
  /**
   * Resolve alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
    }
  }
  
  /**
   * Clear all alerts
   */
  clearAlerts(): void {
    this.alerts = [];
  }
  
  /**
   * Update thresholds
   */
  updateThresholds(newThresholds: Partial<PerformanceThresholds>): void {
    this.thresholds = { ...this.thresholds, ...newThresholds };
    console.log('Updated performance thresholds:', this.thresholds);
  }
  
  /**
   * Get performance statistics
   */
  getStatistics(): {
    uptime: number;
    totalFrames: number;
    averageFPS: number;
    alertCount: number;
    isHealthy: boolean;
  } {
    const uptime = performance.now() - this.monitoringStartTime;
    const fpsValues = this.frameMetrics.map(m => m.fps);
    const averageFPS = fpsValues.length > 0 ? this.calculateAverage(fpsValues) : 0;
    const activeAlerts = this.getActiveAlerts();
    
    return {
      uptime,
      totalFrames: this.frameCount,
      averageFPS,
      alertCount: activeAlerts.length,
      isHealthy: averageFPS >= this.thresholds.minFPS && activeAlerts.filter(a => a.type === 'critical').length === 0,
    };
  }
  
  /**
   * Export performance data
   */
  exportData(): {
    thresholds: PerformanceThresholds;
    metrics: PerformanceMetrics[];
    alerts: PerformanceAlert[];
    statistics: any;
  } {
    return {
      thresholds: this.thresholds,
      metrics: this.frameMetrics,
      alerts: this.alerts,
      statistics: this.getStatistics(),
    };
  }
  
  /**
   * Utility functions
   */
  private calculateAverage(values: number[]): number {
    return values.length > 0 ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
  }
  
  private getDeviceType(): 'mobile' | 'tablet' | 'desktop' {
    const width = window.innerWidth;
    if (width <= 768) return 'mobile';
    if (width <= 1024) return 'tablet';
    return 'desktop';
  }
  
  private getDeviceInfo(): any {
    return {
      type: this.getDeviceType(),
      userAgent: navigator.userAgent,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      devicePixelRatio: window.devicePixelRatio || 1,
      hardwareConcurrency: navigator.hardwareConcurrency || 'Unknown',
      memory: this.getCurrentMemoryUsage(),
      timestamp: Date.now(),
    };
  }
}

/**
 * Global performance monitor instance
 */
let globalPerformanceMonitor: RealTimePerformanceMonitor | null = null;

/**
 * Get global performance monitor instance
 */
export function getPerformanceMonitor(): RealTimePerformanceMonitor {
  if (!globalPerformanceMonitor) {
    globalPerformanceMonitor = new RealTimePerformanceMonitor();
  }
  return globalPerformanceMonitor;
}

/**
 * Start global performance monitoring
 */
export function startGlobalPerformanceMonitoring(
  thresholds?: Partial<PerformanceThresholds>,
  callbacks?: {
    onMetrics?: (metrics: PerformanceMetrics) => void;
    onAlert?: (alert: PerformanceAlert) => void;
    onReport?: (report: PerformanceReport) => void;
  }
): RealTimePerformanceMonitor {
  if (globalPerformanceMonitor) {
    globalPerformanceMonitor.stopMonitoring();
  }
  
  globalPerformanceMonitor = new RealTimePerformanceMonitor(thresholds, callbacks);
  globalPerformanceMonitor.startMonitoring();
  
  return globalPerformanceMonitor;
}

/**
 * Stop global performance monitoring
 */
export function stopGlobalPerformanceMonitoring(): void {
  if (globalPerformanceMonitor) {
    globalPerformanceMonitor.stopMonitoring();
  }
}

/**
 * Quick performance check
 */
export async function quickPerformanceCheck(duration: number = 5000): Promise<PerformanceReport> {
  const monitor = new RealTimePerformanceMonitor();
  
  return new Promise((resolve, reject) => {
    monitor.startMonitoring();
    
    setTimeout(() => {
      try {
        const report = monitor.generateReport();
        monitor.stopMonitoring();
        resolve(report);
      } catch (error) {
        monitor.stopMonitoring();
        reject(error);
      }
    }, duration);
  });
}

/**
 * Performance test for specific FPS targets
 */
export async function testFPSTarget(
  targetFPS: number,
  duration: number = 10000
): Promise<{
  passed: boolean;
  actualFPS: number;
  targetFPS: number;
  deviation: number;
  report: PerformanceReport;
}> {
  const monitor = new RealTimePerformanceMonitor({
    targetFPS,
    minFPS: targetFPS * 0.8,
  });
  
  return new Promise((resolve, reject) => {
    monitor.startMonitoring();
    
    setTimeout(() => {
      try {
        const report = monitor.generateReport();
        monitor.stopMonitoring();
        
        const actualFPS = report.summary.averageFPS;
        const deviation = Math.abs(actualFPS - targetFPS) / targetFPS * 100;
        const passed = actualFPS >= targetFPS * 0.8; // 80% of target
        
        resolve({
          passed,
          actualFPS,
          targetFPS,
          deviation,
          report,
        });
      } catch (error) {
        monitor.stopMonitoring();
        reject(error);
      }
    }, duration);
  });
}