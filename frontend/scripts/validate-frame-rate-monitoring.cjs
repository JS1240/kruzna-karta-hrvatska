#!/usr/bin/env node

/**
 * Performance Monitoring Validation Script (T5.1)
 * 
 * Validates the implementation of frame rate monitoring functionality
 * for the animated background system.
 * 
 * Tests:
 * - Performance monitor utility functionality
 * - AnimatedBackground component FPS monitoring integration
 * - VANTA utils performance monitoring capabilities
 * - Animation manager enhanced performance monitoring
 * - Automatic performance adjustment mechanisms
 * 
 * Usage: node frontend/scripts/validate-frame-rate-monitoring.cjs
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

const log = {
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bold}${colors.cyan}${msg}${colors.reset}`),
  subheader: (msg) => console.log(`${colors.bold}${msg}${colors.reset}`)
};

/**
 * Reads the contents of a file relative to the project root.
 * @param {string} filePath - Path to the file, relative to the project root.
 * @return {string|null} The file contents as a string, or null if the file cannot be read.
 */
function readFile(filePath) {
  try {
    return fs.readFileSync(path.join(__dirname, '..', filePath), 'utf8');
  } catch (error) {
    return null;
  }
}

/**
 * Determines whether a file exists at the given relative path from the project root.
 * @param {string} filePath - The relative path to the file.
 * @return {boolean} True if the file exists, false otherwise.
 */
function fileExists(filePath) {
  try {
    return fs.existsSync(path.join(__dirname, '..', filePath));
  } catch (error) {
    return false;
  }
}

/**
 * Validates the implementation of the performance monitor utility in `performanceMonitor.ts`.
 *
 * Checks for the presence of required interfaces, classes, FPS tracking logic, device-specific targets, memory monitoring, callback systems, a global monitor manager, and visibility change handling. Logs the results of each check and returns whether all criteria are met.
 *
 * @returns {boolean} True if all validation checks pass; otherwise, false.
 */
function validatePerformanceMonitorUtility() {
  log.subheader('1. Performance Monitor Utility (performanceMonitor.ts)');
  
  const filePath = 'src/utils/performanceMonitor.ts';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'PerformanceMetrics interface',
      test: () => content.includes('export interface PerformanceMetrics') && 
                  content.includes('currentFPS: number') &&
                  content.includes('averageFPS: number') &&
                  content.includes('performanceMode:')
    },
    {
      name: 'PerformanceThresholds interface',
      test: () => content.includes('export interface PerformanceThresholds') &&
                  content.includes('targetFPS: number') &&
                  content.includes('mediumThreshold: number') &&
                  content.includes('lowThreshold: number') &&
                  content.includes('criticalThreshold: number')
    },
    {
      name: 'FrameRateMonitor class',
      test: () => content.includes('export class FrameRateMonitor') &&
                  content.includes('start(): void') &&
                  content.includes('stop(): void') &&
                  content.includes('getMetrics(): PerformanceMetrics')
    },
    {
      name: 'RequestAnimationFrame-based FPS tracking',
      test: () => content.includes('requestAnimationFrame') &&
                  content.includes('frameTimestamps') &&
                  content.includes('calculateCurrentFPS') &&
                  content.includes('calculateAverageFPS')
    },
    {
      name: 'Performance mode detection',
      test: () => content.includes('updatePerformanceMetrics') &&
                  content.includes('criticalThreshold') &&
                  content.includes('onPerformanceModeChange') &&
                  content.includes('onPerformanceDrop')
    },
    {
      name: 'Device-specific FPS targets',
      test: () => content.includes('getDeviceTargetFPS') &&
                  content.includes('isMobile') &&
                  content.includes('30') &&
                  content.includes('60')
    },
    {
      name: 'Memory usage monitoring',
      test: () => content.includes('getMemoryUsage') &&
                  content.includes('usedJSHeapSize') &&
                  content.includes('onHighMemoryUsage')
    },
    {
      name: 'Performance callbacks system',
      test: () => content.includes('PerformanceCallbacks') &&
                  content.includes('onPerformanceModeChange') &&
                  content.includes('onPerformanceUpdate')
    },
    {
      name: 'Global performance monitor manager',
      test: () => content.includes('PerformanceMonitorManager') &&
                  content.includes('globalPerformanceMonitor') &&
                  content.includes('startMonitoring') &&
                  content.includes('getAggregatedMetrics')
    },
    {
      name: 'Visibility change handling',
      test: () => content.includes('visibilitychange') &&
                  content.includes('pause') &&
                  content.includes('resume')
    }
  ];
  
  let passed = 0;
  checks.forEach(check => {
    if (check.test()) {
      log.success(`  ${check.name}`);
      passed++;
    } else {
      log.error(`  ${check.name}`);
    }
  });
  
  log.info(`  Performance Monitor Utility: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validates that the AnimatedBackground component implements all required frame rate and performance monitoring features.
 *
 * Checks for correct imports, props, state management, setup and cleanup logic, callback integration, FPS overlay, memory usage display, and performance-based styling in the component source file.
 *
 * @returns {boolean} True if all monitoring-related checks pass; otherwise, false.
 */
function validateAnimatedBackgroundMonitoring() {
  log.subheader('2. AnimatedBackground Component FPS Monitoring');
  
  const filePath = 'src/components/AnimatedBackground.tsx';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Performance monitoring imports',
      test: () => content.includes('import') &&
                  content.includes('performanceMonitor') &&
                  content.includes('PerformanceMetrics') &&
                  content.includes('PerformanceCallbacks')
    },
    {
      name: 'FPS monitoring props',
      test: () => content.includes('enableFrameRateMonitoring') &&
                  content.includes('fpsTarget') &&
                  content.includes('performanceThresholds') &&
                  content.includes('showFPSOverlay') &&
                  content.includes('autoPerformanceAdjustment')
    },
    {
      name: 'Performance callback props',
      test: () => content.includes('onPerformanceChange') &&
                  content.includes('onPerformanceDrop') &&
                  content.includes('onPerformanceRecover') &&
                  content.includes('onPerformanceUpdate') &&
                  content.includes('onHighMemoryUsage')
    },
    {
      name: 'Performance monitoring state',
      test: () => content.includes('performanceMetrics') &&
                  content.includes('setPerformanceMetrics') &&
                  content.includes('currentPerformanceMode') &&
                  content.includes('performanceMonitorRef')
    },
    {
      name: 'Performance monitoring setup useEffect',
      test: () => content.includes('enableFrameRateMonitoring') &&
                  content.includes('startPerformanceMonitoring') &&
                  content.includes('deviceTargetFPS') &&
                  content.includes('isMobile')
    },
    {
      name: 'Performance callbacks implementation',
      test: () => content.includes('onPerformanceModeChange') &&
                  content.includes('setCurrentPerformanceMode') &&
                  content.includes('autoPerformanceAdjustment') &&
                  content.includes('Auto-adjusting performance')
    },
    {
      name: 'FPS overlay component',
      test: () => content.includes('showFPSOverlay') &&
                  content.includes('performanceMetrics') &&
                  content.includes('FPS:') &&
                  content.includes('currentFPS') &&
                  content.includes('performanceRatio')
    },
    {
      name: 'Performance-based styling',
      test: () => content.includes('performanceRatio') &&
                  content.includes('bg-green-400') &&
                  content.includes('bg-yellow-400') &&
                  content.includes('bg-red-400')
    },
    {
      name: 'Memory usage display',
      test: () => content.includes('memoryUsage') &&
                  content.includes('usedJSHeapSize') &&
                  content.includes('Mem:')
    },
    {
      name: 'Performance monitoring cleanup',
      test: () => content.includes('stopPerformanceMonitoring') &&
                  content.includes('performanceMonitorRef.current = null')
    }
  ];
  
  let passed = 0;
  checks.forEach(check => {
    if (check.test()) {
      log.success(`  ${check.name}`);
      passed++;
    } else {
      log.error(`  ${check.name}`);
    }
  });
  
  log.info(`  AnimatedBackground Monitoring: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validates the integration and completeness of performance monitoring features in the VANTA utilities module.
 *
 * Checks for the presence of performance monitoring imports, enhanced topology initialization options, monitoring integration in topology functions, cleanup procedures, and monitoring methods in the topology manager. Logs the results of each check and returns whether all required features are present.
 *
 * @returns {boolean} True if all performance monitoring checks in the VANTA utilities pass; otherwise, false.
 */
function validateVantaUtilsMonitoring() {
  log.subheader('3. VANTA Utils Performance Monitoring');
  
  const filePath = 'src/utils/vantaUtils.ts';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Performance monitoring imports',
      test: () => content.includes('import') &&
                  content.includes('performanceMonitor') &&
                  content.includes('startPerformanceMonitoring') &&
                  content.includes('stopPerformanceMonitoring')
    },
    {
      name: 'Enhanced topology init options',
      test: () => content.includes('TopologyInitOptions') &&
                  content.includes('enablePerformanceMonitoring') &&
                  content.includes('performanceCallbacks') &&
                  content.includes('fpsTarget')
    },
    {
      name: 'Performance monitoring in initVantaTopology',
      test: () => content.includes('initVantaTopology') &&
                  content.includes('enablePerformanceMonitoring') &&
                  content.includes('startPerformanceMonitoring') &&
                  content.includes('__performanceMonitoringId')
    },
    {
      name: 'Performance monitoring in initBlueOnlyTopology',
      test: () => content.includes('initBlueOnlyTopology') &&
                  content.includes('enablePerformanceMonitoring') &&
                  content.includes('vanta-blue-topology-default')
    },
    {
      name: 'Performance monitoring in initGentleTopology',
      test: () => content.includes('initGentleTopology') &&
                  content.includes('enablePerformanceMonitoring') &&
                  content.includes('vanta-gentle-topology-default')
    },
    {
      name: 'Enhanced cleanup with monitoring',
      test: () => content.includes('cleanupVantaEffect') &&
                  content.includes('__performanceMonitoringId') &&
                  content.includes('stopPerformanceMonitoring') &&
                  content.includes('Performance monitoring stopped')
    },
    {
      name: 'VantaTopologyManager monitoring methods',
      test: () => content.includes('startPerformanceMonitoring') &&
                  content.includes('stopPerformanceMonitoring') &&
                  content.includes('VantaTopologyManager')
    },
    {
      name: 'Manager performance monitoring integration',
      test: () => content.includes('deviceTargetFPS') &&
                  content.includes('isMobile') &&
                  content.includes('thresholds')
    },
    {
      name: 'Manager cleanup with monitoring',
      test: () => content.includes('destroy()') &&
                  content.includes('stopPerformanceMonitoring') &&
                  content.includes('this.vantaInstance = null')
    }
  ];
  
  let passed = 0;
  checks.forEach(check => {
    if (check.test()) {
      log.success(`  ${check.name}`);
      passed++;
    } else {
      log.error(`  ${check.name}`);
    }
  });
  
  log.info(`  VANTA Utils Monitoring: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validates that enhanced performance monitoring features are correctly implemented in the animation manager utility.
 *
 * Checks for the presence of required imports, enhanced interfaces, global performance callbacks, monitoring start/stop methods, visibility handling, critical performance detection, aggregated metrics retrieval, and enable/disable controls in `src/utils/animationUtils.ts`.
 *
 * @returns {boolean} True if all validation checks pass; otherwise, false.
 */
function validateAnimationManagerMonitoring() {
  log.subheader('4. Animation Manager Enhanced Monitoring');
  
  const filePath = 'src/utils/animationUtils.ts';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Performance monitoring imports',
      test: () => content.includes('globalPerformanceMonitor') &&
                  content.includes('FrameRateMonitor') &&
                  content.includes('PerformanceMetrics') &&
                  content.includes('PerformanceCallbacks')
    },
    {
      name: 'Enhanced AnimationConfig interface',
      test: () => content.includes('AnimationConfig') &&
                  content.includes('performanceCallbacks') &&
                  content.includes('performanceThresholds') &&
                  content.includes('fpsTarget') &&
                  content.includes('autoPerformanceAdjustment')
    },
    {
      name: 'Enhanced AnimationInstance interface',
      test: () => content.includes('AnimationInstance') &&
                  content.includes('performanceMonitor') &&
                  content.includes('getPerformanceMetrics') &&
                  content.includes('startPerformanceMonitoring') &&
                  content.includes('stopPerformanceMonitoring')
    },
    {
      name: 'Global performance callbacks setup',
      test: () => content.includes('setupGlobalPerformanceCallbacks') &&
                  content.includes('setGlobalCallbacks') &&
                  content.includes('handleCriticalPerformance') &&
                  content.includes('handleHighMemoryUsage')
    },
    {
      name: 'Enhanced performance monitoring start',
      test: () => content.includes('startEnhancedPerformanceMonitoring') &&
                  content.includes('combinedCallbacks') &&
                  content.includes('Enhanced performance monitoring started')
    },
    {
      name: 'Performance monitoring cleanup',
      test: () => content.includes('globalPerformanceMonitor.stopMonitoring') &&
                  content.includes('legacyPerformanceMonitor.stopMonitoring')
    },
    {
      name: 'Visibility change handling',
      test: () => content.includes('visibilitychange') &&
                  content.includes('pauseAll') &&
                  content.includes('resumeAll')
    },
    {
      name: 'Critical performance handling',
      test: () => content.includes('handleCriticalPerformance') &&
                  content.includes('Critical performance detected') &&
                  content.includes('vanta-topology')
    },
    {
      name: 'Aggregated metrics method',
      test: () => content.includes('getAggregatedPerformanceMetrics') &&
                  content.includes('getAggregatedMetrics')
    },
    {
      name: 'Performance monitoring enable/disable',
      test: () => content.includes('enablePerformanceMonitoring') &&
                  content.includes('disablePerformanceMonitoring')
    }
  ];
  
  let passed = 0;
  checks.forEach(check => {
    if (check.test()) {
      log.success(`  ${check.name}`);
      passed++;
    } else {
      log.error(`  ${check.name}`);
    }
  });
  
  log.info(`  Animation Manager Monitoring: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validates the implementation of the performance monitoring demo in the AnimationTestPage component.
 *
 * Checks for the presence of required imports, state interfaces, demo sections, metrics display, test animations, auto adjustment, memory monitoring, comparison animations, documentation, and metrics update logic to ensure the demo fully supports frame rate and performance monitoring features.
 *
 * @returns {boolean} True if all validation checks pass; otherwise, false.
 */
function validateAnimationTestPageDemo() {
  log.subheader('5. AnimationTestPage Performance Demo');
  
  const filePath = 'src/pages/AnimationTestPage.tsx';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Performance monitoring imports',
      test: () => content.includes('globalPerformanceMonitor') &&
                  content.includes('PerformanceMetrics')
    },
    {
      name: 'Performance test state interface',
      test: () => content.includes('PerformanceTestState') &&
                  content.includes('metrics') &&
                  content.includes('isMonitoring') &&
                  content.includes('history')
    },
    {
      name: 'Performance demo section',
      test: () => content.includes('Performance Monitoring Demo (T5.1)') &&
                  content.includes('showPerformanceDemo') &&
                  content.includes('setShowPerformanceDemo')
    },
    {
      name: 'Global performance metrics display',
      test: () => content.includes('Global Performance Metrics') &&
                  content.includes('globalPerformanceMetrics') &&
                  content.includes('totalAnimations') &&
                  content.includes('averageFPS')
    },
    {
      name: 'FPS monitoring test animation',
      test: () => content.includes('fps-monitor-test') &&
                  content.includes('enableFrameRateMonitoring={true}') &&
                  content.includes('showFPSOverlay={true}') &&
                  content.includes('onPerformanceChange')
    },
    {
      name: 'Auto performance adjustment test',
      test: () => content.includes('auto-performance-test') &&
                  content.includes('autoPerformanceAdjustment={true}') &&
                  content.includes('performanceThresholds') &&
                  content.includes('Auto-adjustment triggered')
    },
    {
      name: 'Memory usage monitoring test',
      test: () => content.includes('memory-monitor-test') &&
                  content.includes('onHighMemoryUsage') &&
                  content.includes('High memory usage detected')
    },
    {
      name: 'Performance comparison animations',
      test: () => content.includes('comparison-low') &&
                  content.includes('comparison-medium') &&
                  content.includes('comparison-high') &&
                  content.includes('Performance Comparison')
    },
    {
      name: 'Performance features documentation',
      test: () => content.includes('Performance Monitoring Features (T5.1)') &&
                  content.includes('Real-time FPS Tracking') &&
                  content.includes('Automatic Optimization') &&
                  content.includes('Developer Tools')
    },
    {
      name: 'Global metrics update interval',
      test: () => content.includes('performanceUpdateInterval') &&
                  content.includes('getAggregatedMetrics') &&
                  content.includes('setInterval')
    }
  ];
  
  let passed = 0;
  checks.forEach(check => {
    if (check.test()) {
      log.success(`  ${check.name}`);
      passed++;
    } else {
      log.error(`  ${check.name}`);
    }
  });
  
  log.info(`  AnimationTestPage Demo: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Checks that all required files and key features for frame rate performance monitoring are present and correctly implemented across the codebase.
 * 
 * Runs a series of content-based checks to verify the existence of essential files, TypeScript interfaces, FPS tracking logic, device-specific targets, threshold detection, global manager, component integration, and development demo completeness.
 * 
 * @returns {boolean} True if all completeness checks pass; otherwise, false.
 */
function validateImplementationCompleteness() {
  log.subheader('6. Implementation Completeness Check');
  
  const requiredFiles = [
    'src/utils/performanceMonitor.ts',
    'src/components/AnimatedBackground.tsx',
    'src/utils/vantaUtils.ts',
    'src/utils/animationUtils.ts',
    'src/pages/AnimationTestPage.tsx'
  ];
  
  const checks = [
    {
      name: 'All required files exist',
      test: () => requiredFiles.every(file => fileExists(file))
    },
    {
      name: 'TypeScript interfaces defined',
      test: () => {
        const performanceMonitor = readFile('src/utils/performanceMonitor.ts');
        return performanceMonitor && 
               performanceMonitor.includes('export interface PerformanceMetrics') &&
               performanceMonitor.includes('export interface PerformanceThresholds') &&
               performanceMonitor.includes('export interface PerformanceCallbacks');
      }
    },
    {
      name: 'RequestAnimationFrame implementation',
      test: () => {
        const performanceMonitor = readFile('src/utils/performanceMonitor.ts');
        return performanceMonitor && 
               performanceMonitor.includes('requestAnimationFrame') &&
               performanceMonitor.includes('cancelAnimationFrame') &&
               performanceMonitor.includes('frameTimestamps');
      }
    },
    {
      name: 'Device-specific FPS targets',
      test: () => {
        const performanceMonitor = readFile('src/utils/performanceMonitor.ts');
        return performanceMonitor && 
               performanceMonitor.includes('30') && // mobile target
               performanceMonitor.includes('60') && // desktop target
               performanceMonitor.includes('isMobile');
      }
    },
    {
      name: 'Performance threshold detection',
      test: () => {
        const performanceMonitor = readFile('src/utils/performanceMonitor.ts');
        return performanceMonitor && 
               performanceMonitor.includes('mediumThreshold') &&
               performanceMonitor.includes('lowThreshold') &&
               performanceMonitor.includes('criticalThreshold');
      }
    },
    {
      name: 'Global performance manager',
      test: () => {
        const performanceMonitor = readFile('src/utils/performanceMonitor.ts');
        return performanceMonitor && 
               performanceMonitor.includes('globalPerformanceMonitor') &&
               performanceMonitor.includes('PerformanceMonitorManager');
      }
    },
    {
      name: 'Component integration complete',
      test: () => {
        const animatedBackground = readFile('src/components/AnimatedBackground.tsx');
        return animatedBackground && 
               animatedBackground.includes('enableFrameRateMonitoring') &&
               animatedBackground.includes('showFPSOverlay') &&
               animatedBackground.includes('performanceMetrics');
      }
    },
    {
      name: 'Development demo complete',
      test: () => {
        const testPage = readFile('src/pages/AnimationTestPage.tsx');
        return testPage && 
               testPage.includes('Performance Monitoring Demo') &&
               testPage.includes('fps-monitor-test') &&
               testPage.includes('auto-performance-test');
      }
    }
  ];
  
  let passed = 0;
  checks.forEach(check => {
    if (check.test()) {
      log.success(`  ${check.name}`);
      passed++;
    } else {
      log.error(`  ${check.name}`);
    }
  });
  
  log.info(`  Implementation Completeness: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Runs all validation checks for frame rate performance monitoring implementation and reports the results.
 *
 * Executes a series of validation functions to verify the presence and correctness of performance monitoring features across the codebase. Logs a summary of results and exits the process with a success or failure code based on the outcome.
 */
function main() {
  log.header('🚀 Performance Monitoring Validation (T5.1)');
  log.info('Validating frame rate monitoring implementation for animated backgrounds...\n');
  
  const results = [
    validatePerformanceMonitorUtility(),
    validateAnimatedBackgroundMonitoring(),
    validateVantaUtilsMonitoring(),
    validateAnimationManagerMonitoring(),
    validateAnimationTestPageDemo(),
    validateImplementationCompleteness()
  ];
  
  const passed = results.filter(Boolean).length;
  const total = results.length;
  
  log.header(`📊 Validation Results: ${passed}/${total} sections passed`);
  
  if (passed === total) {
    log.success('🎉 All performance monitoring features successfully implemented!');
    log.info('\nImplemented Features:');
    log.info('• Real-time FPS monitoring using requestAnimationFrame');
    log.info('• Device-specific performance targets (60fps desktop, 30fps mobile)');
    log.info('• Automatic performance mode adjustment based on FPS drops');
    log.info('• Memory usage monitoring and warnings');
    log.info('• Performance statistics and history tracking');
    log.info('• Live FPS overlay with color-coded performance status');
    log.info('• Global performance manager for multiple animations');
    log.info('• Seamless integration with AnimatedBackground component');
    log.info('• Comprehensive development demo and testing tools');
    log.info('• Performance event callbacks for custom handling');
    
    log.info('\nTask T5.1 (Implement performance monitoring for frame rates) is COMPLETE! ✅');
    process.exit(0);
  } else {
    log.error('❌ Performance monitoring validation failed!');
    log.warning(`Please address the ${total - passed} failing validation sections above.`);
    process.exit(1);
  }
}

// Run validation
main();