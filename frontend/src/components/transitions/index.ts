/**
 * Loading Transitions Components
 * 
 * Export all transition components and hooks for easy importing
 */

// Fade transitions
export {
  default as FadeInOnScroll,
  FadeInFast,
  FadeInSlow,
  FadeInDelayed,
  FadeInCard,
  FadeInHero,
  FadeInText,
} from './FadeInOnScroll';

// Slide transitions
export {
  default as SlideInOnScroll,
  SlideUpOnScroll,
  SlideDownOnScroll,
  SlideLeftOnScroll,
  SlideRightOnScroll,
  SlideInFast,
  SlideInSlow,
  SlideInSubtle,
  SlideInDramatic,
  SlideInCard,
  SlideInHero,
  SlideInListItem,
  SlideInButton,
  CustomSlideInOnScroll,
} from './SlideInOnScroll';

// Stagger transitions
export {
  default as StaggerContainer,
  StaggerItem,
  StaggerList,
  StaggerGrid,
  StaggerCardGrid,
  StaggerText,
  StaggerFast,
  StaggerSlow,
  StaggerReverse,
  withStagger,
  useStaggerContext,
  useStandaloneStaggerItem,
} from './StaggerContainer';

// Re-export hooks for convenience
export {
  default as useAnimateOnScroll,
  useFadeIn,
  useSlideUp,
  useSlideDown,
  useSlideLeft,
  useSlideRight,
  useScaleIn,
  useBounceIn,
  useCustomScrollAnimation,
} from '@/hooks/useAnimateOnScroll';

export {
  default as useIntersectionObserver,
  useVisibility,
  useInView,
  useStaggeredIntersection,
} from '@/hooks/useIntersectionObserver';

export {
  default as useStaggeredAnimation,
  useStaggeredList,
  useStaggeredGrid,
  useStaggeredText,
  useStaggerItem,
} from '@/hooks/useStaggeredAnimation';

// Types
export type { AnimationType } from '@/hooks/useAnimateOnScroll';
export type { 
  AnimateOnScrollConfig,
  AnimateOnScrollResult,
} from '@/hooks/useAnimateOnScroll';
export type {
  IntersectionConfig,
  IntersectionResult,
} from '@/hooks/useIntersectionObserver';
export type {
  StaggerConfig,
  StaggerResult,
  StaggeredItem,
} from '@/hooks/useStaggeredAnimation';
export type { SlideDirection } from './SlideInOnScroll';