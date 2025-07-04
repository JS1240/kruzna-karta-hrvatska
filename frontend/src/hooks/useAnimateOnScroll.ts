/**
 * useAnimateOnScroll Hook
 * 
 * Scroll-triggered animations with motion preference awareness.
 * Provides smooth entry animations when elements come into view.
 */

import { useCallback, useMemo } from 'react';
import { useIntersectionObserver, IntersectionConfig } from './useIntersectionObserver';
import { useReducedMotion } from './useReducedMotion';

export type AnimationType = 
  | 'fade'
  | 'slideUp'
  | 'slideDown'
  | 'slideLeft'
  | 'slideRight'
  | 'scale'
  | 'scaleUp'
  | 'scaleDown'
  | 'rotateIn'
  | 'bounce'
  | 'elastic';

export interface AnimateOnScrollConfig extends IntersectionConfig {
  animation?: AnimationType;
  duration?: number;
  easing?: string;
  distance?: number;
  scale?: number;
  rotation?: number;
  stagger?: number;
}

export interface AnimateOnScrollResult {
  ref: (node: Element | null) => void;
  isVisible: boolean;
  hasAnimated: boolean;
  style: React.CSSProperties;
  className: string;
}

/**
 * Animation configurations for different types
 */
const ANIMATION_CONFIGS = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    className: 'motion-safe-fade',
  },
  slideUp: {
    initial: { opacity: 0, transform: 'translateY(var(--motion-offset, 40px))' },
    animate: { opacity: 1, transform: 'translateY(0)' },
    className: 'motion-safe-slide',
  },
  slideDown: {
    initial: { opacity: 0, transform: 'translateY(calc(-1 * var(--motion-offset, 40px)))' },
    animate: { opacity: 1, transform: 'translateY(0)' },
    className: 'motion-safe-slide',
  },
  slideLeft: {
    initial: { opacity: 0, transform: 'translateX(var(--motion-offset, 40px))' },
    animate: { opacity: 1, transform: 'translateX(0)' },
    className: 'motion-safe-slide',
  },
  slideRight: {
    initial: { opacity: 0, transform: 'translateX(calc(-1 * var(--motion-offset, 40px)))' },
    animate: { opacity: 1, transform: 'translateX(0)' },
    className: 'motion-safe-slide',
  },
  scale: {
    initial: { opacity: 0, transform: 'scale(0.8)' },
    animate: { opacity: 1, transform: 'scale(1)' },
    className: 'motion-safe-scale',
  },
  scaleUp: {
    initial: { opacity: 0, transform: 'scale(0.9)' },
    animate: { opacity: 1, transform: 'scale(1)' },
    className: 'motion-safe-scale',
  },
  scaleDown: {
    initial: { opacity: 0, transform: 'scale(1.1)' },
    animate: { opacity: 1, transform: 'scale(1)' },
    className: 'motion-safe-scale',
  },
  rotateIn: {
    initial: { opacity: 0, transform: 'rotate(-10deg) scale(0.9)' },
    animate: { opacity: 1, transform: 'rotate(0deg) scale(1)' },
    className: 'motion-safe-scale',
  },
  bounce: {
    initial: { opacity: 0, transform: 'translateY(var(--motion-offset, 40px))' },
    animate: { opacity: 1, transform: 'translateY(0)' },
    className: 'motion-enhanced-bounce',
  },
  elastic: {
    initial: { opacity: 0, transform: 'scale(0.8)' },
    animate: { opacity: 1, transform: 'scale(1)' },
    className: 'motion-enhanced-pulse',
  },
} as const;

/**
 * React hook that animates an element when it scrolls into view, with support for configurable animation types and user motion preferences.
 *
 * Applies the specified animation when the target element enters the viewport, using intersection observer logic and respecting reduced motion settings. Returns a ref callback for the element, visibility state, animation completion state, computed inline styles, and a CSS class name.
 *
 * @param config - Optional configuration for animation type, duration, easing, distance, scale, rotation, stagger delay, and intersection observer options
 * @returns An object containing the ref callback, visibility booleans, computed style, and class name for the animated element
 */
export function useAnimateOnScroll(
  config: AnimateOnScrollConfig = {}
): AnimateOnScrollResult {
  const {
    animation = 'fade',
    duration = 0.6,
    easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
    distance = 40,
    scale = 0.8,
    rotation = 0,
    stagger = 0,
    ...intersectionConfig
  } = config;

  const {
    prefersReducedMotion,
    getClassName,
    shouldDisableAnimation,
    transitionMultiplier,
  } = useReducedMotion();

  const { isIntersecting, hasIntersected, ref } = useIntersectionObserver({
    triggerOnce: true,
    threshold: 0.1,
    rootMargin: '50px',
    ...intersectionConfig,
  });

  // Get animation configuration
  const animationConfig = ANIMATION_CONFIGS[animation];

  // Calculate effective duration with motion preferences
  const effectiveDuration = duration * transitionMultiplier;

  // Create style object
  const style = useMemo((): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      '--motion-offset': `${distance}px`,
      transition: shouldDisableAnimation 
        ? 'none' 
        : `all ${effectiveDuration}s ${easing}${stagger ? ` ${stagger}s` : ''}`,
    };

    if (shouldDisableAnimation) {
      // For reduced motion, show final state immediately
      return {
        ...baseStyles,
        ...animationConfig.animate,
      };
    }

    // For normal motion, apply initial or animate state based on visibility
    if (hasIntersected || isIntersecting) {
      return {
        ...baseStyles,
        ...animationConfig.animate,
      };
    } else {
      return {
        ...baseStyles,
        ...animationConfig.initial,
      };
    }
  }, [
    distance,
    shouldDisableAnimation,
    effectiveDuration,
    easing,
    stagger,
    animationConfig,
    hasIntersected,
    isIntersecting,
  ]);

  // Create class name
  const className = getClassName(
    'animate-on-scroll',
    // Motion classes
    animationConfig.className,
    // Reduced motion classes
    'opacity-100'
  );

  return {
    ref,
    isVisible: isIntersecting,
    hasAnimated: hasIntersected,
    style,
    className,
  };
}

/**
 * React hook for applying a fade-in animation to an element when it scrolls into view.
 *
 * @returns An object containing a ref callback, visibility state, computed style, and className for the animated element.
 */
export function useFadeIn(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'fade', ...config });
}

/**
 * React hook that animates an element with a slide-up effect when it enters the viewport.
 *
 * Uses the `useAnimateOnScroll` hook with the `'slideUp'` animation preset. Additional configuration options can be provided to customize the animation.
 *
 * @returns An object containing a ref callback, visibility booleans, computed style, and className for the animated element.
 */
export function useSlideUp(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideUp', ...config });
}

/**
 * React hook that animates an element with a slide-down effect when it enters the viewport.
 *
 * @param config - Optional configuration to customize the animation and intersection observer behavior
 * @returns An object containing a ref callback, visibility state, computed styles, and class name for the animated element
 */
export function useSlideDown(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideDown', ...config });
}

/**
 * React hook that animates an element with a slide-in-from-left effect when it enters the viewport.
 *
 * @param config - Optional configuration to customize the animation and intersection observer behavior
 * @returns An object containing a ref callback, visibility state, computed style, and class name for the animated element
 */
export function useSlideLeft(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideLeft', ...config });
}

/**
 * React hook that animates an element with a slide-in-from-right effect when it enters the viewport.
 *
 * @returns An object containing a ref callback, visibility state, computed styles, and class name for the animated element.
 */
export function useSlideRight(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideRight', ...config });
}

/**
 * React hook that animates an element with a scale-in effect when it enters the viewport.
 *
 * Uses scroll-triggered animation with support for user motion preferences. Additional animation and intersection observer options can be provided via the config object.
 *
 * @returns An object containing a ref callback, visibility booleans, computed style, and className for the animated element.
 */
export function useScaleIn(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'scale', ...config });
}

/**
 * React hook that animates an element with a bounce-in effect when it enters the viewport.
 *
 * Accepts configuration options to customize the animation behavior.
 *
 * @returns An object containing a ref callback, visibility booleans, computed style, and className for the animated element.
 */
export function useBounceIn(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'bounce', ...config });
}

/**
 * Provides scroll-triggered animation with custom CSS transforms, respecting user motion preferences.
 *
 * Applies the specified initial and animate transform styles to an element as it enters the viewport, with configurable transition properties. Animations are disabled if the user prefers reduced motion.
 *
 * @param initialTransform - The CSS transform to apply before the element is visible
 * @param animateTransform - The CSS transform to apply when the element becomes visible (defaults to 'none')
 * @returns An object containing a ref callback, visibility booleans, computed style, and a motion-related class name
 */
export function useCustomScrollAnimation(
  initialTransform: string,
  animateTransform: string = 'none',
  config: AnimateOnScrollConfig = {}
): AnimateOnScrollResult {
  const {
    duration = 0.6,
    easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
    stagger = 0,
    ...intersectionConfig
  } = config;

  const {
    prefersReducedMotion,
    shouldDisableAnimation,
    transitionMultiplier,
  } = useReducedMotion();

  const { isIntersecting, hasIntersected, ref } = useIntersectionObserver({
    triggerOnce: true,
    threshold: 0.1,
    ...intersectionConfig,
  });

  const effectiveDuration = duration * transitionMultiplier;

  const style = useMemo((): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      transition: shouldDisableAnimation 
        ? 'none' 
        : `all ${effectiveDuration}s ${easing}${stagger ? ` ${stagger}s` : ''}`,
    };

    if (shouldDisableAnimation) {
      return {
        ...baseStyles,
        opacity: 1,
        transform: animateTransform,
      };
    }

    if (hasIntersected || isIntersecting) {
      return {
        ...baseStyles,
        opacity: 1,
        transform: animateTransform,
      };
    } else {
      return {
        ...baseStyles,
        opacity: 0,
        transform: initialTransform,
      };
    }
  }, [
    shouldDisableAnimation,
    effectiveDuration,
    easing,
    stagger,
    hasIntersected,
    isIntersecting,
    initialTransform,
    animateTransform,
  ]);

  return {
    ref,
    isVisible: isIntersecting,
    hasAnimated: hasIntersected,
    style,
    className: prefersReducedMotion ? 'motion-reduce' : 'motion-safe',
  };
}

export default useAnimateOnScroll;