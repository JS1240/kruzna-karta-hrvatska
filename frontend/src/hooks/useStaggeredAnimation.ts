/**
 * useStaggeredAnimation Hook
 * 
 * Coordinated staggered entry animations for lists and grids.
 * Provides orchestrated animations with motion preference awareness.
 */

import { useCallback, useRef, useState, useEffect } from 'react';
import { useReducedMotion } from './useReducedMotion';
import { useIntersectionObserver, IntersectionConfig } from './useIntersectionObserver';
import type { AnimationType } from './useAnimateOnScroll';

export interface StaggerConfig extends IntersectionConfig {
  staggerDelay?: number;
  maxItems?: number;
  animation?: AnimationType;
  duration?: number;
  easing?: string;
  direction?: 'normal' | 'reverse' | 'alternate';
  resetOnExit?: boolean;
}

export interface StaggeredItem {
  id: string | number;
  delay: number;
  index: number;
  isReady: boolean;
}

export interface StaggerResult {
  containerRef: (node: Element | null) => void;
  isVisible: boolean;
  register: (id: string | number) => StaggeredItem;
  getItemStyle: (item: StaggeredItem) => React.CSSProperties;
  getItemClassName: (item: StaggeredItem) => string;
  reset: () => void;
  items: StaggeredItem[];
}

/**
 * Provides a controller for orchestrating staggered entry animations for a group of items within a container, with support for motion preferences and viewport visibility.
 *
 * Registers items, calculates their animation delays based on configuration, and manages their readiness state for animation. Triggers staggered animations when the container enters the viewport, or immediately if reduced motion is preferred. Exposes utility functions for retrieving item styles and class names reflecting their animation state.
 *
 * @param config - Optional configuration for stagger timing, animation type, direction, duration, easing, maximum items, and intersection observer options.
 * @returns An object containing a container ref, visibility state, item registration function, style and class name getters, reset function, and the current list of registered items.
 */
export function useStaggeredAnimation(
  config: StaggerConfig = {}
): StaggerResult {
  const {
    staggerDelay = 100,
    maxItems = 20,
    animation = 'slideUp',
    duration = 0.6,
    easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
    direction = 'normal',
    resetOnExit = false,
    ...intersectionConfig
  } = config;

  const {
    prefersReducedMotion,
    shouldDisableAnimation,
    transitionMultiplier,
    getClassName,
  } = useReducedMotion();

  const [items, setItems] = useState<Map<string | number, StaggeredItem>>(new Map());
  const [isTriggered, setIsTriggered] = useState(false);
  const timeoutsRef = useRef<Set<NodeJS.Timeout>>(new Set());

  const { isIntersecting, hasIntersected, ref: containerRef } = useIntersectionObserver({
    threshold: 0.1,
    rootMargin: '100px',
    triggerOnce: !resetOnExit,
    ...intersectionConfig,
  });

  // Reset function
  const reset = useCallback(() => {
    // Clear all timeouts
    timeoutsRef.current.forEach(timeout => clearTimeout(timeout));
    timeoutsRef.current.clear();
    
    // Reset all items
    setItems(prev => {
      const newItems = new Map(prev);
      newItems.forEach(item => {
        item.isReady = false;
      });
      return newItems;
    });
    
    setIsTriggered(false);
  }, []);

  // Register item function
  const register = useCallback((id: string | number): StaggeredItem => {
    const currentItems = Array.from(items.values());
    const index = currentItems.length;
    
    // Calculate delay based on direction and index
    let effectiveIndex = index;
    if (direction === 'reverse') {
      effectiveIndex = Math.max(0, maxItems - index - 1);
    } else if (direction === 'alternate') {
      effectiveIndex = index % 2 === 0 ? index / 2 : maxItems - Math.floor(index / 2) - 1;
    }

    const delay = Math.min(effectiveIndex * staggerDelay, maxItems * staggerDelay);

    const item: StaggeredItem = {
      id,
      delay,
      index,
      isReady: shouldDisableAnimation || isTriggered,
    };

    setItems(prev => {
      const newItems = new Map(prev);
      newItems.set(id, item);
      return newItems;
    });

    return item;
  }, [items, direction, maxItems, staggerDelay, shouldDisableAnimation, isTriggered]);

  // Trigger animations when container becomes visible
  useEffect(() => {
    if ((isIntersecting || hasIntersected) && !isTriggered) {
      setIsTriggered(true);

      if (shouldDisableAnimation) {
        // For reduced motion, show all items immediately
        setItems(prev => {
          const newItems = new Map(prev);
          newItems.forEach(item => {
            item.isReady = true;
          });
          return newItems;
        });
      } else {
        // For normal motion, stagger the animations
        items.forEach((item) => {
          const timeout = setTimeout(() => {
            setItems(prev => {
              const newItems = new Map(prev);
              const existingItem = newItems.get(item.id);
              if (existingItem) {
                existingItem.isReady = true;
              }
              return newItems;
            });
          }, item.delay);

          timeoutsRef.current.add(timeout);
        });
      }
    } else if (!isIntersecting && resetOnExit && isTriggered) {
      reset();
    }
  }, [isIntersecting, hasIntersected, isTriggered, shouldDisableAnimation, items, resetOnExit, reset]);

  // Get item style
  const getItemStyle = useCallback((item: StaggeredItem): React.CSSProperties => {
    const effectiveDuration = duration * transitionMultiplier;

    const baseStyle: React.CSSProperties = {
      transition: shouldDisableAnimation 
        ? 'none' 
        : `all ${effectiveDuration}s ${easing}`,
    };

    if (shouldDisableAnimation) {
      return {
        ...baseStyle,
        opacity: 1,
        transform: 'none',
      };
    }

    // Animation styles based on type
    const getAnimationStyles = () => {
      switch (animation) {
        case 'fade':
          return item.isReady 
            ? { opacity: 1 }
            : { opacity: 0 };
        
        case 'slideUp':
          return item.isReady
            ? { opacity: 1, transform: 'translateY(0)' }
            : { opacity: 0, transform: 'translateY(40px)' };
        
        case 'slideDown':
          return item.isReady
            ? { opacity: 1, transform: 'translateY(0)' }
            : { opacity: 0, transform: 'translateY(-40px)' };
        
        case 'slideLeft':
          return item.isReady
            ? { opacity: 1, transform: 'translateX(0)' }
            : { opacity: 0, transform: 'translateX(40px)' };
        
        case 'slideRight':
          return item.isReady
            ? { opacity: 1, transform: 'translateX(0)' }
            : { opacity: 0, transform: 'translateX(-40px)' };
        
        case 'scale':
          return item.isReady
            ? { opacity: 1, transform: 'scale(1)' }
            : { opacity: 0, transform: 'scale(0.8)' };
        
        default:
          return item.isReady 
            ? { opacity: 1 }
            : { opacity: 0 };
      }
    };

    return {
      ...baseStyle,
      ...getAnimationStyles(),
    };
  }, [animation, duration, easing, shouldDisableAnimation, transitionMultiplier]);

  // Get item class name
  const getItemClassName = useCallback((item: StaggeredItem): string => {
    const animationClass = animation === 'fade' ? 'motion-safe-fade' : 'motion-safe-slide';
    
    return getClassName(
      'stagger-item',
      // Motion classes
      `${animationClass} ${item.isReady ? 'animate-in' : 'animate-out'}`,
      // Reduced motion classes
      'opacity-100'
    );
  }, [animation, getClassName]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      timeoutsRef.current.forEach(timeout => clearTimeout(timeout));
      timeoutsRef.current.clear();
    };
  }, []);

  return {
    containerRef,
    isVisible: isIntersecting,
    register,
    getItemStyle,
    getItemClassName,
    reset,
    items: Array.from(items.values()),
  };
}

/**
 * Provides a staggered animation controller for list items with a default slide-up animation and configurable delay.
 *
 * @param staggerDelay - The delay in milliseconds between each item's animation start
 * @param config - Optional configuration to override default animation settings
 * @returns A stagger controller for managing staggered list animations
 */
export function useStaggeredList(
  staggerDelay: number = 100,
  config: Partial<StaggerConfig> = {}
) {
  return useStaggeredAnimation({
    staggerDelay,
    animation: 'slideUp',
    ...config,
  });
}

/**
 * Returns a staggered animation controller configured for grid layouts.
 *
 * Applies a 'scale' animation with alternate direction and customizable number of columns and stagger delay.
 *
 * @param columns - Number of columns in the grid
 * @param staggerDelay - Delay in milliseconds between each item's animation
 * @param config - Additional configuration options for the staggered animation
 * @returns A stagger controller for managing grid item animations
 */
export function useStaggeredGrid(
  columns: number = 3,
  staggerDelay: number = 50,
  config: Partial<StaggerConfig> = {}
) {
  return useStaggeredAnimation({
    staggerDelay,
    animation: 'scale',
    direction: 'alternate',
    ...config,
  });
}

/**
 * Provides a staggered slide-up animation controller optimized for animating text elements such as headings.
 *
 * @param staggerDelay - The delay in milliseconds between each item's animation start
 * @param config - Optional configuration to override default animation settings
 * @returns A stagger controller for managing staggered text animations
 */
export function useStaggeredText(
  staggerDelay: number = 30,
  config: Partial<StaggerConfig> = {}
) {
  return useStaggeredAnimation({
    staggerDelay,
    animation: 'slideUp',
    duration: 0.4,
    ...config,
  });
}

/**
 * Registers an item with a staggered animation controller and returns its animation style, class name, and readiness state.
 *
 * @param id - Unique identifier for the item within the stagger group
 * @param staggerController - The stagger animation controller managing the group
 * @returns An object containing the item's animation style, class name, and readiness state
 */
export function useStaggerItem(
  id: string | number,
  staggerController: StaggerResult
): {
  style: React.CSSProperties;
  className: string;
  isReady: boolean;
} {
  const item = staggerController.register(id);
  
  return {
    style: staggerController.getItemStyle(item),
    className: staggerController.getItemClassName(item),
    isReady: item.isReady,
  };
}

export default useStaggeredAnimation;