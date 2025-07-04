/**
 * SlideInOnScroll Component
 * 
 * Wraps content with slide-in animation when it enters the viewport.
 * Supports multiple directions and respects user motion preferences.
 */

import React, { forwardRef } from 'react';
import { 
  useSlideUp, 
  useSlideDown, 
  useSlideLeft, 
  useSlideRight,
  useAnimateOnScroll 
} from '@/hooks/useAnimateOnScroll';
import type { AnimateOnScrollConfig } from '@/hooks/useAnimateOnScroll';

export type SlideDirection = 'up' | 'down' | 'left' | 'right';

export interface SlideInOnScrollProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  direction?: SlideDirection;
  distance?: number;
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
 * SlideInOnScroll component with directional animation
 */
export const SlideInOnScroll = forwardRef<HTMLDivElement, SlideInOnScrollProps>(
  (
    {
      children,
      direction = 'up',
      distance = 40,
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
    // Select the appropriate hook based on direction
    const getSlideHook = () => {
      const config = {
        delay,
        duration,
        threshold,
        rootMargin,
        triggerOnce,
        disabled,
        easing,
        distance,
        ...animationConfig,
      };

      switch (direction) {
        case 'down':
          return useSlideDown(config);
        case 'left':
          return useSlideLeft(config);
        case 'right':
          return useSlideRight(config);
        case 'up':
        default:
          return useSlideUp(config);
      }
    };

    const { ref, style: animationStyle, className: animationClassName } = getSlideHook();

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

SlideInOnScroll.displayName = 'SlideInOnScroll';

/**
 * Directional slide components
 */

export const SlideUpOnScroll: React.FC<Omit<SlideInOnScrollProps, 'direction'>> = (props) => (
  <SlideInOnScroll direction="up" {...props} />
);

export const SlideDownOnScroll: React.FC<Omit<SlideInOnScrollProps, 'direction'>> = (props) => (
  <SlideInOnScroll direction="down" {...props} />
);

export const SlideLeftOnScroll: React.FC<Omit<SlideInOnScrollProps, 'direction'>> = (props) => (
  <SlideInOnScroll direction="left" {...props} />
);

export const SlideRightOnScroll: React.FC<Omit<SlideInOnScrollProps, 'direction'>> = (props) => (
  <SlideInOnScroll direction="right" {...props} />
);

/**
 * Preset slide variants
 */

// Fast slide for quick content reveals
export const SlideInFast: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll duration={0.4} distance={20} {...props} />
);

// Slow slide for dramatic effects
export const SlideInSlow: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll duration={1.0} distance={60} {...props} />
);

// Subtle slide with minimal movement
export const SlideInSubtle: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll duration={0.5} distance={16} {...props} />
);

// Dramatic slide with large movement
export const SlideInDramatic: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll duration={0.8} distance={80} {...props} />
);

// Card-optimized slide animation
export const SlideInCard: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll
    duration={0.5}
    distance={30}
    threshold={0.2}
    rootMargin="30px"
    easing="cubic-bezier(0.25, 0.46, 0.45, 0.94)"
    {...props}
  />
);

// Hero section slide animation
export const SlideInHero: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll
    duration={0.8}
    distance={50}
    threshold={0.3}
    rootMargin="100px"
    easing="cubic-bezier(0.16, 1, 0.3, 1)"
    {...props}
  />
);

// List item slide animation
export const SlideInListItem: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll
    duration={0.4}
    distance={25}
    threshold={0.1}
    rootMargin="20px"
    direction="up"
    {...props}
  />
);

// Button slide animation
export const SlideInButton: React.FC<SlideInOnScrollProps> = (props) => (
  <SlideInOnScroll
    duration={0.3}
    distance={15}
    threshold={0.5}
    easing="cubic-bezier(0.34, 1.56, 0.64, 1)"
    {...props}
  />
);

/**
 * Custom slide animation with specific transform
 */
export interface CustomSlideProps extends Omit<SlideInOnScrollProps, 'direction' | 'distance'> {
  transform: string;
}

export const CustomSlideInOnScroll: React.FC<CustomSlideProps> = ({
  transform,
  duration = 0.6,
  easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
  threshold = 0.1,
  rootMargin = '50px',
  triggerOnce = true,
  disabled = false,
  delay = 0,
  animationConfig = {},
  children,
  className = '',
  style = {},
  as = 'div',
  ...props
}) => {
  const { ref, style: animationStyle, className: animationClassName } = useAnimateOnScroll({
    animation: 'slideUp', // Base animation, will be overridden by custom transform
    duration,
    easing,
    threshold,
    rootMargin,
    triggerOnce,
    disabled,
    delay,
    ...animationConfig,
  });

  // Override with custom transform
  const customStyle = {
    ...animationStyle,
    transform: animationStyle.transform?.toString().includes('translateY(0)') ? 'none' : transform,
  };

  const Component = as as React.ElementType;

  return (
    <Component
      ref={ref}
      className={`${animationClassName} ${className}`.trim()}
      style={{ ...customStyle, ...style }}
      {...props}
    >
      {children}
    </Component>
  );
};

export default SlideInOnScroll;