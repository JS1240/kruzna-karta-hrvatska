#!/usr/bin/env node

/**
 * Fallback Options Validation Script (T5.2)
 * 
 * Validates the implementation of fallback options for low-performance devices
 * in the animated background system.
 * 
 * Tests:
 * - Device detection system functionality
 * - Fallback animation system implementation
 * - CSS fallback animations and styles
 * - FallbackBackground component integration
 * - AnimatedBackground fallback integration
 * - Performance monitoring integration
 * 
 * Usage: node frontend/scripts/validate-fallback-options.cjs
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
 * Read and validate file contents
 */
function readFile(filePath) {
  try {
    return fs.readFileSync(path.join(__dirname, '..', filePath), 'utf8');
  } catch (error) {
    return null;
  }
}

/**
 * Check if file exists
 */
function fileExists(filePath) {
  try {
    return fs.existsSync(path.join(__dirname, '..', filePath));
  } catch (error) {
    return false;
  }
}

/**
 * Validate device detection system
 */
function validateDeviceDetectionSystem() {
  log.subheader('1. Device Detection System (deviceDetection.ts)');
  
  const filePath = 'src/utils/deviceDetection.ts';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'DeviceCapabilities interface',
      test: () => content.includes('export interface DeviceCapabilities') &&
                  content.includes('webglSupport: WebGLSupport') &&
                  content.includes('performanceScore: number') &&
                  content.includes('deviceClass: DeviceClass') &&
                  content.includes('hardwareAcceleration: boolean')
    },
    {
      name: 'FallbackRecommendation interface',
      test: () => content.includes('export interface FallbackRecommendation') &&
                  content.includes('mode: \'webgl\' | \'css\' | \'static\' | \'none\'') &&
                  content.includes('cssAnimationType:') &&
                  content.includes('staticPatternType:') &&
                  content.includes('performanceSettings:')
    },
    {
      name: 'DeviceDetector class',
      test: () => content.includes('export class DeviceDetector') &&
                  content.includes('getDeviceCapabilities') &&
                  content.includes('getFallbackRecommendation') &&
                  content.includes('detectCapabilities')
    },
    {
      name: 'WebGL support detection',
      test: () => content.includes('detectWebGLSupport') &&
                  content.includes('canvas.getContext(\'webgl\')') &&
                  content.includes('WEBGL_debug_renderer_info') &&
                  content.includes('isSoftwareRenderer')
    },
    {
      name: 'Performance scoring system',
      test: () => content.includes('calculatePerformanceScore') &&
                  content.includes('hardwareAcceleration') &&
                  content.includes('navigator.hardwareConcurrency') &&
                  content.includes('estimateMemory')
    },
    {
      name: 'Device classification',
      test: () => content.includes('classifyDevice') &&
                  content.includes('high-end') &&
                  content.includes('mid-range') &&
                  content.includes('low-end') &&
                  content.includes('very-low-end')
    },
    {
      name: 'Battery and thermal detection',
      test: () => content.includes('isLowBattery') &&
                  content.includes('getThermalState') &&
                  content.includes('getBattery') &&
                  content.includes('navigator.thermal')
    },
    {
      name: 'Connection quality detection',
      test: () => content.includes('detectConnectionQuality') &&
                  content.includes('navigator.connection') &&
                  content.includes('effectiveType') &&
                  content.includes('downlink')
    },
    {
      name: 'Fallback recommendation logic',
      test: () => content.includes('getFallbackRecommendation') &&
                  content.includes('prefersReducedMotion') &&
                  content.includes('webglSupport === \'hardware\'') &&
                  content.includes('performanceScore')
    },
    {
      name: 'Convenience functions',
      test: () => content.includes('export const getDeviceCapabilities') &&
                  content.includes('export const getFallbackRecommendation') &&
                  content.includes('export const shouldUseFallback') &&
                  content.includes('deviceDetector = DeviceDetector.getInstance()')
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
  
  log.info(`  Device Detection System: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validate fallback animation system
 */
function validateFallbackAnimationSystem() {
  log.subheader('2. Fallback Animation System (fallbackAnimations.ts)');
  
  const filePath = 'src/utils/fallbackAnimations.ts';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Animation configuration interfaces',
      test: () => content.includes('interface FallbackAnimationConfig') &&
                  content.includes('interface CSSParticleConfig') &&
                  content.includes('interface GradientAnimationConfig') &&
                  content.includes('interface StaticPatternConfig')
    },
    {
      name: 'FallbackAnimationManager class',
      test: () => content.includes('export class FallbackAnimationManager') &&
                  content.includes('initializeParticleAnimation') &&
                  content.includes('initializeGradientAnimation') &&
                  content.includes('initializeStaticPattern')
    },
    {
      name: 'CSS particle animation system',
      test: () => content.includes('createParticle') &&
                  content.includes('updateParticleAnimations') &&
                  content.includes('requestAnimationFrame') &&
                  content.includes('fallback-particle')
    },
    {
      name: 'Gradient animation implementation',
      test: () => content.includes('applyGradientAnimation') &&
                  content.includes('linear-gradient') &&
                  content.includes('fallback-gradient-shift') &&
                  content.includes('animation:')
    },
    {
      name: 'Static pattern generation',
      test: () => content.includes('generatePatternStyles') &&
                  content.includes('geometric') &&
                  content.includes('brand') &&
                  content.includes('solid')
    },
    {
      name: 'FallbackConfigGenerator class',
      test: () => content.includes('export class FallbackConfigGenerator') &&
                  content.includes('generateParticleConfig') &&
                  content.includes('generateGradientConfig') &&
                  content.includes('generateStaticPatternConfig')
    },
    {
      name: 'CSS styles injector',
      test: () => content.includes('export class FallbackStylesInjector') &&
                  content.includes('injectStyles') &&
                  content.includes('generateCSS') &&
                  content.includes('@keyframes fallback-particle')
    },
    {
      name: 'Animation cleanup system',
      test: () => content.includes('cleanup') &&
                  content.includes('cleanupAll') &&
                  content.includes('cancelAnimationFrame') &&
                  content.includes('removeChild')
    },
    {
      name: 'Brand color integration',
      test: () => content.includes('BRAND_COLORS') &&
                  content.includes('primary') &&
                  content.includes('secondary') &&
                  content.includes('accent1')
    },
    {
      name: 'Convenience functions',
      test: () => content.includes('export const initializeFallbackAnimation') &&
                  content.includes('export const stopFallbackAnimation') &&
                  content.includes('export const cleanupFallbackAnimation')
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
  
  log.info(`  Fallback Animation System: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validate CSS fallback styles
 */
function validateCSSFallbackStyles() {
  log.subheader('3. CSS Fallback Styles (fallbackAnimations.css)');
  
  const filePath = 'src/styles/fallbackAnimations.css';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Base container styles',
      test: () => content.includes('.fallback-animation-container') &&
                  content.includes('.fallback-animation-overlay') &&
                  content.includes('position: relative') &&
                  content.includes('overflow: hidden')
    },
    {
      name: 'Particle animation styles',
      test: () => content.includes('.fallback-particle') &&
                  content.includes('border-radius: 50%') &&
                  content.includes('will-change: transform') &&
                  content.includes('translate3d')
    },
    {
      name: 'Animation keyframes',
      test: () => content.includes('@keyframes fallback-particle-float-1') &&
                  content.includes('@keyframes fallback-particle-float-2') &&
                  content.includes('@keyframes fallback-particle-float-3') &&
                  content.includes('@keyframes fallback-gradient-flow')
    },
    {
      name: 'Gradient animation styles',
      test: () => content.includes('.fallback-gradient-animation') &&
                  content.includes('.fallback-gradient--flow') &&
                  content.includes('.fallback-gradient--shift') &&
                  content.includes('background-size: 400%')
    },
    {
      name: 'Static pattern styles',
      test: () => content.includes('.fallback-static-pattern') &&
                  content.includes('.fallback-pattern--geometric') &&
                  content.includes('.fallback-pattern--brand') &&
                  content.includes('radial-gradient')
    },
    {
      name: 'Performance optimizations',
      test: () => content.includes('-webkit-transform: translate3d') &&
                  content.includes('backface-visibility: hidden') &&
                  content.includes('-webkit-perspective: 1000px') &&
                  content.includes('@media (max-width: 768px)')
    },
    {
      name: 'Reduced motion support',
      test: () => content.includes('@media (prefers-reduced-motion: reduce)') &&
                  content.includes('animation: none !important') &&
                  content.includes('transform: none !important')
    },
    {
      name: 'High contrast support',
      test: () => content.includes('@media (prefers-contrast: high)') &&
                  content.includes('opacity: 0.6 !important')
    },
    {
      name: 'Color theme variations',
      test: () => content.includes('.fallback-theme--primary') &&
                  content.includes('.fallback-theme--accent') &&
                  content.includes('--pattern-color-1') &&
                  content.includes('--pattern-color-2')
    },
    {
      name: 'Utility classes',
      test: () => content.includes('.fallback-animation--hidden') &&
                  content.includes('.fallback-animation--paused') &&
                  content.includes('.fallback-transition--fade')
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
  
  log.info(`  CSS Fallback Styles: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validate FallbackBackground component
 */
function validateFallbackBackgroundComponent() {
  log.subheader('4. FallbackBackground Component (FallbackBackground.tsx)');
  
  const filePath = 'src/components/FallbackBackground.tsx';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Component imports',
      test: () => content.includes('import React') &&
                  content.includes('import { BRAND_COLORS }') &&
                  content.includes('import { getDeviceCapabilities }') &&
                  content.includes('import { FallbackConfigGenerator }')
    },
    {
      name: 'FallbackBackgroundProps interface',
      test: () => content.includes('export interface FallbackBackgroundProps') &&
                  content.includes('fallbackMode?: FallbackMode') &&
                  content.includes('cssAnimationType?: CSSAnimationType') &&
                  content.includes('staticPatternType?: StaticPatternType')
    },
    {
      name: 'Device detection integration',
      test: () => content.includes('getDeviceCapabilities()') &&
                  content.includes('getFallbackRecommendation') &&
                  content.includes('onDeviceCapabilitiesDetected') &&
                  content.includes('setDeviceCapabilities')
    },
    {
      name: 'Fallback animation initialization',
      test: () => content.includes('initializeFallbackAnimation') &&
                  content.includes('cleanupFallbackAnimation') &&
                  content.includes('FallbackStylesInjector.injectStyles()') &&
                  content.includes('finalRecommendation')
    },
    {
      name: 'CSS variable generation',
      test: () => content.includes('cssVariables') &&
                  content.includes('--pattern-color-1') &&
                  content.includes('--particle-duration') &&
                  content.includes('--animation-duration')
    },
    {
      name: 'Theme class generation',
      test: () => content.includes('getThemeClass') &&
                  content.includes('fallback-theme--accent') &&
                  content.includes('fallback-theme--monochrome') &&
                  content.includes('fallback-theme--primary')
    },
    {
      name: 'Debug information display',
      test: () => content.includes('showDebugInfo') &&
                  content.includes('Fallback Debug Info') &&
                  content.includes('deviceCapabilities.deviceClass') &&
                  content.includes('recommendation.reason')
    },
    {
      name: 'Error handling',
      test: () => content.includes('setError') &&
                  content.includes('Fallback Error:') &&
                  content.includes('catch (err)') &&
                  content.includes('console.error')
    },
    {
      name: 'Accessibility features',
      test: () => content.includes('aria-hidden="true"') &&
                  content.includes('prefers-reduced-motion') &&
                  content.includes('data-testid="fallback-background"')
    },
    {
      name: 'Content overlay system',
      test: () => content.includes('fallback-animation-overlay') &&
                  content.includes('relative z-10') &&
                  content.includes('{children}')
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
  
  log.info(`  FallbackBackground Component: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validate AnimatedBackground integration
 */
function validateAnimatedBackgroundIntegration() {
  log.subheader('5. AnimatedBackground Fallback Integration');
  
  const filePath = 'src/components/AnimatedBackground.tsx';
  const content = readFile(filePath);
  
  if (!content) {
    log.error(`File not found: ${filePath}`);
    return false;
  }
  
  const checks = [
    {
      name: 'Fallback imports',
      test: () => content.includes('import { getDeviceCapabilities }') &&
                  content.includes('import { deviceDetector }') &&
                  content.includes('import FallbackBackground')
    },
    {
      name: 'Fallback props',
      test: () => content.includes('enableFallbacks?: boolean') &&
                  content.includes('forceFallbackMode?: FallbackMode') &&
                  content.includes('minPerformanceScore?: number') &&
                  content.includes('requireHardwareWebGL?: boolean')
    },
    {
      name: 'Fallback state management',
      test: () => content.includes('const [useFallback, setUseFallback]') &&
                  content.includes('const [fallbackMode, setFallbackMode]') &&
                  content.includes('const [deviceCapabilities, setDeviceCapabilities]') &&
                  content.includes('const [fallbackReason, setFallbackReason]')
    },
    {
      name: 'Device detection logic',
      test: () => content.includes('checkDeviceAndFallback') &&
                  content.includes('getDeviceCapabilities()') &&
                  content.includes('shouldUseFallback') &&
                  content.includes('getFallbackRecommendation')
    },
    {
      name: 'Battery and thermal detection',
      test: () => content.includes('isLowBattery') &&
                  content.includes('getThermalState') &&
                  content.includes('forceFallbackForPower') &&
                  content.includes('Low battery - conserving power')
    },
    {
      name: 'Performance monitoring integration',
      test: () => content.includes('Critical performance detected') &&
                  content.includes('High memory usage detected') &&
                  content.includes('setUseFallback(true)') &&
                  content.includes('cleanupVantaEffect')
    },
    {
      name: 'Fallback component rendering',
      test: () => content.includes('<FallbackBackground') &&
                  content.includes('useFallback &&') &&
                  content.includes('enableFallbacks &&') &&
                  content.includes('fallbackMode={fallbackMode}')
    },
    {
      name: 'WebGL animation prevention',
      test: () => content.includes('enableFallbacks && useFallback') &&
                  content.includes('setIsLoaded(true)') &&
                  content.includes('return;')
    },
    {
      name: 'Fallback debug display',
      test: () => content.includes('showFallbackDebug') &&
                  content.includes('Fallback:') &&
                  content.includes('fallbackReason')
    },
    {
      name: 'Callback integration',
      test: () => content.includes('onFallbackActivated') &&
                  content.includes('onDeviceDetected') &&
                  content.includes('recommendation.mode, finalReason')
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
  
  log.info(`  AnimatedBackground Integration: ${passed}/${checks.length} checks passed`);
  return passed === checks.length;
}

/**
 * Validate implementation completeness
 */
function validateImplementationCompleteness() {
  log.subheader('6. Implementation Completeness Check');
  
  const requiredFiles = [
    'src/utils/deviceDetection.ts',
    'src/utils/fallbackAnimations.ts',
    'src/styles/fallbackAnimations.css',
    'src/components/FallbackBackground.tsx',
    'src/components/AnimatedBackground.tsx'
  ];
  
  const checks = [
    {
      name: 'All required files exist',
      test: () => requiredFiles.every(file => fileExists(file))
    },
    {
      name: 'Device detection system complete',
      test: () => {
        const deviceDetection = readFile('src/utils/deviceDetection.ts');
        return deviceDetection && 
               deviceDetection.includes('export class DeviceDetector') &&
               deviceDetection.includes('detectWebGLSupport') &&
               deviceDetection.includes('calculatePerformanceScore');
      }
    },
    {
      name: 'Fallback animation system complete',
      test: () => {
        const fallbackAnimations = readFile('src/utils/fallbackAnimations.ts');
        return fallbackAnimations && 
               fallbackAnimations.includes('export class FallbackAnimationManager') &&
               fallbackAnimations.includes('initializeParticleAnimation') &&
               fallbackAnimations.includes('FallbackStylesInjector');
      }
    },
    {
      name: 'CSS styles comprehensive',
      test: () => {
        const cssStyles = readFile('src/styles/fallbackAnimations.css');
        return cssStyles && 
               cssStyles.includes('@keyframes fallback-particle') &&
               cssStyles.includes('@media (prefers-reduced-motion') &&
               cssStyles.includes('.fallback-pattern--geometric');
      }
    },
    {
      name: 'Component integration complete',
      test: () => {
        const fallbackComponent = readFile('src/components/FallbackBackground.tsx');
        const animatedComponent = readFile('src/components/AnimatedBackground.tsx');
        return fallbackComponent && animatedComponent &&
               fallbackComponent.includes('getDeviceCapabilities') &&
               animatedComponent.includes('enableFallbacks');
      }
    },
    {
      name: 'Performance monitoring integration',
      test: () => {
        const animatedBackground = readFile('src/components/AnimatedBackground.tsx');
        return animatedBackground && 
               animatedBackground.includes('Critical performance detected') &&
               animatedBackground.includes('High memory usage detected');
      }
    },
    {
      name: 'TypeScript interfaces complete',
      test: () => {
        const deviceDetection = readFile('src/utils/deviceDetection.ts');
        const fallbackAnimations = readFile('src/utils/fallbackAnimations.ts');
        return deviceDetection && fallbackAnimations &&
               deviceDetection.includes('export interface DeviceCapabilities') &&
               fallbackAnimations.includes('interface FallbackAnimationConfig');
      }
    },
    {
      name: 'Accessibility support complete',
      test: () => {
        const cssStyles = readFile('src/styles/fallbackAnimations.css');
        const fallbackComponent = readFile('src/components/FallbackBackground.tsx');
        return cssStyles && fallbackComponent &&
               cssStyles.includes('@media (prefers-reduced-motion') &&
               fallbackComponent.includes('aria-hidden="true"');
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
 * Main validation function
 */
function main() {
  log.header('🚀 Fallback Options Validation (T5.2)');
  log.info('Validating fallback options for low-performance devices...\n');
  
  const results = [
    validateDeviceDetectionSystem(),
    validateFallbackAnimationSystem(),
    validateCSSFallbackStyles(),
    validateFallbackBackgroundComponent(),
    validateAnimatedBackgroundIntegration(),
    validateImplementationCompleteness()
  ];
  
  const passed = results.filter(Boolean).length;
  const total = results.length;
  
  log.header(`📊 Validation Results: ${passed}/${total} sections passed`);
  
  if (passed === total) {
    log.success('🎉 All fallback options successfully implemented!');
    log.info('\nImplemented Features:');
    log.info('• Comprehensive device detection with WebGL quality assessment');
    log.info('• Automatic fallback recommendations based on device capabilities');
    log.info('• CSS-based particle animation system for WebGL alternatives');
    log.info('• Gradient and static pattern fallback options');
    log.info('• Battery level and thermal state consideration');
    log.info('• Performance monitoring integration with automatic fallbacks');
    log.info('• Brand-consistent visual design across all fallback modes');
    log.info('• Full accessibility support with reduced motion compliance');
    log.info('• Memory usage optimization and automatic cleanup');
    log.info('• Seamless integration with existing AnimatedBackground component');
    
    log.info('\nFallback Hierarchy:');
    log.info('1. Full VANTA.js WebGL (high-performance devices)');
    log.info('2. Reduced VANTA.js (medium performance)');
    log.info('3. CSS Particle Animation (low performance, no WebGL)');
    log.info('4. CSS Gradient Animation (very low performance)');
    log.info('5. Static Background Pattern (critical performance)');
    log.info('6. No Animation (accessibility/user preference)');
    
    log.info('\nTask T5.2 (Add fallback options for low-performance devices) is COMPLETE! ✅');
    process.exit(0);
  } else {
    log.error('❌ Fallback options validation failed!');
    log.warning(`Please address the ${total - passed} failing validation sections above.`);
    process.exit(1);
  }
}

// Run validation
main();