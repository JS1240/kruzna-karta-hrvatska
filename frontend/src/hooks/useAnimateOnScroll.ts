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
 * Main scroll animation hook
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
 * Preset hooks for common animations
 */
export function useFadeIn(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'fade', ...config });
}

export function useSlideUp(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideUp', ...config });
}

export function useSlideDown(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideDown', ...config });
}

export function useSlideLeft(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideLeft', ...config });
}

export function useSlideRight(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'slideRight', ...config });
}

export function useScaleIn(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'scale', ...config });
}

export function useBounceIn(config: AnimateOnScrollConfig = {}) {
  return useAnimateOnScroll({ animation: 'bounce', ...config });
}

/**
 * Scroll animation with custom transform
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