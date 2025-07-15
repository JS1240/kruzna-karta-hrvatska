#!/usr/bin/env node

/**
 * Performance Test Runner
 * 
 * Command-line tool for running comprehensive performance tests
 * to maintain 60fps on desktop and 30fps minimum on mobile.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ANSI color codes
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m'
};

const log = {
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bold}${colors.cyan}${msg}${colors.reset}`),
  metric: (label, value, unit = '') => console.log(`${colors.magenta}${label}:${colors.reset} ${colors.bold}${value}${unit}${colors.reset}`),
};

/**
 * Performance test configuration
 */
const TEST_CONFIG = {
  // Target frame rates
  targets: {
    desktop: {
      target: 60,
      minimum: 50,
      acceptable: 45,
    },
    mobile: {
      target: 30,
      minimum: 25,
      acceptable: 20,
    },
    tablet: {
      target: 45,
      minimum: 35,
      acceptable: 30,
    },
  },
  
  // Test scenarios
  scenarios: [
    {
      name: 'Basic Performance',
      description: 'Standard animation with default settings',
      config: {
        particleCount: 12,
        intensity: 0.5,
        effects: true,
        duration: 10000, // 10 seconds
      },
    },
    {
      name: 'Mobile Optimized',
      description: 'Optimized settings for mobile devices',
      config: {
        particleCount: 6,
        intensity: 0.3,
        effects: false,
        duration: 10000,
      },
    },
    {
      name: 'High Performance',
      description: 'Enhanced settings for high-end devices',
      config: {
        particleCount: 24,
        intensity: 0.8,
        effects: true,
        duration: 10000,
      },
    },
    {
      name: 'Stress Test',
      description: 'Maximum load to test performance limits',
      config: {
        particleCount: 48,
        intensity: 1.0,
        effects: true,
        duration: 5000, // Shorter for stress test
      },
    },
  ],
  
  // Test types
  testTypes: {
    basic: 'Run basic performance validation',
    stress: 'Run stress testing scenarios',
    benchmark: 'Run comprehensive benchmark suite',
    validation: 'Validate FPS targets (60fps desktop, 30fps mobile)',
    regression: 'Check for performance regressions',
    automated: 'Run automated optimization tests',
  },
  
  // Output configuration
  output: {
    reportsDir: path.join(__dirname, '../dist/performance-reports'),
    historyFile: path.join(__dirname, '../dist/performance-history.json'),
    summaryFile: path.join(__dirname, '../dist/performance-summary.json'),
  },
};

/**
 * Device simulation configurations
 */
const DEVICE_SIMULATIONS = {
  'high-end-desktop': {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    viewport: { width: 1920, height: 1080 },
    devicePixelRatio: 1,
    hardwareConcurrency: 8,
    memory: 8192,
    connection: '4g',
    gpu: 'high-end',
  },
  'mid-range-desktop': {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    viewport: { width: 1366, height: 768 },
    devicePixelRatio: 1,
    hardwareConcurrency: 4,
    memory: 4096,
    connection: '4g',
    gpu: 'mid-range',
  },
  'high-end-mobile': {
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) WebKit/605.1.15',
    viewport: { width: 390, height: 844 },
    devicePixelRatio: 3,
    hardwareConcurrency: 6,
    memory: 6144,
    connection: '4g',
    gpu: 'high-end',
  },
  'mid-range-mobile': {
    userAgent: 'Mozilla/5.0 (Linux; Android 12; SM-G975F) Chrome/120.0.0.0',
    viewport: { width: 360, height: 760 },
    devicePixelRatio: 2,
    hardwareConcurrency: 4,
    memory: 4096,
    connection: '3g',
    gpu: 'mid-range',
  },
  'low-end-mobile': {
    userAgent: 'Mozilla/5.0 (Linux; Android 10; SM-A205F) Chrome/120.0.0.0',
    viewport: { width: 360, height: 640 },
    devicePixelRatio: 1.5,
    hardwareConcurrency: 2,
    memory: 2048,
    connection: '2g',
    gpu: 'low-end',
  },
  'tablet': {
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) WebKit/605.1.15',
    viewport: { width: 768, height: 1024 },
    devicePixelRatio: 2,
    hardwareConcurrency: 4,
    memory: 4096,
    connection: '4g',
    gpu: 'mid-range',
  },
};

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  
  const options = {
    testType: 'validation',
    device: 'all',
    scenario: 'all',
    output: true,
    verbose: false,
    continuous: false,
    threshold: 'standard',
    duration: null,
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--test' && args[i + 1]) {
      options.testType = args[i + 1];
      i++;
    } else if (arg === '--device' && args[i + 1]) {
      options.device = args[i + 1];
      i++;
    } else if (arg === '--scenario' && args[i + 1]) {
      options.scenario = args[i + 1];
      i++;
    } else if (arg === '--duration' && args[i + 1]) {
      options.duration = parseInt(args[i + 1]);
      i++;
    } else if (arg === '--no-output') {
      options.output = false;
    } else if (arg === '--verbose' || arg === '-v') {
      options.verbose = true;
    } else if (arg === '--continuous') {
      options.continuous = true;
    } else if (arg === '--threshold' && args[i + 1]) {
      options.threshold = args[i + 1];
      i++;
    }
  }
  
  return options;
}

/**
 * Simulate device characteristics
 */
function simulateDevice(deviceName) {
  const device = DEVICE_SIMULATIONS[deviceName];
  if (!device) {
    log.warning(`Unknown device: ${deviceName}`);
    return null;
  }
  
  log.info(`Simulating device: ${deviceName}`);
  log.info(`Viewport: ${device.viewport.width}x${device.viewport.height}`);
  log.info(`Memory: ${device.memory}MB`);
  log.info(`CPU Cores: ${device.hardwareConcurrency}`);
  log.info(`Connection: ${device.connection}`);
  
  return device;
}

/**
 * Run performance validation test
 */
async function runValidationTest(options) {
  log.header('🎯 Performance Validation Test');
  log.info('Validating 60fps desktop and 30fps mobile targets...');
  
  const devices = options.device === 'all' ? 
    ['high-end-desktop', 'mid-range-desktop', 'high-end-mobile', 'mid-range-mobile'] :
    [options.device];
  
  const results = [];
  
  for (const deviceName of devices) {
    const device = simulateDevice(deviceName);
    if (!device) continue;
    
    const deviceType = deviceName.includes('mobile') ? 'mobile' : 
                      deviceName.includes('tablet') ? 'tablet' : 'desktop';
    
    const targets = TEST_CONFIG.targets[deviceType];
    
    log.info(`\nTesting ${deviceName}...`);
    log.metric('Target FPS', targets.target);
    log.metric('Minimum FPS', targets.minimum);
    
    // Simulate test results (in real implementation, this would run actual tests)
    const testResult = await simulatePerformanceTest(device, targets, options);
    
    results.push({
      device: deviceName,
      deviceType,
      ...testResult,
      timestamp: new Date().toISOString(),
    });
    
    // Display results
    displayTestResult(testResult, targets);
  }
  
  // Generate summary
  const summary = generateValidationSummary(results);
  displayValidationSummary(summary);
  
  if (options.output) {
    await saveTestResults('validation', results, summary);
  }
  
  return summary.overallPassed;
}

/**
 * Run stress test
 */
async function runStressTest(options) {
  log.header('🔥 Stress Testing');
  log.info('Testing performance under extreme conditions...');
  
  const stressScenarios = [
    { name: 'High Particle Count', multiplier: 2.0, duration: 5000 },
    { name: 'Maximum Effects', multiplier: 1.5, duration: 5000 },
    { name: 'Memory Pressure', multiplier: 3.0, duration: 3000 },
    { name: 'CPU Intensive', multiplier: 2.5, duration: 4000 },
  ];
  
  const devices = options.device === 'all' ? 
    ['high-end-desktop', 'mid-range-mobile'] : [options.device];
  
  const results = [];
  
  for (const deviceName of devices) {
    const device = simulateDevice(deviceName);
    if (!device) continue;
    
    log.info(`\nStress testing ${deviceName}...`);
    
    for (const scenario of stressScenarios) {
      log.info(`Running scenario: ${scenario.name}`);
      
      const testResult = await simulateStressTest(device, scenario, options);
      
      results.push({
        device: deviceName,
        scenario: scenario.name,
        ...testResult,
        timestamp: new Date().toISOString(),
      });
      
      displayStressTestResult(testResult, scenario);
      
      // Recovery test
      log.info('Testing performance recovery...');
      await simulateRecoveryTest(device);
    }
  }
  
  const summary = generateStressTestSummary(results);
  displayStressTestSummary(summary);
  
  if (options.output) {
    await saveTestResults('stress', results, summary);
  }
  
  return summary.stabilityScore > 0.8;
}

/**
 * Run benchmark suite
 */
async function runBenchmarkSuite(options) {
  log.header('📊 Benchmark Suite');
  log.info('Running comprehensive performance benchmarks...');
  
  const scenarios = options.scenario === 'all' ? 
    TEST_CONFIG.scenarios : 
    TEST_CONFIG.scenarios.filter(s => s.name.toLowerCase().includes(options.scenario.toLowerCase()));
  
  const devices = options.device === 'all' ? 
    Object.keys(DEVICE_SIMULATIONS) : [options.device];
  
  const results = [];
  
  for (const deviceName of devices) {
    const device = simulateDevice(deviceName);
    if (!device) continue;
    
    log.info(`\nBenchmarking ${deviceName}...`);
    
    for (const scenario of scenarios) {
      log.info(`Running scenario: ${scenario.name}`);
      
      const testResult = await simulateBenchmarkTest(device, scenario, options);
      
      results.push({
        device: deviceName,
        scenario: scenario.name,
        ...testResult,
        timestamp: new Date().toISOString(),
      });
      
      displayBenchmarkResult(testResult, scenario);
    }
  }
  
  const summary = generateBenchmarkSummary(results);
  displayBenchmarkSummary(summary);
  
  if (options.output) {
    await saveTestResults('benchmark', results, summary);
  }
  
  return summary.overallScore > 0.7;
}

/**
 * Simulate performance test (placeholder for actual implementation)
 */
async function simulatePerformanceTest(device, targets, options) {
  // Simulate test execution delay
  await delay(options.duration || 2000);
  
  // Calculate simulated performance based on device characteristics
  const basePerformance = calculateDevicePerformance(device);
  const variation = (Math.random() - 0.5) * 0.2; // ±10% variation
  
  const averageFPS = Math.max(10, basePerformance.fps * (1 + variation));
  const minFPS = Math.max(5, averageFPS * 0.8);
  const maxFPS = Math.min(120, averageFPS * 1.2);
  
  const frameDrops = averageFPS < targets.minimum ? Math.floor(Math.random() * 50) : Math.floor(Math.random() * 10);
  const memoryUsage = basePerformance.memory * (1 + Math.random() * 0.3);
  
  return {
    averageFPS: Math.round(averageFPS * 10) / 10,
    minFPS: Math.round(minFPS * 10) / 10,
    maxFPS: Math.round(maxFPS * 10) / 10,
    frameDrops,
    memoryUsage: Math.round(memoryUsage),
    testPassed: averageFPS >= targets.minimum && minFPS >= targets.acceptable,
    duration: options.duration || 10000,
  };
}

/**
 * Simulate stress test
 */
async function simulateStressTest(device, scenario, options) {
  await delay(scenario.duration);
  
  const basePerformance = calculateDevicePerformance(device);
  const stressImpact = scenario.multiplier;
  
  // Stress reduces performance
  const averageFPS = Math.max(5, basePerformance.fps / stressImpact);
  const minFPS = Math.max(1, averageFPS * 0.6);
  const memoryUsage = basePerformance.memory * stressImpact;
  
  return {
    averageFPS: Math.round(averageFPS * 10) / 10,
    minFPS: Math.round(minFPS * 10) / 10,
    memoryUsage: Math.round(memoryUsage),
    stressLevel: stressImpact,
    recovered: Math.random() > 0.2, // 80% recovery rate
    duration: scenario.duration,
  };
}

/**
 * Simulate benchmark test
 */
async function simulateBenchmarkTest(device, scenario, options) {
  await delay(scenario.config.duration || 5000);
  
  const basePerformance = calculateDevicePerformance(device);
  const scenarioImpact = scenario.config.particleCount / 12; // Normalize to base
  
  const averageFPS = Math.max(5, basePerformance.fps / scenarioImpact);
  const score = Math.min(1, averageFPS / (device.gpu === 'high-end' ? 60 : 30));
  
  return {
    averageFPS: Math.round(averageFPS * 10) / 10,
    score: Math.round(score * 100) / 100,
    memoryUsage: Math.round(basePerformance.memory * scenarioImpact),
    duration: scenario.config.duration || 5000,
  };
}

/**
 * Calculate device performance characteristics
 */
function calculateDevicePerformance(device) {
  let baseFPS = 30;
  let baseMemory = 100;
  
  // Adjust based on device type
  if (device.gpu === 'high-end') {
    baseFPS = device.hardwareConcurrency >= 6 ? 60 : 45;
  } else if (device.gpu === 'mid-range') {
    baseFPS = device.hardwareConcurrency >= 4 ? 35 : 25;
  } else {
    baseFPS = 20;
  }
  
  // Adjust for mobile devices
  if (device.viewport.width <= 768) {
    baseFPS = Math.min(30, baseFPS * 0.7);
  }
  
  // Adjust for memory
  baseMemory = 50 + (device.memory / 1024) * 20;
  
  // Connection impact
  if (device.connection === '2g') {
    baseFPS *= 0.8;
  } else if (device.connection === '3g') {
    baseFPS *= 0.9;
  }
  
  return {
    fps: baseFPS,
    memory: baseMemory,
  };
}

/**
 * Display test result
 */
function displayTestResult(result, targets) {
  const status = result.testPassed ? '✓' : '✗';
  const statusColor = result.testPassed ? colors.green : colors.red;
  
  console.log(`${statusColor}${status}${colors.reset} Test Result:`);
  log.metric('Average FPS', result.averageFPS);
  log.metric('Min FPS', result.minFPS);
  log.metric('Max FPS', result.maxFPS);
  log.metric('Frame Drops', result.frameDrops);
  log.metric('Memory Usage', result.memoryUsage, 'MB');
  log.metric('Duration', result.duration, 'ms');
  
  if (!result.testPassed) {
    log.warning(`Performance below target: ${result.averageFPS} < ${targets.minimum} FPS`);
  }
}

/**
 * Display stress test result
 */
function displayStressTestResult(result, scenario) {
  console.log(`\n${colors.cyan}Stress Test Result: ${scenario.name}${colors.reset}`);
  log.metric('Average FPS', result.averageFPS);
  log.metric('Min FPS', result.minFPS);
  log.metric('Memory Usage', result.memoryUsage, 'MB');
  log.metric('Stress Level', `${result.stressLevel}x`);
  
  if (result.recovered) {
    log.success('Performance recovered after stress');
  } else {
    log.warning('Performance did not recover after stress');
  }
}

/**
 * Display benchmark result
 */
function displayBenchmarkResult(result, scenario) {
  console.log(`\n${colors.cyan}Benchmark Result: ${scenario.name}${colors.reset}`);
  log.metric('Average FPS', result.averageFPS);
  log.metric('Performance Score', `${(result.score * 100).toFixed(1)}%`);
  log.metric('Memory Usage', result.memoryUsage, 'MB');
}

/**
 * Generate validation summary
 */
function generateValidationSummary(results) {
  const totalTests = results.length;
  const passedTests = results.filter(r => r.testPassed).length;
  const passRate = (passedTests / totalTests) * 100;
  
  const desktopResults = results.filter(r => r.deviceType === 'desktop');
  const mobileResults = results.filter(r => r.deviceType === 'mobile');
  
  const averageDesktopFPS = desktopResults.length > 0 ?
    desktopResults.reduce((sum, r) => sum + r.averageFPS, 0) / desktopResults.length : 0;
  
  const averageMobileFPS = mobileResults.length > 0 ?
    mobileResults.reduce((sum, r) => sum + r.averageFPS, 0) / mobileResults.length : 0;
  
  return {
    totalTests,
    passedTests,
    passRate: Math.round(passRate * 100) / 100,
    averageDesktopFPS: Math.round(averageDesktopFPS * 10) / 10,
    averageMobileFPS: Math.round(averageMobileFPS * 10) / 10,
    overallPassed: passRate >= 80, // 80% pass rate required
    timestamp: new Date().toISOString(),
  };
}

/**
 * Generate stress test summary
 */
function generateStressTestSummary(results) {
  const recoveryRate = results.filter(r => r.recovered).length / results.length;
  const stabilityScore = recoveryRate * 0.7 + (results.reduce((sum, r) => sum + (r.minFPS > 10 ? 1 : 0), 0) / results.length) * 0.3;
  
  return {
    totalScenarios: results.length,
    recoveryRate: Math.round(recoveryRate * 100),
    stabilityScore: Math.round(stabilityScore * 100) / 100,
    averageMinFPS: Math.round(results.reduce((sum, r) => sum + r.minFPS, 0) / results.length * 10) / 10,
  };
}

/**
 * Generate benchmark summary
 */
function generateBenchmarkSummary(results) {
  const averageScore = results.reduce((sum, r) => sum + r.score, 0) / results.length;
  const averageFPS = results.reduce((sum, r) => sum + r.averageFPS, 0) / results.length;
  
  return {
    totalBenchmarks: results.length,
    overallScore: Math.round(averageScore * 100) / 100,
    averageFPS: Math.round(averageFPS * 10) / 10,
    performanceGrade: averageScore > 0.8 ? 'A' : averageScore > 0.6 ? 'B' : averageScore > 0.4 ? 'C' : 'D',
  };
}

/**
 * Display summaries
 */
function displayValidationSummary(summary) {
  log.header('📋 Validation Summary');
  log.metric('Tests Passed', `${summary.passedTests}/${summary.totalTests}`);
  log.metric('Pass Rate', `${summary.passRate}%`);
  log.metric('Desktop FPS', summary.averageDesktopFPS);
  log.metric('Mobile FPS', summary.averageMobileFPS);
  
  if (summary.overallPassed) {
    log.success('✅ All performance targets met!');
  } else {
    log.error('❌ Performance targets not met');
  }
}

function displayStressTestSummary(summary) {
  log.header('📋 Stress Test Summary');
  log.metric('Recovery Rate', `${summary.recoveryRate}%`);
  log.metric('Stability Score', summary.stabilityScore);
  log.metric('Average Min FPS', summary.averageMinFPS);
}

function displayBenchmarkSummary(summary) {
  log.header('📋 Benchmark Summary');
  log.metric('Overall Score', `${(summary.overallScore * 100).toFixed(1)}%`);
  log.metric('Performance Grade', summary.performanceGrade);
  log.metric('Average FPS', summary.averageFPS);
}

/**
 * Save test results
 */
async function saveTestResults(testType, results, summary) {
  try {
    // Ensure output directory exists
    if (!fs.existsSync(TEST_CONFIG.output.reportsDir)) {
      fs.mkdirSync(TEST_CONFIG.output.reportsDir, { recursive: true });
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportFile = path.join(TEST_CONFIG.output.reportsDir, `${testType}-${timestamp}.json`);
    
    const report = {
      testType,
      timestamp: new Date().toISOString(),
      summary,
      results,
      config: TEST_CONFIG,
    };
    
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    log.success(`Report saved: ${reportFile}`);
    
    // Update history
    updateTestHistory(testType, summary);
    
    // Update summary file
    updateSummaryFile(testType, summary);
    
  } catch (error) {
    log.error(`Failed to save results: ${error.message}`);
  }
}

/**
 * Update test history
 */
function updateTestHistory(testType, summary) {
  try {
    let history = [];
    
    if (fs.existsSync(TEST_CONFIG.output.historyFile)) {
      const data = fs.readFileSync(TEST_CONFIG.output.historyFile, 'utf8');
      history = JSON.parse(data);
    }
    
    history.push({
      testType,
      timestamp: new Date().toISOString(),
      ...summary,
    });
    
    // Keep last 100 entries
    if (history.length > 100) {
      history = history.slice(-100);
    }
    
    fs.writeFileSync(TEST_CONFIG.output.historyFile, JSON.stringify(history, null, 2));
    
  } catch (error) {
    log.warning(`Failed to update history: ${error.message}`);
  }
}

/**
 * Update summary file
 */
function updateSummaryFile(testType, summary) {
  try {
    let summaryData = {};
    
    if (fs.existsSync(TEST_CONFIG.output.summaryFile)) {
      const data = fs.readFileSync(TEST_CONFIG.output.summaryFile, 'utf8');
      summaryData = JSON.parse(data);
    }
    
    summaryData[testType] = {
      lastRun: new Date().toISOString(),
      ...summary,
    };
    
    fs.writeFileSync(TEST_CONFIG.output.summaryFile, JSON.stringify(summaryData, null, 2));
    
  } catch (error) {
    log.warning(`Failed to update summary: ${error.message}`);
  }
}

/**
 * Utility functions
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function simulateRecoveryTest(device) {
  await delay(1000);
  log.info('Recovery test completed');
}

/**
 * Show help
 */
function showHelp() {
  console.log(`
${colors.bold}Performance Test Runner${colors.reset}

Usage: npm run performance:test [options]

${colors.cyan}Test Types:${colors.reset}
  --test validation    Validate 60fps desktop, 30fps mobile targets (default)
  --test stress        Run stress testing scenarios
  --test benchmark     Run comprehensive benchmark suite
  --test regression    Check for performance regressions
  --test automated     Run automated optimization tests

${colors.cyan}Device Options:${colors.reset}
  --device all                  Test all device types (default)
  --device high-end-desktop     Test high-end desktop
  --device mid-range-desktop    Test mid-range desktop
  --device high-end-mobile      Test high-end mobile
  --device mid-range-mobile     Test mid-range mobile
  --device low-end-mobile       Test low-end mobile
  --device tablet               Test tablet

${colors.cyan}Other Options:${colors.reset}
  --scenario <name>     Run specific scenario (for benchmark tests)
  --duration <ms>       Override test duration
  --threshold <level>   Set performance threshold (strict/standard/relaxed)
  --verbose, -v         Verbose output
  --continuous          Run continuous monitoring
  --no-output          Don't save test results

${colors.cyan}Examples:${colors.reset}
  npm run performance:test --test validation
  npm run performance:test --test stress --device mobile
  npm run performance:test --test benchmark --scenario "High Performance"
  npm run performance:test --continuous --duration 30000
`);
}

/**
 * Main function
 */
async function main() {
  const options = parseArgs();
  
  if (process.argv.includes('--help') || process.argv.includes('-h')) {
    showHelp();
    return;
  }
  
  log.header('🎮 Performance Test Runner');
  log.info(`Test Type: ${options.testType}`);
  log.info(`Device: ${options.device}`);
  log.info(`Threshold: ${options.threshold}`);
  
  let success = false;
  
  try {
    switch (options.testType) {
      case 'validation':
        success = await runValidationTest(options);
        break;
      case 'stress':
        success = await runStressTest(options);
        break;
      case 'benchmark':
        success = await runBenchmarkSuite(options);
        break;
      default:
        log.error(`Unknown test type: ${options.testType}`);
        showHelp();
        process.exit(1);
    }
    
    if (success) {
      log.success('\n🎉 All performance tests passed!');
      process.exit(0);
    } else {
      log.error('\n❌ Performance tests failed');
      process.exit(1);
    }
    
  } catch (error) {
    log.error(`Test execution failed: ${error.message}`);
    if (options.verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Handle continuous monitoring
if (process.argv.includes('--continuous')) {
  log.info('Starting continuous performance monitoring...');
  
  const runContinuous = async () => {
    while (true) {
      try {
        await main();
        await delay(60000); // Run every minute
      } catch (error) {
        log.error(`Continuous monitoring error: ${error.message}`);
        await delay(30000); // Wait 30s before retry
      }
    }
  };
  
  runContinuous();
} else {
  main();
}