/**
 * Mobile Browser Performance and Compatibility Optimizations
 * 
 * Specialized optimizations for mobile browsers including iOS Safari,
 * Chrome Mobile, Firefox Mobile, and Samsung Internet
 */

import { detectBrowser, type BrowserInfo } from './browserCompatibility';
import { loadSpecificPolyfill } from './polyfills';

export interface MobileOptimizationConfig {
  enableBatteryOptimization: boolean;
  enableThermalThrottling: boolean;
  enableMemoryConservation: boolean;
  enableTouchOptimization: boolean;
  enableViewportOptimization: boolean;
  enableNetworkOptimization: boolean;
  aggressivePowerSaving: boolean;
  debug: boolean;
}

export interface MobileCapabilities {
  isMobile: boolean;
  isTablet: boolean;
  platform: string;
  touchSupport: boolean;
  batteryAPI: boolean;
  deviceMemory: number;
  hardwareConcurrency: number;
  connectionType: string;
  reducedData: boolean;
  isLowEndDevice: boolean;
  recommendedSettings: {
    maxParticles: number;
    animationDuration: number;
    enableWebGL: boolean;
    enableComplexAnimations: boolean;
    maxFPS: number;
  };
}

let mobileCapabilities: MobileCapabilities | null = null;
let optimizationListeners: (() => void)[] = [];

/**
 * Detect mobile capabilities and performance characteristics
 */
export async function detectMobileCapabilities(): Promise<MobileCapabilities> {
  if (mobileCapabilities) {
    return mobileCapabilities;
  }

  const browser = detectBrowser();
  const userAgent = navigator.userAgent.toLowerCase();
  
  // Device detection
  const isMobile = /android|webos|iphone|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
  const isTablet = /ipad|android(?!.*mobile)|tablet/i.test(userAgent);
  
  // Platform detection
  let platform = 'unknown';
  if (/iphone|ipod|ipad/i.test(userAgent)) platform = 'ios';
  else if (/android/i.test(userAgent)) platform = 'android';
  else if (/windows phone/i.test(userAgent)) platform = 'windows';
  
  // Touch support
  const touchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  // Battery API
  const batteryAPI = 'getBattery' in navigator;
  
  // Device memory (Chrome feature)
  const deviceMemory = (navigator as any).deviceMemory || 4; // Default to 4GB if unknown
  
  // Hardware concurrency
  const hardwareConcurrency = navigator.hardwareConcurrency || 2;
  
  // Network information
  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
  const connectionType = connection?.effectiveType || 'unknown';
  const reducedData = connection?.saveData || false;
  
  // Low-end device detection
  const isLowEndDevice = (
    deviceMemory <= 2 || 
    hardwareConcurrency <= 2 || 
    connectionType === 'slow-2g' || 
    connectionType === '2g' ||
    reducedData
  );
  
  // Generate recommended settings
  const recommendedSettings = generateMobileSettings(
    isMobile,
    isTablet,
    platform,
    deviceMemory,
    hardwareConcurrency,
    isLowEndDevice,
    browser
  );

  mobileCapabilities = {
    isMobile,
    isTablet,
    platform,
    touchSupport,
    batteryAPI,
    deviceMemory,
    hardwareConcurrency,
    connectionType,
    reducedData,
    isLowEndDevice,
    recommendedSettings,
  };

  return mobileCapabilities;
}

/**
 * Generate optimal settings for mobile devices
 */
function generateMobileSettings(
  isMobile: boolean,
  isTablet: boolean,
  platform: string,
  deviceMemory: number,
  hardwareConcurrency: number,
  isLowEndDevice: boolean,
  browser: BrowserInfo
): MobileCapabilities['recommendedSettings'] {
  let maxParticles = 50;
  let animationDuration = 15000; // 15 seconds
  let enableWebGL = true;
  let enableComplexAnimations = true;
  let maxFPS = 60;

  // Base mobile adjustments
  if (isMobile) {
    maxParticles = 25;
    animationDuration = 20000; // 20 seconds
    maxFPS = 30;
  }

  // Platform-specific adjustments
  if (platform === 'ios') {
    // iOS optimizations
    if (browser.majorVersion < 14) {
      enableWebGL = false; // WebGL issues on older iOS
      maxParticles = 15;
    }
    
    // iOS Safari memory constraints
    if (deviceMemory <= 3) {
      maxParticles = Math.floor(maxParticles * 0.6);
      enableComplexAnimations = false;
    }
  } else if (platform === 'android') {
    // Android optimizations
    if (deviceMemory <= 2) {
      enableWebGL = false; // Low memory Android devices
      maxParticles = 10;
      enableComplexAnimations = false;
    }
    
    // Chrome Mobile optimizations
    if (browser.name === 'Chrome' && deviceMemory >= 4) {
      maxParticles = Math.min(40, maxParticles * 1.2);
    }
  }

  // Low-end device overrides
  if (isLowEndDevice) {
    maxParticles = Math.min(10, maxParticles);
    animationDuration = 30000; // 30 seconds
    enableWebGL = false;
    enableComplexAnimations = false;
    maxFPS = 20;
  }

  // Tablet adjustments
  if (isTablet && !isLowEndDevice) {
    maxParticles = Math.floor(maxParticles * 1.5);
    animationDuration = Math.floor(animationDuration * 0.8);
    maxFPS = 45;
  }

  // Hardware-based adjustments
  if (hardwareConcurrency >= 6 && deviceMemory >= 6) {
    // High-end device
    maxParticles = Math.floor(maxParticles * 1.3);
    maxFPS = isMobile ? 45 : 60;
  }

  return {
    maxParticles: Math.max(5, maxParticles),
    animationDuration: Math.max(10000, animationDuration),
    enableWebGL,
    enableComplexAnimations,
    maxFPS: Math.max(15, maxFPS),
  };
}

/**
 * Apply mobile-specific optimizations
 */
export async function applyMobileOptimizations(
  config: Partial<MobileOptimizationConfig> = {}
): Promise<void> {
  const defaultConfig: MobileOptimizationConfig = {
    enableBatteryOptimization: true,
    enableThermalThrottling: true,
    enableMemoryConservation: true,
    enableTouchOptimization: true,
    enableViewportOptimization: true,
    enableNetworkOptimization: true,
    aggressivePowerSaving: false,
    debug: false,
    ...config,
  };

  const capabilities = await detectMobileCapabilities();
  
  if (!capabilities.isMobile && !capabilities.isTablet) {
    if (defaultConfig.debug) {
      console.log('Desktop device detected, skipping mobile optimizations');
    }
    return;
  }

  if (defaultConfig.debug) {
    console.log('Applying mobile optimizations:', capabilities);
  }

  // Apply viewport optimizations
  if (defaultConfig.enableViewportOptimization) {
    await applyViewportOptimizations(capabilities, defaultConfig.debug);
  }

  // Apply touch optimizations
  if (defaultConfig.enableTouchOptimization) {
    await applyTouchOptimizations(capabilities, defaultConfig.debug);
  }

  // Apply battery optimizations
  if (defaultConfig.enableBatteryOptimization) {
    await applyBatteryOptimizations(capabilities, defaultConfig.debug);
  }

  // Apply thermal throttling
  if (defaultConfig.enableThermalThrottling) {
    await applyThermalOptimizations(capabilities, defaultConfig.debug);
  }

  // Apply memory conservation
  if (defaultConfig.enableMemoryConservation) {
    await applyMemoryConservation(capabilities, defaultConfig.debug);
  }

  // Apply network optimizations
  if (defaultConfig.enableNetworkOptimization) {
    await applyNetworkOptimizations(capabilities, defaultConfig.debug);
  }

  // Apply aggressive power saving if enabled
  if (defaultConfig.aggressivePowerSaving) {
    await applyAggressivePowerSaving(capabilities, defaultConfig.debug);
  }
}

/**
 * Apply viewport and layout optimizations for mobile
 */
async function applyViewportOptimizations(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-mobile-optimizations', 'viewport');
  
  let css = `
    /* Mobile viewport optimizations */
    @media screen and (max-width: 768px) {
      .animation-container {
        -webkit-transform: translate3d(0, 0, 0);
        transform: translate3d(0, 0, 0);
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
      }
      
      /* Reduce repaints on mobile */
      .fallback-particle,
      .vanta-canvas {
        will-change: transform;
      }
    }
  `;

  // iOS Safari specific viewport fixes
  if (capabilities.platform === 'ios') {
    css += `
      /* iOS Safari viewport fixes */
      body {
        -webkit-overflow-scrolling: touch;
        -webkit-touch-callout: none;
        -webkit-user-select: none;
      }
      
      .animation-container {
        -webkit-transform: translate3d(0, 0, 0);
        -webkit-perspective: 1000px;
      }
      
      /* Fix iOS zoom issues */
      @media screen and (max-device-width: 767px) {
        .animation-container {
          position: fixed;
          width: 100vw;
          height: 100vh;
        }
      }
    `;
  }

  // Android specific optimizations
  if (capabilities.platform === 'android') {
    css += `
      /* Android Chrome optimizations */
      .animation-container {
        contain: layout style paint;
      }
      
      /* Fix Android scrolling issues */
      .fallback-animation-container {
        overscroll-behavior: none;
      }
    `;
  }

  styleSheet.textContent = css;
  document.head.appendChild(styleSheet);

  if (debug) {
    console.log('Applied viewport optimizations for', capabilities.platform);
  }
}

/**
 * Apply touch-specific optimizations
 */
async function applyTouchOptimizations(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  if (!capabilities.touchSupport) return;

  // Load touch polyfills if needed
  await loadSpecificPolyfill('requestAnimationFrame', debug);

  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-mobile-optimizations', 'touch');
  
  const css = `
    /* Touch optimizations */
    .touch-optimized {
      touch-action: manipulation;
      -webkit-tap-highlight-color: transparent;
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      user-select: none;
    }
    
    /* Improve touch responsiveness */
    .animation-container {
      pointer-events: auto;
    }
    
    .animation-container * {
      pointer-events: none;
    }
    
    /* Touch-specific animation adjustments */
    @media (hover: none) and (pointer: coarse) {
      .fallback-particle {
        animation-duration: 25s !important;
      }
      
      .fallback-gradient-animation {
        animation-duration: 30s !important;
      }
    }
  `;

  styleSheet.textContent = css;
  document.head.appendChild(styleSheet);

  if (debug) {
    console.log('Applied touch optimizations');
  }
}

/**
 * Apply battery-aware optimizations
 */
async function applyBatteryOptimizations(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  if (!capabilities.batteryAPI) {
    if (debug) {
      console.log('Battery API not available, using conservative settings');
    }
    // Apply conservative settings when battery API is not available
    applyConservativeBatterySettings();
    return;
  }

  try {
    const battery = await (navigator as any).getBattery();
    
    const updateBatteryOptimizations = () => {
      const isCharging = battery.charging;
      const batteryLevel = battery.level;
      const chargingTime = battery.chargingTime;
      const dischargingTime = battery.dischargingTime;
      
      let optimizationLevel = 'normal';
      
      if (!isCharging && batteryLevel < 0.2) {
        optimizationLevel = 'aggressive';
      } else if (!isCharging && batteryLevel < 0.5) {
        optimizationLevel = 'conservative';
      } else if (isCharging && batteryLevel > 0.8) {
        optimizationLevel = 'performance';
      }
      
      applyBatteryLevelOptimizations(optimizationLevel, debug);
      
      // Dispatch event for components to react
      window.dispatchEvent(new CustomEvent('battery-optimization-change', {
        detail: {
          level: optimizationLevel,
          battery: { isCharging, batteryLevel, chargingTime, dischargingTime }
        }
      }));
    };

    // Initial optimization
    updateBatteryOptimizations();

    // Listen for battery changes
    battery.addEventListener('chargingchange', updateBatteryOptimizations);
    battery.addEventListener('levelchange', updateBatteryOptimizations);

    if (debug) {
      console.log('Battery optimizations initialized');
    }

  } catch (error) {
    if (debug) {
      console.warn('Battery API failed:', error);
    }
    applyConservativeBatterySettings();
  }
}

/**
 * Apply battery level specific optimizations
 */
function applyBatteryLevelOptimizations(level: string, debug: boolean): void {
  const styleSheet = document.getElementById('battery-optimizations') as HTMLStyleElement || 
    document.createElement('style');
  styleSheet.id = 'battery-optimizations';
  
  let css = '';
  
  switch (level) {
    case 'aggressive':
      css = `
        /* Aggressive battery saving */
        .fallback-particle,
        .fallback-gradient-animation,
        .vanta-canvas {
          animation-play-state: paused !important;
          will-change: auto !important;
        }
        
        .animation-container {
          filter: none !important;
          backdrop-filter: none !important;
        }
      `;
      break;
      
    case 'conservative':
      css = `
        /* Conservative battery saving */
        .fallback-particle {
          animation-duration: 40s !important;
        }
        
        .fallback-gradient-animation {
          animation-duration: 50s !important;
        }
        
        .vanta-canvas {
          opacity: 0.5 !important;
        }
      `;
      break;
      
    case 'performance':
      css = `
        /* Performance mode while charging */
        .fallback-particle {
          animation-duration: 12s !important;
        }
        
        .fallback-gradient-animation {
          animation-duration: 15s !important;
        }
      `;
      break;
      
    default:
      // Normal mode - remove optimizations
      css = '';
      break;
  }
  
  styleSheet.textContent = css;
  if (!styleSheet.parentNode) {
    document.head.appendChild(styleSheet);
  }

  if (debug) {
    console.log(`Applied battery optimization level: ${level}`);
  }
}

/**
 * Apply conservative battery settings when API is not available
 */
function applyConservativeBatterySettings(): void {
  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-mobile-optimizations', 'battery-conservative');
  
  const css = `
    /* Conservative battery settings */
    @media screen and (max-width: 768px) {
      .fallback-particle {
        animation-duration: 30s !important;
      }
      
      .fallback-gradient-animation {
        animation-duration: 40s !important;
      }
      
      .vanta-canvas {
        opacity: 0.7 !important;
      }
    }
  `;
  
  styleSheet.textContent = css;
  document.head.appendChild(styleSheet);
}

/**
 * Apply thermal throttling protections
 */
async function applyThermalOptimizations(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  // Simple thermal monitoring based on performance degradation
  let performanceBaseline = 0;
  let thermalThrottleDetected = false;
  
  const measurePerformance = () => {
    const start = performance.now();
    
    // Simple computation to measure performance
    let result = 0;
    for (let i = 0; i < 100000; i++) {
      result += Math.sqrt(i);
    }
    
    const duration = performance.now() - start;
    
    if (performanceBaseline === 0) {
      performanceBaseline = duration;
    } else if (duration > performanceBaseline * 2) {
      // Performance degraded significantly - likely thermal throttling
      if (!thermalThrottleDetected) {
        thermalThrottleDetected = true;
        applyThermalThrottleProtection(debug);
      }
    } else if (duration < performanceBaseline * 1.2 && thermalThrottleDetected) {
      // Performance recovered
      thermalThrottleDetected = false;
      removeThermalThrottleProtection(debug);
    }
  };

  // Monitor performance every 30 seconds
  setInterval(measurePerformance, 30000);
  
  // Initial measurement
  measurePerformance();
}

/**
 * Apply thermal throttle protection
 */
function applyThermalThrottleProtection(debug: boolean): void {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'thermal-protection';
  
  const css = `
    /* Thermal throttle protection */
    .fallback-particle,
    .fallback-gradient-animation {
      animation-play-state: paused !important;
    }
    
    .vanta-canvas {
      display: none !important;
    }
    
    .animation-container {
      background: linear-gradient(135deg, #3674B520, #578FCA10) !important;
    }
  `;
  
  styleSheet.textContent = css;
  document.head.appendChild(styleSheet);

  // Dispatch event
  window.dispatchEvent(new CustomEvent('thermal-throttle-detected'));

  if (debug) {
    console.warn('Thermal throttling detected - animations paused');
  }
}

/**
 * Remove thermal throttle protection
 */
function removeThermalThrottleProtection(debug: boolean): void {
  const styleSheet = document.getElementById('thermal-protection');
  if (styleSheet) {
    styleSheet.remove();
  }

  // Dispatch event
  window.dispatchEvent(new CustomEvent('thermal-throttle-recovered'));

  if (debug) {
    console.log('Thermal throttling recovered - animations resumed');
  }
}

/**
 * Apply memory conservation techniques
 */
async function applyMemoryConservation(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  if (capabilities.deviceMemory >= 4) {
    if (debug) {
      console.log('Device has sufficient memory, skipping conservation');
    }
    return;
  }

  // Enable aggressive memory management for low-memory devices
  const conservationLevel = capabilities.deviceMemory <= 2 ? 'aggressive' : 'moderate';
  
  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-mobile-optimizations', 'memory');
  
  let css = `
    /* Memory conservation */
    .fallback-particle {
      contain: strict;
    }
    
    .animation-container {
      contain: layout style paint;
    }
  `;

  if (conservationLevel === 'aggressive') {
    css += `
      /* Aggressive memory conservation */
      .fallback-particle {
        display: none !important;
      }
      
      .vanta-canvas {
        display: none !important;
      }
      
      .animation-container {
        background: linear-gradient(135deg, #3674B530, #578FCA20) !important;
      }
    `;
  }

  styleSheet.textContent = css;
  document.head.appendChild(styleSheet);

  // Set up memory monitoring
  if ('memory' in performance) {
    setInterval(() => {
      const memInfo = (performance as any).memory;
      const usedMB = memInfo.usedJSHeapSize / (1024 * 1024);
      
      if (usedMB > capabilities.deviceMemory * 256 * 0.8) { // 80% of estimated available memory
        window.dispatchEvent(new CustomEvent('memory-pressure', {
          detail: { usedMB, deviceMemory: capabilities.deviceMemory }
        }));
      }
    }, 15000); // Check every 15 seconds
  }

  if (debug) {
    console.log(`Applied ${conservationLevel} memory conservation`);
  }
}

/**
 * Apply network-aware optimizations
 */
async function applyNetworkOptimizations(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  if (capabilities.connectionType === 'unknown') return;

  const isSlowConnection = ['slow-2g', '2g', '3g'].includes(capabilities.connectionType);
  const saveData = capabilities.reducedData;

  if (isSlowConnection || saveData) {
    const styleSheet = document.createElement('style');
    styleSheet.setAttribute('data-mobile-optimizations', 'network');
    
    const css = `
      /* Network optimizations for slow connections */
      .vanta-canvas {
        display: none !important;
      }
      
      .fallback-gradient-animation {
        animation: none !important;
      }
      
      .fallback-particle {
        display: none !important;
      }
      
      .animation-container {
        background: linear-gradient(135deg, #3674B540, #578FCA30) !important;
      }
    `;
    
    styleSheet.textContent = css;
    document.head.appendChild(styleSheet);

    if (debug) {
      console.log('Applied network optimizations for slow connection:', capabilities.connectionType);
    }
  }
}

/**
 * Apply aggressive power saving mode
 */
async function applyAggressivePowerSaving(capabilities: MobileCapabilities, debug: boolean): Promise<void> {
  const styleSheet = document.createElement('style');
  styleSheet.setAttribute('data-mobile-optimizations', 'aggressive-power');
  
  const css = `
    /* Aggressive power saving */
    .fallback-particle,
    .fallback-gradient-animation,
    .vanta-canvas {
      display: none !important;
    }
    
    .animation-container {
      background: linear-gradient(135deg, #3674B520, #578FCA10) !important;
      backdrop-filter: none !important;
      filter: none !important;
      will-change: auto !important;
    }
    
    * {
      animation-play-state: paused !important;
      transition: none !important;
    }
  `;
  
  styleSheet.textContent = css;
  document.head.appendChild(styleSheet);

  if (debug) {
    console.log('Applied aggressive power saving mode');
  }
}

/**
 * Get current mobile capabilities
 */
export function getMobileCapabilities(): MobileCapabilities | null {
  return mobileCapabilities;
}

/**
 * Reset mobile optimizations
 */
export function resetMobileOptimizations(): void {
  mobileCapabilities = null;
  
  // Remove optimization stylesheets
  const optimizationSheets = document.querySelectorAll('style[data-mobile-optimizations]');
  optimizationSheets.forEach(sheet => sheet.remove());
  
  // Remove specific optimization sheets
  const specificSheets = ['battery-optimizations', 'thermal-protection'];
  specificSheets.forEach(id => {
    const sheet = document.getElementById(id);
    if (sheet) sheet.remove();
  });
}

export default {
  detectMobileCapabilities,
  applyMobileOptimizations,
  getMobileCapabilities,
  resetMobileOptimizations,
};