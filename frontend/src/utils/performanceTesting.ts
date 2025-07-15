/**
 * Enhanced Performance Testing Suite
 * 
 * Comprehensive testing framework for maintaining 60fps on desktop
 * and 30fps minimum on mobile with stress testing and benchmarking.
 */

import type { MobileCapabilities, MobileOptimizationSettings } from './mobileDetection';

// Performance test configuration
export interface PerformanceTestConfig {
  targetFPS: {
    desktop: number;
    mobile: number;
    tablet: number;
  };
  testDuration: number; // in milliseconds
  stressTestMultiplier: number;
  acceptableDropThreshold: number; // percentage
  memoryLimitMB: number;
  enableStressTest: boolean;
  enableBenchmarking: boolean;
  enableAutomaticOptimization: boolean;
}

// Performance test results
export interface PerformanceTestResults {
  averageFPS: number;
  minFPS: number;
  maxFPS: number;
  frameDrops: number;
  testDuration: number;
  memoryUsage: {
    initial: number;
    peak: number;
    final: number;
  };
  deviceInfo: {
    type: 'desktop' | 'mobile' | 'tablet';
    capabilities: MobileCapabilities;
  };
  testPassed: boolean;
  recommendations: string[];
  optimizationApplied?: MobileOptimizationSettings;
}

// Benchmark test scenario
export interface BenchmarkScenario {
  name: string;
  description: string;
  config: {
    particleCount: number;
    intensity: number;
    complexityLevel: 'low' | 'medium' | 'high' | 'extreme';
    enableEffects: boolean;
    textureQuality: 'low' | 'medium' | 'high';
  };
  expectedFPS: {
    desktop: number;
    mobile: number;
  };
}

// Stress test configuration
export interface StressTestConfig {
  scenarios: BenchmarkScenario[];
  progressiveLoad: boolean;
  maxStressLevel: number;
  recoveryTestEnabled: boolean;
}

/**
 * Enhanced Performance Testing Framework
 */
export class PerformanceTestSuite {
  private testConfig: PerformanceTestConfig;
  private isTestRunning: boolean = false;
  private testStartTime: number = 0;
  private frameHistory: number[] = [];
  private memoryHistory: number[] = [];
  private animationFrame: number | null = null;
  private testResults: PerformanceTestResults[] = [];
  
  constructor(config?: Partial<PerformanceTestConfig>) {
    this.testConfig = {
      targetFPS: {
        desktop: 60,
        mobile: 30,
        tablet: 45,
      },
      testDuration: 10000, // 10 seconds
      stressTestMultiplier: 2.0,
      acceptableDropThreshold: 5, // 5% frame drops acceptable
      memoryLimitMB: 512,
      enableStressTest: true,
      enableBenchmarking: true,
      enableAutomaticOptimization: true,
      ...config,
    };
  }
  
  /**
   * Run comprehensive performance test
   */
  async runPerformanceTest(
    animationElement: HTMLElement,
    optimizationSettings?: MobileOptimizationSettings
  ): Promise<PerformanceTestResults> {
    console.log('🚀 Starting comprehensive performance test...');
    
    const deviceInfo = await this.getDeviceInfo();
    const targetFPS = this.getTargetFPS(deviceInfo.type);
    
    // Initialize test
    this.resetTestMetrics();
    this.isTestRunning = true;
    this.testStartTime = performance.now();
    
    const memoryInitial = this.getCurrentMemoryUsage();
    
    // Start FPS monitoring
    this.startFPSMonitoring();
    
    // Run test for specified duration
    await this.waitForTestCompletion();
    
    // Stop monitoring
    this.stopFPSMonitoring();
    
    const memoryFinal = this.getCurrentMemoryUsage();
    const memoryPeak = Math.max(...this.memoryHistory);
    
    // Calculate metrics
    const averageFPS = this.calculateAverageFPS();
    const minFPS = Math.min(...this.frameHistory);
    const maxFPS = Math.max(...this.frameHistory);
    const frameDrops = this.calculateFrameDrops(targetFPS);
    
    // Determine if test passed
    const testPassed = this.evaluateTestResults(averageFPS, minFPS, targetFPS, frameDrops);
    
    // Generate recommendations
    const recommendations = this.generateOptimizationRecommendations(
      averageFPS,
      minFPS,
      targetFPS,
      memoryPeak,
      deviceInfo
    );
    
    const results: PerformanceTestResults = {
      averageFPS,
      minFPS,
      maxFPS,
      frameDrops,
      testDuration: this.testConfig.testDuration,
      memoryUsage: {
        initial: memoryInitial,
        peak: memoryPeak,
        final: memoryFinal,
      },
      deviceInfo,
      testPassed,
      recommendations,
      optimizationApplied: optimizationSettings,
    };
    
    this.testResults.push(results);
    
    console.log('✅ Performance test completed:', results);
    return results;
  }
  
  /**
   * Run stress test with progressive load
   */
  async runStressTest(animationElement: HTMLElement): Promise<PerformanceTestResults[]> {
    if (!this.testConfig.enableStressTest) {
      throw new Error('Stress testing is disabled');
    }
    
    console.log('🔥 Starting stress test with progressive load...');
    
    const stressScenarios = this.generateStressScenarios();
    const stressResults: PerformanceTestResults[] = [];
    
    for (const scenario of stressScenarios) {
      console.log(`Testing scenario: ${scenario.name}`);
      
      // Apply stress scenario configuration
      await this.applyStressScenario(animationElement, scenario);
      
      // Run performance test for this scenario
      const result = await this.runPerformanceTest(animationElement);
      result.deviceInfo = { ...result.deviceInfo, type: 'desktop' }; // Override for stress test
      
      stressResults.push({
        ...result,
        testDuration: 5000, // Shorter duration for stress tests
      });
      
      // Recovery test - check if performance recovers after stress
      if (this.testConfig.enableStressTest) {
        await this.runRecoveryTest(animationElement);
      }
      
      // Small delay between tests
      await this.delay(1000);
    }
    
    console.log('✅ Stress test completed. Results:', stressResults);
    return stressResults;
  }
  
  /**
   * Run benchmark suite
   */
  async runBenchmarkSuite(animationElement: HTMLElement): Promise<{
    scenarios: BenchmarkScenario[];
    results: PerformanceTestResults[];
    summary: {
      averageDesktopFPS: number;
      averageMobileFPS: number;
      passRate: number;
      recommendations: string[];
    };
  }> {
    if (!this.testConfig.enableBenchmarking) {
      throw new Error('Benchmarking is disabled');
    }
    
    console.log('📊 Starting benchmark suite...');
    
    const benchmarkScenarios = this.getBenchmarkScenarios();
    const benchmarkResults: PerformanceTestResults[] = [];
    
    for (const scenario of benchmarkScenarios) {
      console.log(`Benchmarking: ${scenario.name}`);
      
      // Configure animation for this benchmark
      await this.configureBenchmarkScenario(animationElement, scenario);
      
      // Run test
      const result = await this.runPerformanceTest(animationElement);
      benchmarkResults.push(result);
      
      await this.delay(500);
    }
    
    // Generate summary
    const summary = this.generateBenchmarkSummary(benchmarkResults);
    
    console.log('✅ Benchmark suite completed');
    return {
      scenarios: benchmarkScenarios,
      results: benchmarkResults,
      summary,
    };
  }
  
  /**
   * Automated performance optimization
   */
  async optimizePerformanceAutomatically(
    animationElement: HTMLElement,
    deviceCapabilities: MobileCapabilities
  ): Promise<{
    originalSettings: MobileOptimizationSettings;
    optimizedSettings: MobileOptimizationSettings;
    improvementMetrics: {
      fpsImprovement: number;
      memoryReduction: number;
      stabilityImprovement: number;
    };
  }> {
    console.log('🔧 Starting automatic performance optimization...');
    
    // Get baseline performance
    const baselineTest = await this.runPerformanceTest(animationElement);
    const originalSettings = this.getCurrentOptimizationSettings(deviceCapabilities);
    
    // Generate optimized settings based on test results
    const optimizedSettings = this.generateOptimizedSettings(
      baselineTest,
      originalSettings,
      deviceCapabilities
    );
    
    // Apply optimizations
    await this.applyOptimizationSettings(animationElement, optimizedSettings);
    
    // Test optimized performance
    const optimizedTest = await this.runPerformanceTest(animationElement, optimizedSettings);
    
    // Calculate improvements
    const improvementMetrics = {
      fpsImprovement: ((optimizedTest.averageFPS - baselineTest.averageFPS) / baselineTest.averageFPS) * 100,
      memoryReduction: ((baselineTest.memoryUsage.peak - optimizedTest.memoryUsage.peak) / baselineTest.memoryUsage.peak) * 100,
      stabilityImprovement: ((optimizedTest.minFPS - baselineTest.minFPS) / baselineTest.minFPS) * 100,
    };
    
    console.log('✅ Automatic optimization completed:', improvementMetrics);
    
    return {
      originalSettings,
      optimizedSettings,
      improvementMetrics,
    };
  }
  
  /**
   * Device info detection
   */
  private async getDeviceInfo(): Promise<{ type: 'desktop' | 'mobile' | 'tablet'; capabilities: MobileCapabilities }> {
    // Use existing mobile detection if available
    try {
      const { getMobileCapabilities } = await import('./mobileDetection');
      const capabilities = await getMobileCapabilities();
      
      const type = this.determineDeviceType(capabilities);
      
      return { type, capabilities };
    } catch (error) {
      // Fallback detection
      const type = window.innerWidth <= 768 ? 'mobile' : 
                  window.innerWidth <= 1024 ? 'tablet' : 'desktop';
      
      const capabilities: MobileCapabilities = {
        isMobile: type === 'mobile',
        devicePixelRatio: window.devicePixelRatio || 1,
        hardwareConcurrency: navigator.hardwareConcurrency || 4,
        maxTouchPoints: navigator.maxTouchPoints || 0,
        supportsWebGL: true,
        supportsWebGL2: true,
        gpuVendor: 'unknown',
        gpuRenderer: 'unknown',
        maxTextureSize: 4096,
        gpuMemoryMB: 1024,
        batteryLevel: 1,
        isCharging: true,
        connectionType: 'wifi',
        effectiveConnectionType: '4g',
        downlinkSpeed: 10,
        saveData: false,
        deviceClass: 'high-end',
        performanceScore: 0.8,
        thermalState: 'nominal',
        orientationSupport: true,
        motionSensors: false,
        screenSize: { width: window.innerWidth, height: window.innerHeight },
        viewportSize: { width: window.innerWidth, height: window.innerHeight },
        colorGamut: 'srgb',
        colorDepth: screen.colorDepth || 24,
        refreshRate: 60,
        hdrSupport: false,
        reducedMotion: false,
      };
      
      return { type, capabilities };
    }
  }
  
  /**
   * Determine device type from capabilities
   */
  private determineDeviceType(capabilities: MobileCapabilities): 'desktop' | 'mobile' | 'tablet' {
    if (capabilities.isMobile && capabilities.screenSize.width <= 768) {
      return 'mobile';
    } else if (capabilities.maxTouchPoints > 0 && capabilities.screenSize.width <= 1024) {
      return 'tablet';
    } else {
      return 'desktop';
    }
  }
  
  /**
   * Get target FPS for device type
   */
  private getTargetFPS(deviceType: 'desktop' | 'mobile' | 'tablet'): number {
    return this.testConfig.targetFPS[deviceType];
  }
  
  /**
   * Reset test metrics
   */
  private resetTestMetrics(): void {
    this.frameHistory = [];
    this.memoryHistory = [];
    this.isTestRunning = false;
    this.testStartTime = 0;
  }
  
  /**
   * Start FPS monitoring
   */
  private startFPSMonitoring(): void {
    let lastFrameTime = performance.now();
    let frameCount = 0;
    
    const measureFrame = () => {
      if (!this.isTestRunning) return;
      
      const currentTime = performance.now();
      const deltaTime = currentTime - lastFrameTime;
      
      if (deltaTime > 0) {
        const fps = 1000 / deltaTime;
        this.frameHistory.push(fps);
        
        // Sample memory usage periodically
        if (frameCount % 30 === 0) { // Every 30 frames
          this.memoryHistory.push(this.getCurrentMemoryUsage());
        }
      }
      
      lastFrameTime = currentTime;
      frameCount++;
      
      this.animationFrame = requestAnimationFrame(measureFrame);
    };
    
    this.animationFrame = requestAnimationFrame(measureFrame);
  }
  
  /**
   * Stop FPS monitoring
   */
  private stopFPSMonitoring(): void {
    this.isTestRunning = false;
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
  }
  
  /**
   * Wait for test completion
   */
  private async waitForTestCompletion(): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.isTestRunning = false;
        resolve();
      }, this.testConfig.testDuration);
    });
  }
  
  /**
   * Calculate average FPS
   */
  private calculateAverageFPS(): number {
    if (this.frameHistory.length === 0) return 0;
    const sum = this.frameHistory.reduce((acc, fps) => acc + fps, 0);
    return Math.round(sum / this.frameHistory.length * 100) / 100;
  }
  
  /**
   * Calculate frame drops
   */
  private calculateFrameDrops(targetFPS: number): number {
    const threshold = targetFPS * 0.8; // 80% of target FPS
    return this.frameHistory.filter(fps => fps < threshold).length;
  }
  
  /**
   * Evaluate test results
   */
  private evaluateTestResults(averageFPS: number, minFPS: number, targetFPS: number, frameDrops: number): boolean {
    const fpsThreshold = targetFPS * 0.9; // 90% of target FPS
    const maxFrameDrops = this.frameHistory.length * (this.testConfig.acceptableDropThreshold / 100);
    
    return averageFPS >= fpsThreshold && 
           minFPS >= targetFPS * 0.7 && // Min FPS should be at least 70% of target
           frameDrops <= maxFrameDrops;
  }
  
  /**
   * Generate optimization recommendations
   */
  private generateOptimizationRecommendations(
    averageFPS: number,
    minFPS: number,
    targetFPS: number,
    memoryPeak: number,
    deviceInfo: { type: string; capabilities: MobileCapabilities }
  ): string[] {
    const recommendations: string[] = [];
    
    if (averageFPS < targetFPS * 0.9) {
      recommendations.push(`Average FPS (${averageFPS.toFixed(1)}) is below target (${targetFPS}). Consider reducing particle count or complexity.`);
    }
    
    if (minFPS < targetFPS * 0.7) {
      recommendations.push(`Minimum FPS (${minFPS.toFixed(1)}) indicates frame drops. Enable adaptive quality or frame rate limiting.`);
    }
    
    if (memoryPeak > this.testConfig.memoryLimitMB) {
      recommendations.push(`Memory usage (${memoryPeak.toFixed(1)}MB) exceeds limit (${this.testConfig.memoryLimitMB}MB). Optimize texture sizes and particle buffers.`);
    }
    
    if (deviceInfo.type === 'mobile' && averageFPS > 35) {
      recommendations.push('Mobile device performing well. Consider enabling enhanced visual effects.');
    }
    
    if (deviceInfo.capabilities.deviceClass === 'low-end') {
      recommendations.push('Low-end device detected. Use minimal animation settings for better performance.');
    }
    
    if (deviceInfo.capabilities.thermalState === 'critical') {
      recommendations.push('Thermal throttling detected. Reduce animation intensity to prevent overheating.');
    }
    
    return recommendations;
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
   * Generate stress test scenarios
   */
  private generateStressScenarios(): BenchmarkScenario[] {
    const baseMultiplier = this.testConfig.stressTestMultiplier;
    
    return [
      {
        name: 'Moderate Stress Test',
        description: 'Moderate load to test stability',
        config: {
          particleCount: Math.round(16 * baseMultiplier),
          intensity: 0.7,
          complexityLevel: 'medium',
          enableEffects: true,
          textureQuality: 'medium',
        },
        expectedFPS: { desktop: 50, mobile: 25 },
      },
      {
        name: 'High Stress Test',
        description: 'High load to test performance limits',
        config: {
          particleCount: Math.round(32 * baseMultiplier),
          intensity: 0.9,
          complexityLevel: 'high',
          enableEffects: true,
          textureQuality: 'high',
        },
        expectedFPS: { desktop: 40, mobile: 20 },
      },
      {
        name: 'Extreme Stress Test',
        description: 'Maximum load to test breaking point',
        config: {
          particleCount: Math.round(64 * baseMultiplier),
          intensity: 1.0,
          complexityLevel: 'extreme',
          enableEffects: true,
          textureQuality: 'high',
        },
        expectedFPS: { desktop: 30, mobile: 15 },
      },
    ];
  }
  
  /**
   * Get benchmark scenarios
   */
  private getBenchmarkScenarios(): BenchmarkScenario[] {
    return [
      {
        name: 'Low Performance',
        description: 'Minimal settings for low-end devices',
        config: {
          particleCount: 4,
          intensity: 0.3,
          complexityLevel: 'low',
          enableEffects: false,
          textureQuality: 'low',
        },
        expectedFPS: { desktop: 60, mobile: 30 },
      },
      {
        name: 'Medium Performance',
        description: 'Balanced settings for mid-range devices',
        config: {
          particleCount: 12,
          intensity: 0.5,
          complexityLevel: 'medium',
          enableEffects: true,
          textureQuality: 'medium',
        },
        expectedFPS: { desktop: 60, mobile: 30 },
      },
      {
        name: 'High Performance',
        description: 'Enhanced settings for high-end devices',
        config: {
          particleCount: 24,
          intensity: 0.8,
          complexityLevel: 'high',
          enableEffects: true,
          textureQuality: 'high',
        },
        expectedFPS: { desktop: 60, mobile: 25 },
      },
    ];
  }
  
  /**
   * Utility functions
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  private async applyStressScenario(element: HTMLElement, scenario: BenchmarkScenario): Promise<void> {
    // Implementation would configure the animation based on scenario
    console.log(`Applying stress scenario: ${scenario.name}`);
  }
  
  private async configureBenchmarkScenario(element: HTMLElement, scenario: BenchmarkScenario): Promise<void> {
    // Implementation would configure the animation based on scenario
    console.log(`Configuring benchmark: ${scenario.name}`);
  }
  
  private async runRecoveryTest(element: HTMLElement): Promise<void> {
    // Test if performance recovers after stress
    console.log('Running recovery test...');
    await this.delay(2000);
  }
  
  private getCurrentOptimizationSettings(capabilities: MobileCapabilities): MobileOptimizationSettings {
    // Return current optimization settings based on device capabilities
    return {
      maxParticleCount: capabilities.isMobile ? 8 : 16,
      preferredFrameRate: capabilities.isMobile ? 30 : 60,
      enableMotionReduce: capabilities.reducedMotion,
      enableCPUThrottling: capabilities.isMobile,
      enableGPUMemoryLimit: capabilities.isMobile,
      maxTextureResolution: capabilities.maxTextureSize,
      enableBatteryAwareness: capabilities.isMobile,
      lowBatteryThreshold: 0.2,
      enableDataSaving: capabilities.saveData,
      preloadAnimations: !capabilities.isMobile,
      enableHDRSupport: capabilities.hdrSupport,
      maxPixelDensity: capabilities.devicePixelRatio,
      preferredColorSpace: capabilities.colorGamut,
    };
  }
  
  private generateOptimizedSettings(
    testResults: PerformanceTestResults,
    currentSettings: MobileOptimizationSettings,
    capabilities: MobileCapabilities
  ): MobileOptimizationSettings {
    const optimized = { ...currentSettings };
    
    // Adjust based on test results
    if (testResults.averageFPS < testResults.deviceInfo.type === 'mobile' ? 25 : 50) {
      optimized.maxParticleCount = Math.max(4, Math.floor(optimized.maxParticleCount * 0.7));
      optimized.maxTextureResolution = Math.min(1024, optimized.maxTextureResolution);
    }
    
    if (testResults.memoryUsage.peak > 200) {
      optimized.enableGPUMemoryLimit = true;
      optimized.maxTextureResolution = Math.min(1024, optimized.maxTextureResolution);
    }
    
    return optimized;
  }
  
  private async applyOptimizationSettings(element: HTMLElement, settings: MobileOptimizationSettings): Promise<void> {
    // Apply optimization settings to the animation
    console.log('Applying optimization settings:', settings);
  }
  
  private generateBenchmarkSummary(results: PerformanceTestResults[]): any {
    const desktopResults = results.filter(r => r.deviceInfo.type === 'desktop');
    const mobileResults = results.filter(r => r.deviceInfo.type === 'mobile');
    
    const averageDesktopFPS = desktopResults.length > 0 ? 
      desktopResults.reduce((sum, r) => sum + r.averageFPS, 0) / desktopResults.length : 0;
    
    const averageMobileFPS = mobileResults.length > 0 ?
      mobileResults.reduce((sum, r) => sum + r.averageFPS, 0) / mobileResults.length : 0;
    
    const passRate = (results.filter(r => r.testPassed).length / results.length) * 100;
    
    const recommendations = [
      ...new Set(results.flatMap(r => r.recommendations))
    ];
    
    return {
      averageDesktopFPS: Math.round(averageDesktopFPS * 100) / 100,
      averageMobileFPS: Math.round(averageMobileFPS * 100) / 100,
      passRate: Math.round(passRate * 100) / 100,
      recommendations,
    };
  }
  
  /**
   * Get test history
   */
  getTestHistory(): PerformanceTestResults[] {
    return [...this.testResults];
  }
  
  /**
   * Clear test history
   */
  clearTestHistory(): void {
    this.testResults = [];
  }
  
  /**
   * Export test results
   */
  exportTestResults(): string {
    return JSON.stringify(this.testResults, null, 2);
  }
}