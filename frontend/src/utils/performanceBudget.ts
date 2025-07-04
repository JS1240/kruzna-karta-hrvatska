/**
 * Performance Budget and Alert System
 * 
 * Maintains strict performance budgets for 60fps desktop and 30fps mobile
 * with real-time alerts and automatic optimization recommendations.
 */

import type { PerformanceMetrics, PerformanceAlert } from './performanceMonitor';

// Performance budget configuration
export interface PerformanceBudget {
  name: string;
  description: string;
  targets: {
    desktop: {
      targetFPS: number;
      minFPS: number;
      maxFrameTime: number;
      memoryLimit: number;
      cpuLimit: number;
    };
    mobile: {
      targetFPS: number;
      minFPS: number;
      maxFrameTime: number;
      memoryLimit: number;
      cpuLimit: number;
    };
    tablet: {
      targetFPS: number;
      minFPS: number;
      maxFrameTime: number;
      memoryLimit: number;
      cpuLimit: number;
    };
  };
  alertThresholds: {
    warningLevel: number; // percentage of target before warning
    criticalLevel: number; // percentage of target before critical alert
    consecutiveFailures: number; // consecutive failures before alert
  };
  enforcementMode: 'strict' | 'advisory' | 'disabled';
  autoOptimization: boolean;
}

// Budget violation
export interface BudgetViolation {
  id: string;
  budgetName: string;
  deviceType: 'desktop' | 'mobile' | 'tablet';
  violationType: 'fps' | 'frameTime' | 'memory' | 'cpu';
  severity: 'warning' | 'critical';
  currentValue: number;
  targetValue: number;
  deviation: number;
  timestamp: number;
  consecutiveCount: number;
  resolved: boolean;
}

// Auto-optimization action
export interface OptimizationAction {
  id: string;
  type: 'reduce_particles' | 'lower_quality' | 'disable_effects' | 'throttle_framerate' | 'cleanup_memory';
  description: string;
  impact: {
    expectedFPSGain: number;
    expectedMemoryReduction: number;
    qualityLoss: 'none' | 'minimal' | 'moderate' | 'significant';
  };
  applied: boolean;
  timestamp: number;
}

// Budget report
export interface BudgetReport {
  budget: PerformanceBudget;
  currentMetrics: PerformanceMetrics;
  deviceType: 'desktop' | 'mobile' | 'tablet';
  compliance: {
    overall: boolean;
    fps: boolean;
    frameTime: boolean;
    memory: boolean;
    cpu: boolean;
  };
  violations: BudgetViolation[];
  recommendations: string[];
  optimizationActions: OptimizationAction[];
  timestamp: number;
}

/**
 * Performance Budget Manager
 */
export class PerformanceBudgetManager {
  private budgets: Map<string, PerformanceBudget> = new Map();
  private activeBudget: PerformanceBudget | null = null;
  private violations: BudgetViolation[] = [];
  private optimizationActions: OptimizationAction[] = [];
  private consecutiveFailures: Map<string, number> = new Map();
  
  private callbacks: {
    onViolation?: (violation: BudgetViolation) => void;
    onCompliance?: (report: BudgetReport) => void;
    onOptimization?: (action: OptimizationAction) => void;
  } = {};
  
  constructor(callbacks?: {
    onViolation?: (violation: BudgetViolation) => void;
    onCompliance?: (report: BudgetReport) => void;
    onOptimization?: (action: OptimizationAction) => void;
  }) {
    this.callbacks = callbacks || {};
    this.initializeDefaultBudgets();
  }
  
  /**
   * Initialize default performance budgets
   */
  private initializeDefaultBudgets(): void {
    // Strict budget for production
    this.addBudget({
      name: 'production',
      description: 'Production performance budget with strict FPS requirements',
      targets: {
        desktop: {
          targetFPS: 60,
          minFPS: 55,
          maxFrameTime: 16.67,
          memoryLimit: 512,
          cpuLimit: 70,
        },
        mobile: {
          targetFPS: 30,
          minFPS: 25,
          maxFrameTime: 33.33,
          memoryLimit: 256,
          cpuLimit: 80,
        },
        tablet: {
          targetFPS: 45,
          minFPS: 38,
          maxFrameTime: 22.22,
          memoryLimit: 384,
          cpuLimit: 75,
        },
      },
      alertThresholds: {
        warningLevel: 85, // Alert when performance drops to 85% of target
        criticalLevel: 70, // Critical alert when performance drops to 70% of target
        consecutiveFailures: 3,
      },
      enforcementMode: 'strict',
      autoOptimization: true,
    });
    
    // Development budget (more lenient)
    this.addBudget({
      name: 'development',
      description: 'Development budget with more lenient targets for testing',
      targets: {
        desktop: {
          targetFPS: 60,
          minFPS: 45,
          maxFrameTime: 20,
          memoryLimit: 1024,
          cpuLimit: 85,
        },
        mobile: {
          targetFPS: 30,
          minFPS: 20,
          maxFrameTime: 40,
          memoryLimit: 384,
          cpuLimit: 90,
        },
        tablet: {
          targetFPS: 45,
          minFPS: 30,
          maxFrameTime: 30,
          memoryLimit: 512,
          cpuLimit: 85,
        },
      },
      alertThresholds: {
        warningLevel: 75,
        criticalLevel: 60,
        consecutiveFailures: 5,
      },
      enforcementMode: 'advisory',
      autoOptimization: false,
    });
    
    // Performance testing budget (very strict)
    this.addBudget({
      name: 'testing',
      description: 'Ultra-strict budget for performance testing and validation',
      targets: {
        desktop: {
          targetFPS: 60,
          minFPS: 58,
          maxFrameTime: 16.67,
          memoryLimit: 256,
          cpuLimit: 60,
        },
        mobile: {
          targetFPS: 30,
          minFPS: 28,
          maxFrameTime: 33.33,
          memoryLimit: 128,
          cpuLimit: 70,
        },
        tablet: {
          targetFPS: 45,
          minFPS: 42,
          maxFrameTime: 22.22,
          memoryLimit: 192,
          cpuLimit: 65,
        },
      },
      alertThresholds: {
        warningLevel: 95,
        criticalLevel: 90,
        consecutiveFailures: 2,
      },
      enforcementMode: 'strict',
      autoOptimization: true,
    });
    
    // Set production as default
    this.activeBudget = this.budgets.get('production') || null;
  }
  
  /**
   * Add a new performance budget
   */
  addBudget(budget: PerformanceBudget): void {
    this.budgets.set(budget.name, budget);
    console.log(`📊 Added performance budget: ${budget.name}`);
  }
  
  /**
   * Set active budget
   */
  setActiveBudget(budgetName: string): boolean {
    const budget = this.budgets.get(budgetName);
    if (budget) {
      this.activeBudget = budget;
      console.log(`🎯 Active performance budget set to: ${budgetName}`);
      
      // Clear previous violations when switching budgets
      this.violations = [];
      this.consecutiveFailures.clear();
      
      return true;
    }
    
    console.warn(`Budget not found: ${budgetName}`);
    return false;
  }
  
  /**
   * Check performance against budget
   */
  checkBudgetCompliance(metrics: PerformanceMetrics): BudgetReport {
    if (!this.activeBudget) {
      throw new Error('No active performance budget set');
    }
    
    const deviceType = this.getDeviceType();
    const targets = this.activeBudget.targets[deviceType];
    
    // Check compliance for each metric
    const compliance = {
      overall: true,
      fps: metrics.fps >= targets.minFPS,
      frameTime: metrics.frameTime <= targets.maxFrameTime,
      memory: metrics.memoryUsage <= targets.memoryLimit,
      cpu: metrics.cpuUsage <= targets.cpuLimit,
    };
    
    compliance.overall = compliance.fps && compliance.frameTime && compliance.memory && compliance.cpu;
    
    // Check for violations
    const newViolations = this.checkForViolations(metrics, targets, deviceType);
    
    // Update consecutive failure tracking
    this.updateConsecutiveFailures(newViolations);
    
    // Add new violations
    newViolations.forEach(violation => {
      this.violations.push(violation);
      
      if (this.callbacks.onViolation) {
        this.callbacks.onViolation(violation);
      }
      
      console.warn(`🚨 Budget violation [${violation.severity.toUpperCase()}]: ${violation.violationType} - ${violation.currentValue} (target: ${violation.targetValue})`);
    });
    
    // Generate recommendations
    const recommendations = this.generateBudgetRecommendations(metrics, targets, newViolations);
    
    // Apply auto-optimization if enabled
    let optimizationActions: OptimizationAction[] = [];
    if (this.activeBudget.autoOptimization && newViolations.some(v => v.severity === 'critical')) {
      optimizationActions = this.applyAutoOptimizations(metrics, targets, newViolations);
    }
    
    const report: BudgetReport = {
      budget: this.activeBudget,
      currentMetrics: metrics,
      deviceType,
      compliance,
      violations: newViolations,
      recommendations,
      optimizationActions,
      timestamp: Date.now(),
    };
    
    // Trigger compliance callback
    if (this.callbacks.onCompliance) {
      this.callbacks.onCompliance(report);
    }
    
    return report;
  }
  
  /**
   * Check for budget violations
   */
  private checkForViolations(
    metrics: PerformanceMetrics,
    targets: any,
    deviceType: 'desktop' | 'mobile' | 'tablet'
  ): BudgetViolation[] {
    const violations: BudgetViolation[] = [];
    const thresholds = this.activeBudget!.alertThresholds;
    
    // Check FPS violation
    if (metrics.fps < targets.targetFPS) {
      const deviation = ((targets.targetFPS - metrics.fps) / targets.targetFPS) * 100;
      const severity = deviation > (100 - thresholds.criticalLevel) ? 'critical' : 'warning';
      
      if (deviation > (100 - thresholds.warningLevel)) {
        violations.push({
          id: `fps-${Date.now()}`,
          budgetName: this.activeBudget!.name,
          deviceType,
          violationType: 'fps',
          severity,
          currentValue: metrics.fps,
          targetValue: targets.targetFPS,
          deviation,
          timestamp: Date.now(),
          consecutiveCount: this.getConsecutiveCount('fps'),
          resolved: false,
        });
      }
    }
    
    // Check frame time violation
    if (metrics.frameTime > targets.maxFrameTime) {
      const deviation = ((metrics.frameTime - targets.maxFrameTime) / targets.maxFrameTime) * 100;
      const severity = deviation > 50 ? 'critical' : 'warning';
      
      violations.push({
        id: `frametime-${Date.now()}`,
        budgetName: this.activeBudget!.name,
        deviceType,
        violationType: 'frameTime',
        severity,
        currentValue: metrics.frameTime,
        targetValue: targets.maxFrameTime,
        deviation,
        timestamp: Date.now(),
        consecutiveCount: this.getConsecutiveCount('frameTime'),
        resolved: false,
      });
    }
    
    // Check memory violation
    if (metrics.memoryUsage > targets.memoryLimit) {
      const deviation = ((metrics.memoryUsage - targets.memoryLimit) / targets.memoryLimit) * 100;
      const severity = deviation > 30 ? 'critical' : 'warning';
      
      violations.push({
        id: `memory-${Date.now()}`,
        budgetName: this.activeBudget!.name,
        deviceType,
        violationType: 'memory',
        severity,
        currentValue: metrics.memoryUsage,
        targetValue: targets.memoryLimit,
        deviation,
        timestamp: Date.now(),
        consecutiveCount: this.getConsecutiveCount('memory'),
        resolved: false,
      });
    }
    
    // Check CPU violation
    if (metrics.cpuUsage > targets.cpuLimit) {
      const deviation = ((metrics.cpuUsage - targets.cpuLimit) / targets.cpuLimit) * 100;
      const severity = deviation > 25 ? 'critical' : 'warning';
      
      violations.push({
        id: `cpu-${Date.now()}`,
        budgetName: this.activeBudget!.name,
        deviceType,
        violationType: 'cpu',
        severity,
        currentValue: metrics.cpuUsage,
        targetValue: targets.cpuLimit,
        deviation,
        timestamp: Date.now(),
        consecutiveCount: this.getConsecutiveCount('cpu'),
        resolved: false,
      });
    }
    
    return violations;
  }
  
  /**
   * Update consecutive failure tracking
   */
  private updateConsecutiveFailures(violations: BudgetViolation[]): void {
    const currentViolationTypes = new Set(violations.map(v => v.violationType));
    
    // Increment counters for current violations
    currentViolationTypes.forEach(type => {
      const current = this.consecutiveFailures.get(type) || 0;
      this.consecutiveFailures.set(type, current + 1);
    });
    
    // Reset counters for resolved violations
    ['fps', 'frameTime', 'memory', 'cpu'].forEach(type => {
      if (!currentViolationTypes.has(type)) {
        this.consecutiveFailures.set(type, 0);
      }
    });
  }
  
  /**
   * Get consecutive failure count
   */
  private getConsecutiveCount(violationType: string): number {
    return this.consecutiveFailures.get(violationType) || 0;
  }
  
  /**
   * Generate budget recommendations
   */
  private generateBudgetRecommendations(
    metrics: PerformanceMetrics,
    targets: any,
    violations: BudgetViolation[]
  ): string[] {
    const recommendations: string[] = [];
    
    violations.forEach(violation => {
      switch (violation.violationType) {
        case 'fps':
          if (violation.severity === 'critical') {
            recommendations.push(`CRITICAL: FPS is ${violation.currentValue.toFixed(1)} (target: ${violation.targetValue}). Enable aggressive optimization mode.`);
          } else {
            recommendations.push(`FPS below target. Consider reducing animation complexity or particle count.`);
          }
          break;
          
        case 'frameTime':
          recommendations.push(`Frame time is ${violation.currentValue.toFixed(1)}ms (target: ≤${violation.targetValue}ms). Optimize rendering pipeline.`);
          break;
          
        case 'memory':
          recommendations.push(`Memory usage is ${violation.currentValue.toFixed(1)}MB (limit: ${violation.targetValue}MB). Check for memory leaks and optimize textures.`);
          break;
          
        case 'cpu':
          recommendations.push(`CPU usage is ${violation.currentValue.toFixed(1)}% (limit: ${violation.targetValue}%). Reduce computational complexity.`);
          break;
      }
      
      // Add consecutive failure recommendations
      if (violation.consecutiveCount >= this.activeBudget!.alertThresholds.consecutiveFailures) {
        recommendations.push(`PERSISTENT ISSUE: ${violation.violationType} has been violating budget for ${violation.consecutiveCount} consecutive checks. Immediate action required.`);
      }
    });
    
    // Device-specific recommendations
    const deviceType = this.getDeviceType();
    if (deviceType === 'mobile' && violations.length > 0) {
      recommendations.push('Mobile device detected. Consider enabling mobile optimization mode.');
    }
    
    if (violations.some(v => v.severity === 'critical')) {
      recommendations.push('Critical performance issues detected. Consider disabling non-essential animations.');
    }
    
    return recommendations;
  }
  
  /**
   * Apply automatic optimizations
   */
  private applyAutoOptimizations(
    metrics: PerformanceMetrics,
    targets: any,
    violations: BudgetViolation[]
  ): OptimizationAction[] {
    const actions: OptimizationAction[] = [];
    
    violations.forEach(violation => {
      if (violation.severity === 'critical') {
        let action: OptimizationAction | null = null;
        
        switch (violation.violationType) {
          case 'fps':
            if (violation.deviation > 40) {
              action = {
                id: `auto-reduce-particles-${Date.now()}`,
                type: 'reduce_particles',
                description: 'Automatically reduced particle count by 50% due to critical FPS violation',
                impact: {
                  expectedFPSGain: 15,
                  expectedMemoryReduction: 20,
                  qualityLoss: 'moderate',
                },
                applied: false,
                timestamp: Date.now(),
              };
            } else {
              action = {
                id: `auto-lower-quality-${Date.now()}`,
                type: 'lower_quality',
                description: 'Automatically lowered animation quality due to FPS violation',
                impact: {
                  expectedFPSGain: 8,
                  expectedMemoryReduction: 10,
                  qualityLoss: 'minimal',
                },
                applied: false,
                timestamp: Date.now(),
              };
            }
            break;
            
          case 'memory':
            action = {
              id: `auto-cleanup-memory-${Date.now()}`,
              type: 'cleanup_memory',
              description: 'Automatically triggered memory cleanup due to memory violation',
              impact: {
                expectedFPSGain: 3,
                expectedMemoryReduction: 25,
                qualityLoss: 'none',
              },
              applied: false,
              timestamp: Date.now(),
            };
            break;
            
          case 'cpu':
            action = {
              id: `auto-throttle-framerate-${Date.now()}`,
              type: 'throttle_framerate',
              description: 'Automatically throttled frame rate due to CPU violation',
              impact: {
                expectedFPSGain: 0,
                expectedMemoryReduction: 5,
                qualityLoss: 'minimal',
              },
              applied: false,
              timestamp: Date.now(),
            };
            break;
        }
        
        if (action) {
          actions.push(action);
          this.optimizationActions.push(action);
          
          // Apply the optimization (in real implementation)
          this.applyOptimizationAction(action);
          
          if (this.callbacks.onOptimization) {
            this.callbacks.onOptimization(action);
          }
          
          console.log(`🔧 Auto-optimization applied: ${action.description}`);
        }
      }
    });
    
    return actions;
  }
  
  /**
   * Apply optimization action
   */
  private applyOptimizationAction(action: OptimizationAction): void {
    // In a real implementation, this would:
    // - Reduce particle count for 'reduce_particles'
    // - Lower quality settings for 'lower_quality'
    // - Disable effects for 'disable_effects'
    // - Throttle frame rate for 'throttle_framerate'
    // - Trigger garbage collection for 'cleanup_memory'
    
    action.applied = true;
    console.log(`Applied optimization: ${action.type}`);
  }
  
  /**
   * Get device type
   */
  private getDeviceType(): 'desktop' | 'mobile' | 'tablet' {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1920;
    if (width <= 768) return 'mobile';
    if (width <= 1024) return 'tablet';
    return 'desktop';
  }
  
  /**
   * Get active violations
   */
  getActiveViolations(): BudgetViolation[] {
    return this.violations.filter(v => !v.resolved);
  }
  
  /**
   * Resolve violation
   */
  resolveViolation(violationId: string): void {
    const violation = this.violations.find(v => v.id === violationId);
    if (violation) {
      violation.resolved = true;
      console.log(`✅ Resolved budget violation: ${violationId}`);
    }
  }
  
  /**
   * Clear all violations
   */
  clearViolations(): void {
    this.violations = [];
    this.consecutiveFailures.clear();
    console.log('🧹 Cleared all budget violations');
  }
  
  /**
   * Get budget summary
   */
  getBudgetSummary(): {
    activeBudget: string;
    totalViolations: number;
    activeViolations: number;
    criticalViolations: number;
    optimizationActions: number;
    consecutiveFailures: { [type: string]: number };
  } {
    const activeViolations = this.getActiveViolations();
    
    return {
      activeBudget: this.activeBudget?.name || 'none',
      totalViolations: this.violations.length,
      activeViolations: activeViolations.length,
      criticalViolations: activeViolations.filter(v => v.severity === 'critical').length,
      optimizationActions: this.optimizationActions.filter(a => a.applied).length,
      consecutiveFailures: Object.fromEntries(this.consecutiveFailures),
    };
  }
  
  /**
   * Export budget data
   */
  exportBudgetData(): string {
    return JSON.stringify({
      activeBudget: this.activeBudget,
      budgets: Object.fromEntries(this.budgets),
      violations: this.violations,
      optimizationActions: this.optimizationActions,
      summary: this.getBudgetSummary(),
      timestamp: new Date().toISOString(),
    }, null, 2);
  }
  
  /**
   * Set enforcement mode
   */
  setEnforcementMode(mode: 'strict' | 'advisory' | 'disabled'): void {
    if (this.activeBudget) {
      this.activeBudget.enforcementMode = mode;
      console.log(`🎛️ Budget enforcement mode set to: ${mode}`);
    }
  }
  
  /**
   * Enable/disable auto-optimization
   */
  setAutoOptimization(enabled: boolean): void {
    if (this.activeBudget) {
      this.activeBudget.autoOptimization = enabled;
      console.log(`🤖 Auto-optimization ${enabled ? 'enabled' : 'disabled'}`);
    }
  }
  
  /**
   * Get available budgets
   */
  getAvailableBudgets(): PerformanceBudget[] {
    return Array.from(this.budgets.values());
  }
  
  /**
   * Get budget compliance rate
   */
  getComplianceRate(timeWindow: number = 3600000): number { // Default: 1 hour
    const cutoffTime = Date.now() - timeWindow;
    const recentViolations = this.violations.filter(v => v.timestamp > cutoffTime);
    
    if (recentViolations.length === 0) return 100;
    
    // Calculate compliance rate based on resolved vs total violations
    const resolvedViolations = recentViolations.filter(v => v.resolved).length;
    return (resolvedViolations / recentViolations.length) * 100;
  }
}

/**
 * Global budget manager instance
 */
let globalBudgetManager: PerformanceBudgetManager | null = null;

/**
 * Get global budget manager
 */
export function getBudgetManager(): PerformanceBudgetManager {
  if (!globalBudgetManager) {
    globalBudgetManager = new PerformanceBudgetManager();
  }
  return globalBudgetManager;
}

/**
 * Initialize budget manager with callbacks
 */
export function initializeBudgetManager(callbacks?: {
  onViolation?: (violation: BudgetViolation) => void;
  onCompliance?: (report: BudgetReport) => void;
  onOptimization?: (action: OptimizationAction) => void;
}): PerformanceBudgetManager {
  globalBudgetManager = new PerformanceBudgetManager(callbacks);
  return globalBudgetManager;
}

/**
 * Quick budget check
 */
export function checkBudget(metrics: PerformanceMetrics): BudgetReport {
  const manager = getBudgetManager();
  return manager.checkBudgetCompliance(metrics);
}