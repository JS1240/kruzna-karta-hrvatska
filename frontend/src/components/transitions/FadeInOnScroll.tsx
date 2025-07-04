/**
 * FadeInOnScroll Component
 * 
 * Wraps content with fade-in animation when it enters the viewport.
 * Respects user motion preferences and provides smooth loading transitions.
 */

import React, { forwardRef } from 'react';
import { useFadeIn } from '@/hooks/useAnimateOnScroll';
import type { AnimateOnScrollConfig } from '@/hooks/useAnimateOnScroll';

export interface FadeInOnScrollProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  threshold?: number;
  rootMargin?: string;
  triggerOnce?: boolean;
  disabled?: boolean;
  easing?: string;
  as?: keyof JSX.IntrinsicElements;
  animationConfig?: Partial<AnimateOnScrollConfig>;
}

/**
 * FadeInOnScroll component with motion preference awareness
 */
export const FadeInOnScroll = forwardRef<HTMLDivElement, FadeInOnScrollProps>(
  (
    {
      children,
      delay = 0,
      duration = 0.6,
      threshold = 0.1,
      rootMargin = '50px',
      triggerOnce = true,
      disabled = false,
      easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
      as = 'div',
      animationConfig = {},
      className = '',
      style = {},
      ...props
    },
    forwardedRef
  ) => {
    const { ref, style: animationStyle, className: animationClassName } = useFadeIn({
      delay,
      duration,
      threshold,
      rootMargin,
      triggerOnce,
      disabled,
      easing,
      ...animationConfig,
    });

    // Combine refs
    const setRef = (node: HTMLElement | null) => {
      ref(node);
      if (forwardedRef) {
        if (typeof forwardedRef === 'function') {
          forwardedRef(node);
        } else {
          forwardedRef.current = node;
        }
      }
    };

    const Component = as as React.ElementType;

    return (
      <Component
        ref={setRef}
        className={`${animationClassName} ${className}`.trim()}
        style={{ ...animationStyle, ...style }}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

FadeInOnScroll.displayName = 'FadeInOnScroll';

/**
 * Preset fade-in variants
 */

// Fast fade-in for quick content
export const FadeInFast: React.FC<Omit<FadeInOnScrollProps, 'duration'>> = (props) => (
  <FadeInOnScroll duration={0.3} {...props} />
);

// Slow fade-in for dramatic effect
export const FadeInSlow: React.FC<Omit<FadeInOnScrollProps, 'duration'>> = (props) => (
  <FadeInOnScroll duration={1.2} {...props} />
);

// Delayed fade-in for staggered effects
export const FadeInDelayed: React.FC<Omit<FadeInOnScrollProps, 'delay'>> = (props) => (
  <FadeInOnScroll delay={200} {...props} />
);

// Fade-in for cards with optimized settings
export const FadeInCard: React.FC<FadeInOnScrollProps> = (props) => (
  <FadeInOnScroll
    duration={0.5}
    threshold={0.2}
    rootMargin="30px"
    easing="cubic-bezier(0.25, 0.46, 0.45, 0.94)"
    {...props}
  />
);

// Fade-in for hero sections
export const FadeInHero: React.FC<FadeInOnScrollProps> = (props) => (
  <FadeInOnScroll
    duration={0.8}
    threshold={0.3}
    rootMargin="100px"
    easing="cubic-bezier(0.16, 1, 0.3, 1)"
    {...props}
  />
);

// Fade-in for text content
export const FadeInText: React.FC<FadeInOnScrollProps> = (props) => (
  <FadeInOnScroll
    duration={0.6}
    threshold={0.1}
    rootMargin="40px"
    as="div"
    {...props}
  />
);

export default FadeInOnScroll;