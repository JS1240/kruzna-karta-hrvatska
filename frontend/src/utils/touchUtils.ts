/**
 * Touch Utilities
 * 
 * Utility functions for touch interactions, mobile detection,
 * and touch-optimized UI calculations.
 */

export interface TouchDevice {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  hasTouch: boolean;
  orientation: 'portrait' | 'landscape';
  screenSize: 'small' | 'medium' | 'large' | 'xlarge';
  pixelRatio: number;
}

export interface TouchTarget {
  minSize: number;
  recommendedSize: number;
  spacing: number;
}

/**
 * Detect touch device capabilities
 */
export function detectTouchDevice(): TouchDevice {
  const width = window.innerWidth;
  const height = window.innerHeight;
  const userAgent = navigator.userAgent.toLowerCase();
  
  // Touch detection
  const hasTouch = 'ontouchstart' in window || 
                   navigator.maxTouchPoints > 0 || 
                   (navigator as any).msMaxTouchPoints > 0;

  // Device type detection
  const isMobile = width <= 768 || /android|iphone|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
  const isTablet = !isMobile && (width <= 1024 || /ipad|tablet/i.test(userAgent));
  const isDesktop = !isMobile && !isTablet;

  // Orientation
  const orientation = height > width ? 'portrait' : 'landscape';

  // Screen size categories
  let screenSize: TouchDevice['screenSize'];
  if (width <= 480) screenSize = 'small';
  else if (width <= 768) screenSize = 'medium';
  else if (width <= 1024) screenSize = 'large';
  else screenSize = 'xlarge';

  return {
    isMobile,
    isTablet,
    isDesktop,
    hasTouch,
    orientation,
    screenSize,
    pixelRatio: window.devicePixelRatio || 1,
  };
}

/**
 * Get touch target guidelines based on device
 */
export function getTouchTargetGuidelines(device: TouchDevice): TouchTarget {
  if (device.isMobile) {
    return {
      minSize: 44, // iOS/Android minimum
      recommendedSize: 48,
      spacing: 8,
    };
  } else if (device.isTablet) {
    return {
      minSize: 44,
      recommendedSize: 52,
      spacing: 12,
    };
  } else {
    return {
      minSize: 32,
      recommendedSize: 40,
      spacing: 8,
    };
  }
}

/**
 * Calculate touch-safe spacing
 */
export function calculateTouchSpacing(
  elementCount: number,
  containerWidth: number,
  targetSize: number,
  minSpacing: number = 8
): { elementWidth: number; spacing: number } {
  const totalSpacing = (elementCount - 1) * minSpacing;
  const availableWidth = containerWidth - totalSpacing;
  const elementWidth = Math.max(targetSize, availableWidth / elementCount);
  
  const actualSpacing = elementCount > 1 
    ? (containerWidth - elementWidth * elementCount) / (elementCount - 1)
    : 0;

  return {
    elementWidth: Math.floor(elementWidth),
    spacing: Math.floor(Math.max(minSpacing, actualSpacing)),
  };
}

/**
 * Generate touch-optimized CSS classes
 */
export function getTouchOptimizedClasses(device: TouchDevice): {
  touchTarget: string;
  spacing: string;
  interactive: string;
} {
  const guidelines = getTouchTargetGuidelines(device);
  
  return {
    touchTarget: `min-h-[${guidelines.recommendedSize}px] min-w-[${guidelines.recommendedSize}px]`,
    spacing: `gap-${guidelines.spacing / 4}`, // Tailwind spacing units
    interactive: 'active:scale-95 transition-transform duration-100 cursor-pointer select-none',
  };
}

/**
 * Touch gesture direction utilities
 */
export const GESTURE_DIRECTIONS = {
  horizontal: ['left', 'right'],
  vertical: ['up', 'down'],
  all: ['left', 'right', 'up', 'down'],
} as const;

export function isHorizontalGesture(direction: string): boolean {
  return GESTURE_DIRECTIONS.horizontal.includes(direction as any);
}

export function isVerticalGesture(direction: string): boolean {
  return GESTURE_DIRECTIONS.vertical.includes(direction as any);
}

/**
 * Touch velocity calculations
 */
export function calculateVelocity(
  startPoint: { x: number; y: number; timestamp: number },
  endPoint: { x: number; y: number; timestamp: number }
): { x: number; y: number; magnitude: number } {
  const deltaTime = endPoint.timestamp - startPoint.timestamp;
  
  if (deltaTime === 0) {
    return { x: 0, y: 0, magnitude: 0 };
  }

  const deltaX = endPoint.x - startPoint.x;
  const deltaY = endPoint.y - startPoint.y;
  
  const velocityX = deltaX / deltaTime;
  const velocityY = deltaY / deltaTime;
  const magnitude = Math.sqrt(velocityX * velocityX + velocityY * velocityY);

  return {
    x: velocityX,
    y: velocityY,
    magnitude,
  };
}

/**
 * Momentum scroll calculation
 */
export function calculateMomentumScroll(
  velocity: number,
  deceleration: number = 0.0006
): { distance: number; duration: number } {
  const speed = Math.abs(velocity);
  const duration = speed / deceleration;
  const distance = (speed * speed) / (2 * deceleration);
  
  return {
    distance: velocity < 0 ? -distance : distance,
    duration: Math.min(duration, 2000), // Cap at 2 seconds
  };
}

/**
 * Touch-safe event prevention
 */
export function preventTouchDefault(e: TouchEvent | Event, condition: boolean = true): void {
  if (condition && e.cancelable) {
    e.preventDefault();
  }
}

/**
 * Safe haptic feedback
 */
export function triggerHapticFeedback(
  pattern: 'success' | 'warning' | 'error' | 'selection' | number | number[]
): void {
  if (typeof navigator === 'undefined' || !navigator.vibrate) {
    return;
  }

  try {
    let vibrationPattern: number | number[];
    
    if (typeof pattern === 'string') {
      const patterns = {
        success: [100, 50, 100],
        warning: [200],
        error: [100, 100, 100],
        selection: [50],
      };
      vibrationPattern = patterns[pattern];
    } else {
      vibrationPattern = pattern;
    }
    
    navigator.vibrate(vibrationPattern);
  } catch (error) {
    console.warn('Haptic feedback failed:', error);
  }
}

/**
 * Touch-optimized scroll behavior
 */
export function smoothScrollTo(
  element: Element | Window,
  options: {
    top?: number;
    left?: number;
    behavior?: 'auto' | 'smooth';
    duration?: number;
  } = {}
): void {
  const { top, left, behavior = 'smooth', duration = 300 } = options;
  
  if ('scrollTo' in element) {
    element.scrollTo({
      top,
      left,
      behavior,
    });
  } else {
    // Fallback for older browsers
    if (top !== undefined) {
      element.scrollTop = top;
    }
    if (left !== undefined) {
      element.scrollLeft = left;
    }
  }
}

/**
 * Touch-safe element focusing
 */
export function focusElement(element: HTMLElement, options: {
  preventScroll?: boolean;
  selectText?: boolean;
} = {}): void {
  const { preventScroll = false, selectText = false } = options;
  
  try {
    element.focus({ preventScroll });
    
    if (selectText && 'select' in element) {
      (element as HTMLInputElement).select();
    }
  } catch (error) {
    console.warn('Focus failed:', error);
  }
}

/**
 * Touch interaction zones
 */
export interface TouchZone {
  x: number;
  y: number;
  width: number;
  height: number;
  action: string;
}

export function createTouchZones(
  containerRect: DOMRect,
  zones: Array<{
    region: 'left' | 'right' | 'top' | 'bottom' | 'center';
    percentage: number;
    action: string;
  }>
): TouchZone[] {
  return zones.map(zone => {
    const { region, percentage, action } = zone;
    let x, y, width, height;
    
    switch (region) {
      case 'left':
        x = 0;
        y = 0;
        width = containerRect.width * (percentage / 100);
        height = containerRect.height;
        break;
      case 'right':
        width = containerRect.width * (percentage / 100);
        x = containerRect.width - width;
        y = 0;
        height = containerRect.height;
        break;
      case 'top':
        x = 0;
        y = 0;
        width = containerRect.width;
        height = containerRect.height * (percentage / 100);
        break;
      case 'bottom':
        x = 0;
        height = containerRect.height * (percentage / 100);
        y = containerRect.height - height;
        width = containerRect.width;
        break;
      case 'center':
      default:
        const centerSize = Math.min(containerRect.width, containerRect.height) * (percentage / 100);
        x = (containerRect.width - centerSize) / 2;
        y = (containerRect.height - centerSize) / 2;
        width = centerSize;
        height = centerSize;
        break;
    }
    
    return { x, y, width, height, action };
  });
}

/**
 * Touch point within zone detection
 */
export function getTouchZoneAction(
  touchPoint: { x: number; y: number },
  zones: TouchZone[]
): string | null {
  for (const zone of zones) {
    if (
      touchPoint.x >= zone.x &&
      touchPoint.x <= zone.x + zone.width &&
      touchPoint.y >= zone.y &&
      touchPoint.y <= zone.y + zone.height
    ) {
      return zone.action;
    }
  }
  return null;
}

/**
 * Touch accessibility helpers
 */
export function addTouchAccessibility(element: HTMLElement, options: {
  role?: string;
  label?: string;
  description?: string;
  touchAction?: string;
} = {}): void {
  const { role, label, description, touchAction = 'manipulation' } = options;
  
  // Touch action for better touch handling
  element.style.touchAction = touchAction;
  
  // ARIA attributes
  if (role) element.setAttribute('role', role);
  if (label) element.setAttribute('aria-label', label);
  if (description) element.setAttribute('aria-description', description);
  
  // Touch-specific attributes
  element.setAttribute('tabindex', '0');
  element.style.userSelect = 'none';
  element.style.webkitUserSelect = 'none';
  element.style.webkitTouchCallout = 'none';
}

export default {
  detectTouchDevice,
  getTouchTargetGuidelines,
  calculateTouchSpacing,
  getTouchOptimizedClasses,
  isHorizontalGesture,
  isVerticalGesture,
  calculateVelocity,
  calculateMomentumScroll,
  preventTouchDefault,
  triggerHapticFeedback,
  smoothScrollTo,
  focusElement,
  createTouchZones,
  getTouchZoneAction,
  addTouchAccessibility,
};