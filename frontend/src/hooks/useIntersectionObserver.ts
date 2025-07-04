/**
 * useIntersectionObserver Hook
 * 
 * Motion-aware viewport detection hook that respects user's motion preferences
 * and provides optimized intersection observation for loading transitions.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useReducedMotion } from './useReducedMotion';
import { createMotionAwareIntersectionObserver } from '@/utils/motionUtils';

export interface IntersectionConfig {
  threshold?: number | number[];
  rootMargin?: string;
  triggerOnce?: boolean;
  delay?: number;
  disabled?: boolean;
}

export interface IntersectionResult {
  isIntersecting: boolean;
  hasIntersected: boolean;
  entry: IntersectionObserverEntry | null;
  ref: (node: Element | null) => void;
}

/**
 * React hook that observes an element's intersection with the viewport, respecting user motion preferences and supporting delayed or one-time triggers.
 *
 * Provides intersection state, the latest observer entry, and a ref callback for the target element. If reduced motion is preferred, triggers intersection immediately when the element is visible. Supports configurable threshold, root margin, delay, trigger-once behavior, and disabling.
 *
 * @returns An object containing `isIntersecting`, `hasIntersected`, the latest `IntersectionObserverEntry`, and a `ref` callback to assign to the observed element.
 */
export function useIntersectionObserver(
  config: IntersectionConfig = {}
): IntersectionResult {
  const {
    threshold = 0.1,
    rootMargin = '50px',
    triggerOnce = true,
    delay = 0,
    disabled = false,
  } = config;

  const { shouldDisableAnimation, motionCapabilities } = useReducedMotion();
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const elementRef = useRef<Element | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleIntersection = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      setEntry(entry);

      if (entry.isIntersecting) {
        if (delay > 0 && !shouldDisableAnimation) {
          // Apply delay only if motion is not reduced
          timeoutRef.current = setTimeout(() => {
            setIsIntersecting(true);
            if (triggerOnce) {
              setHasIntersected(true);
            }
          }, delay);
        } else {
          // Immediate trigger for reduced motion or no delay
          setIsIntersecting(true);
          if (triggerOnce) {
            setHasIntersected(true);
          }
        }
      } else {
        // Clear any pending timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }

        if (!triggerOnce) {
          setIsIntersecting(false);
        }
      }
    },
    [delay, triggerOnce, shouldDisableAnimation]
  );

  const setRef = useCallback(
    (node: Element | null) => {
      // Clean up previous observer
      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      // Clear any pending timeouts
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      if (disabled || (triggerOnce && hasIntersected)) {
        elementRef.current = node;
        return;
      }

      if (node) {
        elementRef.current = node;

        // For reduced motion, trigger immediately if element is visible
        if (shouldDisableAnimation) {
          const rect = node.getBoundingClientRect();
          const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
          
          if (isVisible) {
            setIsIntersecting(true);
            if (triggerOnce) {
              setHasIntersected(true);
            }
            return;
          }
        }

        // Create motion-aware intersection observer
        observerRef.current = createMotionAwareIntersectionObserver(
          handleIntersection,
          motionCapabilities,
          {
            threshold,
            rootMargin,
          }
        );

        observerRef.current.observe(node);
      } else {
        elementRef.current = null;
      }
    },
    [
      disabled,
      triggerOnce,
      hasIntersected,
      shouldDisableAnimation,
      handleIntersection,
      motionCapabilities,
      threshold,
      rootMargin,
    ]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    isIntersecting,
    hasIntersected,
    entry,
    ref: setRef,
  };
}

/**
 * Returns a boolean indicating if the element is currently visible in the viewport, along with a ref callback to assign the observed element.
 *
 * @returns A tuple containing the intersection state and a ref setter for the target element
 */
export function useVisibility(
  options: IntersectionConfig = {}
): [boolean, (node: Element | null) => void] {
  const { isIntersecting, ref } = useIntersectionObserver(options);
  return [isIntersecting, ref];
}

/**
 * React hook that returns whether an element has ever intersected the viewport, triggering only once.
 *
 * @returns A tuple containing a boolean indicating if the element has intersected at least once, and a ref callback to assign to the target element.
 */
export function useInView(
  options: IntersectionConfig = {}
): [boolean, (node: Element | null) => void] {
  const { hasIntersected, ref } = useIntersectionObserver({
    triggerOnce: true,
    ...options,
  });
  return [hasIntersected, ref];
}

/**
 * Returns an intersection observer result with a delay staggered by the element's index.
 *
 * The intersection trigger is delayed by `baseDelay * index` milliseconds, enabling staggered animations or loading effects for lists of elements.
 *
 * @param index - The zero-based index used to calculate the staggered delay
 * @param baseDelay - The base delay in milliseconds for each index step (default: 100)
 * @param options - Additional intersection observer configuration
 * @returns The intersection observer result with staggered delay applied
 */
export function useStaggeredIntersection(
  index: number,
  baseDelay: number = 100,
  options: IntersectionConfig = {}
): IntersectionResult {
  const staggeredDelay = baseDelay * index;
  
  return useIntersectionObserver({
    delay: staggeredDelay,
    ...options,
  });
}

export default useIntersectionObserver;