/**
 * Mobile Components
 * 
 * Export all touch-optimized mobile components for easy importing
 */

// Mobile Navigation
export {
  default as MobileNavigation,
  MobileBottomNav,
} from './MobileNavigation';

// Touch Carousel
export {
  default as TouchCarousel,
  TouchCardCarousel,
  TouchImageGallery,
} from './TouchCarousel';

// Touch Controls
export {
  SwipeActions,
  TouchButton,
  TouchCounter,
  PullToRefresh,
  LongPressMenu,
} from './TouchControls';

// Touch Forms
export {
  TouchDatePicker,
  TouchTimePicker,
  TouchSearch,
} from './TouchForms';

// Re-export hooks for convenience
export {
  default as useTouch,
  useSwipe,
  useLongPress,
  useTouchButton,
  usePullToRefresh,
} from '@/hooks/useTouch';

// Re-export utilities
export {
  detectTouchDevice,
  getTouchTargetGuidelines,
  getTouchOptimizedClasses,
  triggerHapticFeedback,
  smoothScrollTo,
  addTouchAccessibility,
} from '@/utils/touchUtils';

// Types
export type { 
  TouchPoint,
  TouchGestureConfig,
  SwipeGesture,
  PinchGesture,
  TouchState,
} from '@/hooks/useTouch';

export type {
  TouchDevice,
  TouchTarget,
  TouchZone,
} from '@/utils/touchUtils';

export type {
  NavigationItem,
  MobileNavigationProps,
  MobileBottomNavProps,
} from './MobileNavigation';

export type {
  TouchCarouselProps,
  TouchCardCarouselProps,
  TouchImageGalleryProps,
} from './TouchCarousel';

export type {
  SwipeAction,
  SwipeActionsProps,
  TouchButtonProps,
  TouchCounterProps,
  PullToRefreshProps,
  LongPressMenuProps,
} from './TouchControls';

export type {
  TouchDatePickerProps,
  TouchTimePickerProps,
  TouchSearchProps,
} from './TouchForms';