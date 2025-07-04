/**
 * Motion Utilities
 * 
 * Utility functions for handling motion preferences, animations,
 * and accessibility compliance across the application.
 */

import type { MotionPreference, MotionCapabilities } from '@/hooks/useReducedMotion';

// Animation configuration types
export interface AnimationConfig {
  duration: number;
  easing: string;
  delay: number;
  fillMode: 'none' | 'forwards' | 'backwards' | 'both';
  iterationCount: number | 'infinite';
  direction: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
}

export interface TransitionConfig {
  property: string;
  duration: number;
  timingFunction: string;
  delay: number;
}

// Safe animation defaults for reduced motion
export const REDUCED_MOTION_CONFIG = {
  animation: {
    duration: 0.2, // Very short duration
    easing: 'ease-out',
    delay: 0,
    fillMode: 'both' as const,
    iterationCount: 1,
    direction: 'normal' as const,
  },
  transition: {
    property: 'opacity, transform',
    duration: 0.15,
    timingFunction: 'ease-out',
    delay: 0,
  },
} as const;

// Standard animation defaults for normal motion
export const NORMAL_MOTION_CONFIG = {
  animation: {
    duration: 0.6,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    delay: 0,
    fillMode: 'both' as const,
    iterationCount: 1,
    direction: 'normal' as const,
  },
  transition: {
    property: 'all',
    duration: 0.3,
    timingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
    delay: 0,
  },
} as const;

// Enhanced motion defaults for users who prefer motion
export const ENHANCED_MOTION_CONFIG = {
  animation: {
    duration: 0.8,
    easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
    delay: 0,
    fillMode: 'both' as const,
    iterationCount: 1,
    direction: 'normal' as const,
  },
  transition: {
    property: 'all',
    duration: 0.4,
    timingFunction: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
    delay: 0,
  },
} as const;

/**
 * Get motion-safe animation configuration
 */
export function getMotionSafeConfig(
  motionPreference: MotionPreference,
  baseConfig?: Partial<AnimationConfig>
): AnimationConfig {
  const defaultConfig = motionPreference === 'reduce' 
    ? REDUCED_MOTION_CONFIG.animation 
    : NORMAL_MOTION_CONFIG.animation;
    
  return { ...defaultConfig, ...baseConfig };
}

/**
 * Get motion-safe transition configuration
 */
export function getMotionSafeTransition(
  motionPreference: MotionPreference,
  baseConfig?: Partial<TransitionConfig>
): TransitionConfig {
  const defaultConfig = motionPreference === 'reduce'
    ? REDUCED_MOTION_CONFIG.transition
    : NORMAL_MOTION_CONFIG.transition;
    
  return { ...defaultConfig, ...baseConfig };
}

/**
 * Generate CSS animation string with motion preference support
 */
export function createAnimationCSS(
  name: string,
  config: Partial<AnimationConfig>,
  motionPreference: MotionPreference = 'no-preference'
): string {
  const safeConfig = getMotionSafeConfig(motionPreference, config);
  
  // Disable animation completely for reduced motion if requested
  if (motionPreference === 'reduce' && config.duration === 0) {
    return 'none';
  }
  
  const parts = [
    name,
    `${safeConfig.duration}s`,
    safeConfig.easing,
    `${safeConfig.delay}s`,
    safeConfig.iterationCount,
    safeConfig.direction,
    safeConfig.fillMode,
  ];
  
  return parts.join(' ');
}

/**
 * Generate CSS transition string with motion preference support
 */
export function createTransitionCSS(
  config: Partial<TransitionConfig>,
  motionPreference: MotionPreference = 'no-preference'
): string {
  const safeConfig = getMotionSafeTransition(motionPreference, config);
  
  // Disable transitions for reduced motion if duration is 0
  if (motionPreference === 'reduce' && config.duration === 0) {
    return 'none';
  }
  
  return `${safeConfig.property} ${safeConfig.duration}s ${safeConfig.timingFunction} ${safeConfig.delay}s`;
}

/**
 * Conditional animation class names with motion preference support
 */
export function getMotionClasses(
  baseClasses: string,
  animationClasses: string,
  motionPreference: MotionPreference = 'no-preference',
  fallbackClasses?: string
): string {
  const classes = [baseClasses];
  
  if (motionPreference === 'reduce') {
    // Use fallback classes or remove animation classes
    if (fallbackClasses) {
      classes.push(fallbackClasses);
    }
    // Remove any animation-related classes
    const safeClasses = classes.join(' ')
      .replace(/animate-\w+/g, '')
      .replace(/transition-\w+/g, '')
      .replace(/duration-\w+/g, '')
      .replace(/ease-\w+/g, '');
    return safeClasses.replace(/\s+/g, ' ').trim();
  } else {
    classes.push(animationClasses);
  }
  
  return classes.join(' ');
}

/**
 * Create media query for reduced motion
 */
export function createReducedMotionMediaQuery(): string {
  return '@media (prefers-reduced-motion: reduce)';
}

/**
 * Create media query for motion preference
 */
export function createMotionMediaQuery(): string {
  return '@media (prefers-reduced-motion: no-preference)';
}

/**
 * Generate complete CSS with motion preference support
 */
export function generateMotionAwareCSS(
  selector: string,
  normalStyles: Record<string, string>,
  reducedMotionStyles: Record<string, string>
): string {
  const normalCSS = Object.entries(normalStyles)
    .map(([property, value]) => `  ${property}: ${value};`)
    .join('\n');
    
  const reducedCSS = Object.entries(reducedMotionStyles)
    .map(([property, value]) => `  ${property}: ${value};`)
    .join('\n');
  
  return `
${selector} {
${normalCSS}
}

${createReducedMotionMediaQuery()} {
  ${selector} {
${reducedCSS}
  }
}`.trim();
}

/**
 * Validate motion preference value
 */
export function isValidMotionPreference(value: unknown): value is MotionPreference {
  return typeof value === 'string' && ['no-preference', 'reduce'].includes(value);
}

/**
 * Get motion preference from media query
 */
export function detectMotionPreference(): MotionPreference {
  if (typeof window === 'undefined') {
    return 'no-preference';
  }
  
  try {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    return mediaQuery.matches ? 'reduce' : 'no-preference';
  } catch (error) {
    console.warn('Error detecting motion preference:', error);
    return 'no-preference';
  }
}

/**
 * Create animation frame with motion preference support
 */
export function createMotionAwareRAF(
  callback: FrameRequestCallback,
  motionCapabilities: MotionCapabilities
): number | null {
  if (!motionCapabilities.canAnimate) {
    // Execute immediately without animation frame for reduced motion
    setTimeout(() => callback(performance.now()), 0);
    return null;
  }
  
  return requestAnimationFrame(callback);
}

/**
 * Cancel motion-aware animation frame
 */
export function cancelMotionAwareRAF(
  handle: number | null,
  motionCapabilities: MotionCapabilities
): void {
  if (handle !== null && motionCapabilities.canAnimate) {
    cancelAnimationFrame(handle);
  }
}

/**
 * Throttle function with motion preference support
 */
export function createMotionAwareThrottle<T extends (...args: any[]) => any>(
  func: T,
  delay: number,
  motionCapabilities: MotionCapabilities
): T {
  // Reduce throttle delay for reduced motion to make interactions feel more immediate
  const effectiveDelay = motionCapabilities.shouldReduceDuration ? delay * 0.5 : delay;
  
  let timeoutId: NodeJS.Timeout | null = null;
  let lastExecTime = 0;
  
  return ((...args: Parameters<T>) => {
    const now = Date.now();
    
    if (now - lastExecTime > effectiveDelay) {
      func(...args);
      lastExecTime = now;
    } else {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      
      timeoutId = setTimeout(() => {
        func(...args);
        lastExecTime = Date.now();
        timeoutId = null;
      }, effectiveDelay - (now - lastExecTime));
    }
  }) as T;
}

/**
 * Debounce function with motion preference support
 */
export function createMotionAwareDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number,
  motionCapabilities: MotionCapabilities
): T {
  // Reduce debounce delay for reduced motion
  const effectiveDelay = motionCapabilities.shouldReduceDuration ? delay * 0.3 : delay;
  
  let timeoutId: NodeJS.Timeout | null = null;
  
  return ((...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    timeoutId = setTimeout(() => {
      func(...args);
      timeoutId = null;
    }, effectiveDelay);
  }) as T;
}

/**
 * Spring animation configuration with motion preference support
 */
export interface SpringConfig {
  tension: number;
  friction: number;
  mass: number;
  precision: number;
}

export function getMotionAwareSpringConfig(
  motionCapabilities: MotionCapabilities,
  baseConfig?: Partial<SpringConfig>
): SpringConfig {
  const defaultConfig = {
    tension: 120,
    friction: 14,
    mass: 1,
    precision: 0.01,
  };
  
  if (motionCapabilities.shouldReduceDuration) {
    // Make spring animations much snappier for reduced motion
    return {
      tension: 300,
      friction: 30,
      mass: 0.5,
      precision: 0.1,
      ...baseConfig,
    };
  }
  
  return { ...defaultConfig, ...baseConfig };
}

/**
 * Intersection Observer with motion preference support
 */
export function createMotionAwareIntersectionObserver(
  callback: IntersectionObserverCallback,
  motionCapabilities: MotionCapabilities,
  options?: IntersectionObserverInit
): IntersectionObserver {
  const wrappedCallback: IntersectionObserverCallback = (entries, observer) => {
    if (motionCapabilities.shouldDisableAnimation) {
      // For reduced motion, trigger immediately without waiting for intersection
      entries.forEach(entry => {
        // Mark as intersecting to trigger animations immediately
        const modifiedEntry = {
          ...entry,
          isIntersecting: true,
          intersectionRatio: 1,
        };
        callback([modifiedEntry], observer);
      });
    } else {
      callback(entries, observer);
    }
  };
  
  const defaultOptions: IntersectionObserverInit = {
    rootMargin: '10px',
    threshold: motionCapabilities.shouldDisableAnimation ? 0 : 0.1,
    ...options,
  };
  
  return new IntersectionObserver(wrappedCallback, defaultOptions);
}

/**
 * Scroll event handler with motion preference support
 */
export function createMotionAwareScrollHandler(
  handler: (event: Event) => void,
  motionCapabilities: MotionCapabilities,
  throttleDelay: number = 16
): (event: Event) => void {
  if (motionCapabilities.shouldDisableAnimation) {
    // For reduced motion, execute immediately without throttling
    return handler;
  }
  
  return createMotionAwareThrottle(handler, throttleDelay, motionCapabilities);
}

/**
 * Performance-aware animation frame loop
 */
export function createMotionAwareAnimationLoop(
  callback: (timestamp: number, deltaTime: number) => void,
  motionCapabilities: MotionCapabilities
): () => void {
  let lastTimestamp = 0;
  let animationId: number | null = null;
  let isRunning = false;
  
  const loop = (timestamp: number) => {
    if (!isRunning) return;
    
    const deltaTime = timestamp - lastTimestamp;
    lastTimestamp = timestamp;
    
    callback(timestamp, deltaTime);
    
    if (isRunning) {
      animationId = createMotionAwareRAF(loop, motionCapabilities);
    }
  };
  
  return () => {
    if (isRunning) {
      isRunning = false;
      if (animationId !== null) {
        cancelMotionAwareRAF(animationId, motionCapabilities);
      }
    } else {
      isRunning = true;
      lastTimestamp = performance.now();
      animationId = createMotionAwareRAF(loop, motionCapabilities);
    }
  };
}

export default {
  getMotionSafeConfig,
  getMotionSafeTransition,
  createAnimationCSS,
  createTransitionCSS,
  getMotionClasses,
  generateMotionAwareCSS,
  detectMotionPreference,
  createMotionAwareRAF,
  createMotionAwareThrottle,
  createMotionAwareDebounce,
  getMotionAwareSpringConfig,
  createMotionAwareIntersectionObserver,
  createMotionAwareScrollHandler,
  createMotionAwareAnimationLoop,
};