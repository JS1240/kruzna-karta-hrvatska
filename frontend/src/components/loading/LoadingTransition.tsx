/**
 * LoadingTransition Component
 * 
 * Smooth transition from skeleton/loading state to actual content.
 * Handles the complete loading → content reveal lifecycle.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { FadeInOnScroll } from '@/components/transitions';

export interface LoadingTransitionProps {
  isLoading: boolean;
  skeleton: React.ReactNode;
  children: React.ReactNode;
  duration?: number;
  delay?: number;
  fadeOutDuration?: number;
  crossfade?: boolean;
  disabled?: boolean;
  onTransitionStart?: () => void;
  onTransitionComplete?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * LoadingTransition component
 */
export const LoadingTransition: React.FC<LoadingTransitionProps> = ({
  isLoading,
  skeleton,
  children,
  duration = 0.6,
  delay = 100,
  fadeOutDuration = 0.3,
  crossfade = true,
  disabled = false,
  onTransitionStart,
  onTransitionComplete,
  className = '',
  style = {},
}) => {
  const [showSkeleton, setShowSkeleton] = useState(isLoading);
  const [showContent, setShowContent] = useState(!isLoading);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const transitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    prefersReducedMotion,
    shouldDisableAnimation,
    transitionMultiplier,
    getClassName,
  } = useReducedMotion();

  // Handle loading state changes
  useEffect(() => {
    if (disabled) {
      setShowSkeleton(isLoading);
      setShowContent(!isLoading);
      return;
    }

    if (isLoading) {
      // Show skeleton immediately when loading starts
      setShowContent(false);
      setShowSkeleton(true);
      setIsTransitioning(false);
    } else {
      // Start transition from skeleton to content
      if (showSkeleton) {
        setIsTransitioning(true);
        onTransitionStart?.();

        const effectiveDelay = shouldDisableAnimation ? 0 : delay;
        const effectiveFadeOutDuration = fadeOutDuration * transitionMultiplier;

        timeoutRef.current = setTimeout(() => {
          if (crossfade) {
            // Show content while skeleton is still visible
            setShowContent(true);
            
            // Hide skeleton after content appears
            transitionTimeoutRef.current = setTimeout(() => {
              setShowSkeleton(false);
              setIsTransitioning(false);
              onTransitionComplete?.();
            }, effectiveFadeOutDuration * 1000);
          } else {
            // Hide skeleton first, then show content
            setShowSkeleton(false);
            
            setTimeout(() => {
              setShowContent(true);
              setIsTransitioning(false);
              onTransitionComplete?.();
            }, 50); // Small delay to avoid flash
          }
        }, effectiveDelay);
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, [
    isLoading,
    showSkeleton,
    delay,
    fadeOutDuration,
    crossfade,
    disabled,
    shouldDisableAnimation,
    transitionMultiplier,
    onTransitionStart,
    onTransitionComplete,
  ]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, []);

  const containerClassName = getClassName(
    'loading-transition relative',
    // Motion classes
    'transition-opacity',
    // Reduced motion classes
    ''
  );

  const skeletonStyle: React.CSSProperties = shouldDisableAnimation
    ? { opacity: showSkeleton ? 1 : 0 }
    : {
        opacity: showSkeleton ? 1 : 0,
        transition: `opacity ${fadeOutDuration * transitionMultiplier}s ease-out`,
        pointerEvents: showSkeleton ? 'auto' : 'none',
      };

  const contentStyle: React.CSSProperties = shouldDisableAnimation
    ? { opacity: showContent ? 1 : 0 }
    : {
        opacity: showContent ? 1 : 0,
        transition: `opacity ${duration * transitionMultiplier}s ease-out`,
      };

  return (
    <div
      className={`${containerClassName} ${className}`.trim()}
      style={style}
      data-loading={isLoading}
      data-transitioning={isTransitioning}
      data-motion-preference={prefersReducedMotion ? 'reduce' : 'no-preference'}
    >
      {/* Skeleton Layer */}
      {showSkeleton && (
        <div
          className="loading-skeleton absolute inset-0"
          style={skeletonStyle}
          aria-hidden={!isLoading}
        >
          {skeleton}
        </div>
      )}

      {/* Content Layer */}
      {showContent && (
        <div
          className="loading-content"
          style={crossfade ? contentStyle : undefined}
        >
          {shouldDisableAnimation ? (
            children
          ) : (
            <FadeInOnScroll
              duration={duration}
              disabled={disabled || isLoading}
              triggerOnce={false}
            >
              {children}
            </FadeInOnScroll>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Preset loading transitions
 */

// Fast loading transition
export const FastLoadingTransition: React.FC<LoadingTransitionProps> = (props) => (
  <LoadingTransition
    duration={0.3}
    delay={50}
    fadeOutDuration={0.2}
    {...props}
  />
);

// Slow loading transition
export const SlowLoadingTransition: React.FC<LoadingTransitionProps> = (props) => (
  <LoadingTransition
    duration={0.8}
    delay={200}
    fadeOutDuration={0.4}
    {...props}
  />
);

// Crossfade loading transition
export const CrossfadeLoadingTransition: React.FC<LoadingTransitionProps> = (props) => (
  <LoadingTransition
    crossfade={true}
    duration={0.6}
    fadeOutDuration={0.4}
    {...props}
  />
);

// Sequential loading transition (no crossfade)
export const SequentialLoadingTransition: React.FC<LoadingTransitionProps> = (props) => (
  <LoadingTransition
    crossfade={false}
    duration={0.5}
    delay={100}
    {...props}
  />
);

// Card loading transition
export const CardLoadingTransition: React.FC<LoadingTransitionProps> = (props) => (
  <LoadingTransition
    duration={0.5}
    delay={150}
    fadeOutDuration={0.3}
    crossfade={true}
    {...props}
  />
);

/**
 * Manages state for transitioning from a loading skeleton to content, providing flags for transition progress and completion.
 *
 * @param isLoading - Whether the loading state is active
 * @param options - Optional configuration for transition delay and callbacks
 * @returns An object with `isTransitioning`, `hasLoaded`, `shouldShowContent`, and `shouldShowSkeleton` flags
 */
export function useLoadingTransition(
  isLoading: boolean,
  options: {
    delay?: number;
    onStart?: () => void;
    onComplete?: () => void;
  } = {}
) {
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(!isLoading);

  useEffect(() => {
    if (!isLoading && !hasLoaded) {
      setIsTransitioning(true);
      options.onStart?.();

      const timeout = setTimeout(() => {
        setHasLoaded(true);
        setIsTransitioning(false);
        options.onComplete?.();
      }, options.delay || 100);

      return () => clearTimeout(timeout);
    } else if (isLoading) {
      setHasLoaded(false);
      setIsTransitioning(false);
    }
  }, [isLoading, hasLoaded, options]);

  return {
    isTransitioning,
    hasLoaded,
    shouldShowContent: !isLoading || isTransitioning,
    shouldShowSkeleton: isLoading,
  };
}

export default LoadingTransition;