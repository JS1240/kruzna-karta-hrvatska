/**
 * useReducedMotion Hook
 * 
 * Comprehensive hook for detecting and respecting user's motion preferences
 * with support for manual overrides and performance optimization.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';

// Motion preference types
export type MotionPreference = 'no-preference' | 'reduce';
export type MotionOverride = 'respect-system' | 'force-enable' | 'force-disable';

// Configuration options
export interface MotionConfig {
  respectSystemPreference: boolean;
  enableAnimations: boolean;
  enableTransitions: boolean;
  enableParallax: boolean;
  enableAutoplay: boolean;
  animationDuration: 'normal' | 'reduced' | 'disabled';
  override?: MotionOverride;
}

// Motion capabilities based on user preferences
export interface MotionCapabilities {
  canAnimate: boolean;
  canTransition: boolean;
  canParallax: boolean;
  canAutoplay: boolean;
  shouldReduceDuration: boolean;
  shouldDisableAnimation: boolean;
  animationMultiplier: number; // For duration scaling
  transitionMultiplier: number;
}

/**
 * React hook for detecting and managing user motion preferences, combining system settings, manual overrides, and configurable animation behaviors.
 *
 * Returns motion state, effective preference, motion capability flags, utility functions for animation/transition/className handling, and CSS custom properties for styling integration.
 *
 * @param config - Optional partial configuration to control motion features and behavior
 * @returns An object containing motion state, capabilities, utility functions, and CSS custom properties
 */
export function useReducedMotion(config?: Partial<MotionConfig>) {
  const [systemPreference, setSystemPreference] = useState<MotionPreference>('no-preference');
  const [userOverride, setUserOverride] = useState<MotionOverride>('respect-system');
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Default configuration
  const defaultConfig: MotionConfig = {
    respectSystemPreference: true,
    enableAnimations: true,
    enableTransitions: true,
    enableParallax: true,
    enableAutoplay: true,
    animationDuration: 'normal',
    ...config,
  };
  
  // Detect system motion preference
  const detectSystemPreference = useCallback((): MotionPreference => {
    if (typeof window === 'undefined') return 'no-preference';
    
    try {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      return mediaQuery.matches ? 'reduce' : 'no-preference';
    } catch (error) {
      console.warn('Error detecting motion preference:', error);
      return 'no-preference';
    }
  }, []);
  
  // Initialize and listen for changes
  useEffect(() => {
    const updatePreference = () => {
      setSystemPreference(detectSystemPreference());
      setIsInitialized(true);
    };
    
    // Initial detection
    updatePreference();
    
    // Listen for changes
    let mediaQuery: MediaQueryList | null = null;
    
    try {
      mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      
      // Modern browsers
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', updatePreference);
      } 
      // Legacy browsers
      else if (mediaQuery.addListener) {
        mediaQuery.addListener(updatePreference);
      }
    } catch (error) {
      console.warn('Error setting up motion preference listener:', error);
    }
    
    return () => {
      if (mediaQuery) {
        try {
          if (mediaQuery.removeEventListener) {
            mediaQuery.removeEventListener('change', updatePreference);
          } else if (mediaQuery.removeListener) {
            mediaQuery.removeListener(updatePreference);
          }
        } catch (error) {
          console.warn('Error removing motion preference listener:', error);
        }
      }
    };
  }, [detectSystemPreference]);
  
  // Load user override from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('motion-preference-override');
      if (stored && ['respect-system', 'force-enable', 'force-disable'].includes(stored)) {
        setUserOverride(stored as MotionOverride);
      }
    } catch (error) {
      console.warn('Error loading motion preference override:', error);
    }
  }, []);
  
  // Calculate effective motion preference
  const effectivePreference = useMemo((): MotionPreference => {
    if (!defaultConfig.respectSystemPreference) {
      return 'no-preference';
    }
    
    switch (userOverride) {
      case 'force-disable':
        return 'reduce';
      case 'force-enable':
        return 'no-preference';
      case 'respect-system':
      default:
        return systemPreference;
    }
  }, [systemPreference, userOverride, defaultConfig.respectSystemPreference]);
  
  // Calculate motion capabilities
  const motionCapabilities = useMemo((): MotionCapabilities => {
    const shouldReduce = effectivePreference === 'reduce';
    
    return {
      canAnimate: defaultConfig.enableAnimations && !shouldReduce,
      canTransition: defaultConfig.enableTransitions && (!shouldReduce || defaultConfig.animationDuration !== 'disabled'),
      canParallax: defaultConfig.enableParallax && !shouldReduce,
      canAutoplay: defaultConfig.enableAutoplay && !shouldReduce,
      shouldReduceDuration: shouldReduce && defaultConfig.animationDuration === 'reduced',
      shouldDisableAnimation: shouldReduce,
      animationMultiplier: shouldReduce ? 
        (defaultConfig.animationDuration === 'disabled' ? 0 : 0.3) : 1,
      transitionMultiplier: shouldReduce ? 0.5 : 1,
    };
  }, [effectivePreference, defaultConfig]);
  
  // Set user override preference
  const setMotionOverride = useCallback((override: MotionOverride) => {
    setUserOverride(override);
    
    try {
      localStorage.setItem('motion-preference-override', override);
    } catch (error) {
      console.warn('Error saving motion preference override:', error);
    }
  }, []);
  
  // Helper functions for common use cases
  const getAnimationProps = useCallback((duration?: number | string) => {
    if (!motionCapabilities.canAnimate) {
      return {
        animate: false,
        transition: { duration: 0 },
        style: { animation: 'none' },
      };
    }
    
    if (motionCapabilities.shouldReduceDuration && typeof duration === 'number') {
      return {
        animate: true,
        transition: { duration: duration * motionCapabilities.animationMultiplier },
      };
    }
    
    return {
      animate: true,
      transition: duration ? { duration } : undefined,
    };
  }, [motionCapabilities]);
  
  const getTransitionProps = useCallback((duration?: number | string) => {
    if (!motionCapabilities.canTransition) {
      return {
        style: { transition: 'none' },
      };
    }
    
    if (motionCapabilities.shouldReduceDuration && typeof duration === 'number') {
      return {
        style: { 
          transitionDuration: `${duration * motionCapabilities.transitionMultiplier}s` 
        },
      };
    }
    
    return duration ? { style: { transitionDuration: `${duration}s` } } : {};
  }, [motionCapabilities]);
  
  const getClassName = useCallback((baseClasses: string, motionClasses?: string, reduceClasses?: string) => {
    const classes = [baseClasses];
    
    if (motionCapabilities.canAnimate && motionClasses) {
      classes.push(motionClasses);
    } else if (motionCapabilities.shouldDisableAnimation && reduceClasses) {
      classes.push(reduceClasses);
    }
    
    return classes.filter(Boolean).join(' ');
  }, [motionCapabilities]);
  
  // CSS custom properties for use in stylesheets
  const cssCustomProperties = useMemo(() => ({
    '--motion-duration-multiplier': motionCapabilities.animationMultiplier.toString(),
    '--motion-transition-multiplier': motionCapabilities.transitionMultiplier.toString(),
    '--motion-can-animate': motionCapabilities.canAnimate ? '1' : '0',
    '--motion-should-reduce': motionCapabilities.shouldDisableAnimation ? '1' : '0',
  }), [motionCapabilities]);
  
  // Performance tracking
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      // Track motion preference usage for analytics
      const trackingData = {
        systemPreference,
        userOverride,
        effectivePreference,
        timestamp: new Date().toISOString(),
      };
      
      // Dispatch custom event for performance monitoring
      window.dispatchEvent(new CustomEvent('motion-preference-change', {
        detail: trackingData,
      }));
    }
  }, [isInitialized, systemPreference, userOverride, effectivePreference]);
  
  return {
    // Core state
    systemPreference,
    userOverride,
    effectivePreference,
    isInitialized,
    
    // Configuration
    config: defaultConfig,
    
    // Capabilities
    ...motionCapabilities,
    
    // Utility functions
    setMotionOverride,
    getAnimationProps,
    getTransitionProps,
    getClassName,
    
    // CSS integration
    cssCustomProperties,
    
    // Legacy compatibility (for existing code)
    prefersReducedMotion: effectivePreference === 'reduce',
    shouldAnimate: motionCapabilities.canAnimate,
    shouldTransition: motionCapabilities.canTransition,
  };
}

// Context for app-wide motion preference management
import { createContext, useContext } from 'react';

export interface MotionContextValue {
  motionState: ReturnType<typeof useReducedMotion>;
  updateConfig: (config: Partial<MotionConfig>) => void;
}

export const MotionContext = createContext<MotionContextValue | null>(null);

/**
 * Provides motion preference state and utilities to the React component tree via context.
 *
 * Applies CSS custom properties for motion settings to the document root and supplies motion state and a configuration update function to descendants.
 *
 * @param children - React nodes to render within the provider
 * @param config - Optional partial configuration for motion behavior
 */
export function MotionProvider({ 
  children, 
  config 
}: { 
  children: React.ReactNode;
  config?: Partial<MotionConfig>;
}) {
  const motionState = useReducedMotion(config);
  
  const updateConfig = useCallback((newConfig: Partial<MotionConfig>) => {
    // This would typically update a state that gets passed to useReducedMotion
    // For now, we'll just log the update
    console.log('Motion config update requested:', newConfig);
  }, []);
  
  // Apply CSS custom properties to document
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      Object.entries(motionState.cssCustomProperties).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });
    }
  }, [motionState.cssCustomProperties]);
  
  const contextValue: MotionContextValue = {
    motionState,
    updateConfig,
  };
  
  return (
    <MotionContext.Provider value={contextValue}>
      {children}
    </MotionContext.Provider>
  );
}

/**
 * Returns the current motion context value.
 *
 * Throws an error if called outside of a `MotionProvider`.
 * @returns The motion context value containing motion state and configuration update function.
 */
export function useMotionContext() {
  const context = useContext(MotionContext);
  if (!context) {
    throw new Error('useMotionContext must be used within a MotionProvider');
  }
  return context;
}

/**
 * Returns animation properties adjusted for the current motion preferences.
 *
 * @param duration - Optional animation duration to be adjusted based on motion settings
 * @returns Animation properties with duration and enabled state adapted to user and system motion preferences
 */
export function useAnimationProps(duration?: number | string) {
  const { getAnimationProps } = useReducedMotion();
  return getAnimationProps(duration);
}

/**
 * Returns transition style properties based on the current motion preferences.
 *
 * If transitions are disabled or reduced, the returned properties will reflect those settings, including adjusting or removing transition durations as appropriate.
 *
 * @param duration - Optional transition duration to use if transitions are allowed
 * @returns An object containing transition-related style properties
 */
export function useTransitionProps(duration?: number | string) {
  const { getTransitionProps } = useReducedMotion();
  return getTransitionProps(duration);
}

/**
 * Returns a class name string that adapts to the user's motion preference.
 *
 * Combines the provided base classes with additional classes for normal or reduced motion, depending on the current motion capabilities.
 *
 * @param baseClasses - The base class names to always include
 * @param motionClasses - Class names to include when motion is allowed
 * @param reduceClasses - Class names to include when reduced motion is preferred
 * @returns The combined class name string reflecting the current motion preference
 */
export function useMotionClassName(
  baseClasses: string, 
  motionClasses?: string, 
  reduceClasses?: string
) {
  const { getClassName } = useReducedMotion();
  return getClassName(baseClasses, motionClasses, reduceClasses);
}

/**
 * Returns a boolean indicating whether the user prefers reduced motion.
 *
 * This is a simplified hook for legacy or basic usage scenarios.
 *
 * @returns `true` if reduced motion is preferred, otherwise `false`
 */
export function useSimpleReducedMotion(): boolean {
  const { prefersReducedMotion } = useReducedMotion();
  return prefersReducedMotion;
}

export default useReducedMotion;