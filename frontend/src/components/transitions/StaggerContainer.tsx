/**
 * StaggerContainer Component
 * 
 * Container for staggered child animations. Orchestrates coordinated
 * entry animations with motion preference awareness.
 */

import React, { forwardRef, useMemo } from 'react';
import { useStaggeredAnimation, useStaggerItem } from '@/hooks/useStaggeredAnimation';
import type { StaggerConfig } from '@/hooks/useStaggeredAnimation';
import type { AnimationType } from '@/hooks/useAnimateOnScroll';

export interface StaggerContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  staggerDelay?: number;
  maxItems?: number;
  animation?: AnimationType;
  duration?: number;
  easing?: string;
  direction?: 'normal' | 'reverse' | 'alternate';
  threshold?: number;
  rootMargin?: string;
  triggerOnce?: boolean;
  resetOnExit?: boolean;
  disabled?: boolean;
  as?: keyof JSX.IntrinsicElements;
  staggerConfig?: Partial<StaggerConfig>;
}

/**
 * StaggerContainer component
 */
export const StaggerContainer = forwardRef<HTMLDivElement, StaggerContainerProps>(
  (
    {
      children,
      staggerDelay = 100,
      maxItems = 20,
      animation = 'slideUp',
      duration = 0.6,
      easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
      direction = 'normal',
      threshold = 0.1,
      rootMargin = '100px',
      triggerOnce = true,
      resetOnExit = false,
      disabled = false,
      as = 'div',
      staggerConfig = {},
      className = '',
      style = {},
      ...props
    },
    forwardedRef
  ) => {
    const staggerController = useStaggeredAnimation({
      staggerDelay,
      maxItems,
      animation,
      duration,
      easing,
      direction,
      threshold,
      rootMargin,
      triggerOnce,
      resetOnExit,
      disabled,
      ...staggerConfig,
    });

    // Combine refs
    const setRef = (node: HTMLElement | null) => {
      staggerController.containerRef(node);
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
        className={`stagger-container ${className}`.trim()}
        style={style}
        data-stagger-animation={animation}
        data-stagger-direction={direction}
        {...props}
      >
        <StaggerContext.Provider value={staggerController}>
          {children}
        </StaggerContext.Provider>
      </Component>
    );
  }
);

StaggerContainer.displayName = 'StaggerContainer';

/**
 * Context for stagger controller
 */
const StaggerContext = React.createContext<ReturnType<typeof useStaggeredAnimation> | null>(null);

/**
 * Hook to access stagger controller from context
 */
export function useStaggerContext() {
  const context = React.useContext(StaggerContext);
  if (!context) {
    throw new Error('useStaggerContext must be used within a StaggerContainer');
  }
  return context;
}

/**
 * StaggerItem component for individual items
 */
export interface StaggerItemProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  id?: string | number;
  as?: keyof JSX.IntrinsicElements;
  index?: number;
}

export const StaggerItem = forwardRef<HTMLElement, StaggerItemProps>(
  (
    {
      children,
      id,
      as = 'div',
      index,
      className = '',
      style = {},
      ...props
    },
    forwardedRef
  ) => {
    const staggerController = useStaggerContext();
    
    // Generate ID if not provided
    const itemId = useMemo(() => {
      return id ?? `stagger-item-${index ?? Math.random().toString(36).substr(2, 9)}`;
    }, [id, index]);

    const { style: itemStyle, className: itemClassName, isReady } = useStaggerItem(itemId, staggerController);

    const Component = as as React.ElementType;

    return (
      <Component
        ref={forwardedRef}
        className={`${itemClassName} ${className}`.trim()}
        style={{ ...itemStyle, ...style }}
        data-stagger-item-id={itemId}
        data-stagger-ready={isReady}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

StaggerItem.displayName = 'StaggerItem';

/**
 * Preset stagger containers
 */

// List stagger container
export const StaggerList: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="slideUp"
    staggerDelay={80}
    direction="normal"
    as="div"
    {...props}
  />
);

// Grid stagger container
export const StaggerGrid: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="scale"
    staggerDelay={50}
    direction="alternate"
    as="div"
    {...props}
  />
);

// Card grid stagger
export const StaggerCardGrid: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="slideUp"
    staggerDelay={60}
    duration={0.5}
    easing="cubic-bezier(0.25, 0.46, 0.45, 0.94)"
    threshold={0.2}
    rootMargin="50px"
    as="div"
    {...props}
  />
);

// Text stagger for headings and paragraphs
export const StaggerText: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="slideUp"
    staggerDelay={30}
    duration={0.4}
    maxItems={10}
    as="div"
    {...props}
  />
);

// Fast stagger for UI elements
export const StaggerFast: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="fade"
    staggerDelay={40}
    duration={0.3}
    as="div"
    {...props}
  />
);

// Slow dramatic stagger
export const StaggerSlow: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="slideUp"
    staggerDelay={150}
    duration={0.8}
    easing="cubic-bezier(0.16, 1, 0.3, 1)"
    as="div"
    {...props}
  />
);

// Reverse stagger (last item first)
export const StaggerReverse: React.FC<StaggerContainerProps> = (props) => (
  <StaggerContainer
    animation="slideUp"
    direction="reverse"
    staggerDelay={80}
    as="div"
    {...props}
  />
);

/**
 * Higher-order component for automatic staggering
 */
export function withStagger<P extends object>(
  Component: React.ComponentType<P>,
  staggerProps: Partial<StaggerContainerProps> = {}
) {
  const WrappedComponent = forwardRef<any, P & { staggerContainer?: boolean }>((props, ref) => {
    const { staggerContainer = true, ...componentProps } = props;

    if (!staggerContainer) {
      return <Component ref={ref} {...(componentProps as P)} />;
    }

    return (
      <StaggerContainer {...staggerProps}>
        <StaggerItem>
          <Component ref={ref} {...(componentProps as P)} />
        </StaggerItem>
      </StaggerContainer>
    );
  });

  WrappedComponent.displayName = `withStagger(${Component.displayName || Component.name})`;
  return WrappedComponent;
}

/**
 * Hook for using stagger items without context
 */
export function useStandaloneStaggerItem(
  id: string | number,
  containerConfig: Partial<StaggerConfig> = {}
) {
  const staggerController = useStaggeredAnimation(containerConfig);
  const itemResult = useStaggerItem(id, staggerController);

  return {
    containerRef: staggerController.containerRef,
    ...itemResult,
    isContainerVisible: staggerController.isVisible,
  };
}

export default StaggerContainer;