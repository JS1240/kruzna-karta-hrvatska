/**
 * useTouch Hook
 * 
 * Comprehensive touch gesture detection and handling with motion preference awareness.
 * Provides touch gestures, accessibility features, and mobile optimizations.
 */

import { useCallback, useRef, useState, useEffect } from 'react';
import { useReducedMotion } from './useReducedMotion';

export interface TouchPoint {
  x: number;
  y: number;
  timestamp: number;
}

export interface TouchGestureConfig {
  threshold?: number;
  maxDuration?: number;
  minVelocity?: number;
  hapticFeedback?: boolean;
  preventScroll?: boolean;
  disabled?: boolean;
}

export interface SwipeGesture {
  direction: 'left' | 'right' | 'up' | 'down';
  distance: number;
  velocity: number;
  duration: number;
  startPoint: TouchPoint;
  endPoint: TouchPoint;
}

export interface PinchGesture {
  scale: number;
  center: TouchPoint;
  distance: number;
  velocity: number;
}

export interface TouchState {
  isPressed: boolean;
  isSwiping: boolean;
  isPinching: boolean;
  isLongPress: boolean;
  touchCount: number;
  startPoint: TouchPoint | null;
  currentPoint: TouchPoint | null;
  lastGesture: SwipeGesture | null;
}

/**
 * React hook for detecting and managing touch gestures, including swipe, pinch, and long press.
 *
 * Provides touch state, gesture event handlers, haptic feedback triggering, and velocity tracking. Supports configurable gesture thresholds, durations, velocity, haptic feedback, scroll prevention, and disabling.
 *
 * @returns An object containing the current touch state, touch event handlers, a haptic feedback trigger function, and the current velocity.
 */
export function useTouch(config: TouchGestureConfig = {}) {
  const {
    threshold = 50,
    maxDuration = 300,
    minVelocity = 0.5,
    hapticFeedback = true,
    preventScroll = false,
    disabled = false,
  } = config;

  const { shouldDisableAnimation } = useReducedMotion();
  
  const [touchState, setTouchState] = useState<TouchState>({
    isPressed: false,
    isSwiping: false,
    isPinching: false,
    isLongPress: false,
    touchCount: 0,
    startPoint: null,
    currentPoint: null,
    lastGesture: null,
  });

  const touchStartRef = useRef<TouchPoint | null>(null);
  const longPressTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const velocityRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const lastMoveTimeRef = useRef<number>(0);

  // Haptic feedback function
  const triggerHaptic = useCallback((type: 'light' | 'medium' | 'heavy' = 'light') => {
    if (!hapticFeedback || typeof navigator === 'undefined') return;
    
    try {
      if (navigator.vibrate) {
        const patterns = {
          light: [10],
          medium: [20],
          heavy: [50],
        };
        navigator.vibrate(patterns[type]);
      }
    } catch (error) {
      console.warn('Haptic feedback not supported:', error);
    }
  }, [hapticFeedback]);

  // Calculate swipe direction and properties
  const calculateSwipe = useCallback((start: TouchPoint, end: TouchPoint): SwipeGesture | null => {
    const deltaX = end.x - start.x;
    const deltaY = end.y - start.y;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    const duration = end.timestamp - start.timestamp;

    if (distance < threshold || duration > maxDuration) {
      return null;
    }

    const velocity = distance / duration;
    if (velocity < minVelocity) {
      return null;
    }

    let direction: SwipeGesture['direction'];
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      direction = deltaX > 0 ? 'right' : 'left';
    } else {
      direction = deltaY > 0 ? 'down' : 'up';
    }

    return {
      direction,
      distance,
      velocity,
      duration,
      startPoint: start,
      endPoint: end,
    };
  }, [threshold, maxDuration, minVelocity]);

  // Touch event handlers
  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (disabled) return;

    const touch = e.touches[0];
    const touchPoint: TouchPoint = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now(),
    };

    touchStartRef.current = touchPoint;
    lastMoveTimeRef.current = Date.now();

    setTouchState(prev => ({
      ...prev,
      isPressed: true,
      touchCount: e.touches.length,
      startPoint: touchPoint,
      currentPoint: touchPoint,
      isSwiping: false,
      isPinching: e.touches.length >= 2,
    }));

    // Start long press detection
    longPressTimeoutRef.current = setTimeout(() => {
      setTouchState(prev => ({ ...prev, isLongPress: true }));
      triggerHaptic('medium');
    }, 500);

    if (preventScroll) {
      e.preventDefault();
    }
  }, [disabled, preventScroll, triggerHaptic]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (disabled || !touchStartRef.current) return;

    const touch = e.touches[0];
    const currentPoint: TouchPoint = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now(),
    };

    // Calculate velocity
    const timeDelta = currentPoint.timestamp - lastMoveTimeRef.current;
    if (timeDelta > 0) {
      const prevPoint = touchState.currentPoint || touchStartRef.current;
      velocityRef.current = {
        x: (currentPoint.x - prevPoint.x) / timeDelta,
        y: (currentPoint.y - prevPoint.y) / timeDelta,
      };
    }
    lastMoveTimeRef.current = currentPoint.timestamp;

    setTouchState(prev => ({
      ...prev,
      currentPoint,
      isSwiping: true,
      touchCount: e.touches.length,
      isPinching: e.touches.length >= 2,
    }));

    // Clear long press if moving
    if (longPressTimeoutRef.current) {
      clearTimeout(longPressTimeoutRef.current);
      longPressTimeoutRef.current = null;
    }

    if (preventScroll) {
      e.preventDefault();
    }
  }, [disabled, preventScroll, touchState.currentPoint]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (disabled || !touchStartRef.current) return;

    const touch = e.changedTouches[0];
    const endPoint: TouchPoint = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now(),
    };

    // Calculate swipe gesture
    const swipeGesture = calculateSwipe(touchStartRef.current, endPoint);

    setTouchState(prev => ({
      ...prev,
      isPressed: false,
      isSwiping: false,
      isPinching: false,
      isLongPress: false,
      touchCount: e.touches.length,
      lastGesture: swipeGesture,
    }));

    // Clear long press timeout
    if (longPressTimeoutRef.current) {
      clearTimeout(longPressTimeoutRef.current);
      longPressTimeoutRef.current = null;
    }

    // Reset refs
    touchStartRef.current = null;
    velocityRef.current = { x: 0, y: 0 };
  }, [disabled, calculateSwipe]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (longPressTimeoutRef.current) {
        clearTimeout(longPressTimeoutRef.current);
      }
    };
  }, []);

  return {
    touchState,
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
    triggerHaptic,
    velocity: velocityRef.current,
  };
}

/**
 * React hook that detects swipe gestures and invokes a callback with gesture details.
 *
 * Calls the provided `onSwipe` function whenever a swipe gesture is recognized, passing information about the gesture such as direction, distance, velocity, and duration.
 *
 * @returns The current touch state and touch event handlers to attach to a touchable element.
 */
export function useSwipe(
  onSwipe: (gesture: SwipeGesture) => void,
  config: TouchGestureConfig = {}
) {
  const { touchState, handlers } = useTouch(config);

  useEffect(() => {
    if (touchState.lastGesture) {
      onSwipe(touchState.lastGesture);
    }
  }, [touchState.lastGesture, onSwipe]);

  return {
    ...touchState,
    handlers,
  };
}

/**
 * React hook for detecting long press gestures and invoking a callback.
 *
 * Calls the provided `onLongPress` function when a long press gesture is recognized based on the configured duration and thresholds.
 *
 * @returns The current touch state and touch event handlers.
 */
export function useLongPress(
  onLongPress: () => void,
  config: TouchGestureConfig = {}
) {
  const { touchState, handlers } = useTouch(config);

  useEffect(() => {
    if (touchState.isLongPress) {
      onLongPress();
    }
  }, [touchState.isLongPress, onLongPress]);

  return {
    ...touchState,
    handlers,
  };
}

/**
 * Provides touch-friendly button behavior with tap detection, optional double-tap prevention, and haptic feedback.
 *
 * Triggers the `onClick` callback on a simple tap (not a swipe or long press). If `preventDoubleClick` is enabled, ignores taps within the `doubleTapWindow` interval. Haptic feedback is triggered on tap.
 *
 * @returns Touch state and event handlers for use on touchable elements
 */
export function useTouchButton(
  onClick: () => void,
  config: TouchGestureConfig & { 
    doubleTapWindow?: number;
    preventDoubleClick?: boolean;
  } = {}
) {
  const { doubleTapWindow = 300, preventDoubleClick = false } = config;
  const [lastTap, setLastTap] = useState<number>(0);
  const { touchState, handlers, triggerHaptic } = useTouch(config);

  const handleClick = useCallback(() => {
    const now = Date.now();
    
    if (preventDoubleClick && now - lastTap < doubleTapWindow) {
      return; // Ignore double tap
    }
    
    setLastTap(now);
    triggerHaptic('light');
    onClick();
  }, [onClick, lastTap, doubleTapWindow, preventDoubleClick, triggerHaptic]);

  useEffect(() => {
    if (touchState.isPressed && !touchState.isSwiping && !touchState.isLongPress) {
      // Simple tap detected
      const timeout = setTimeout(() => {
        if (!touchState.isSwiping) {
          handleClick();
        }
      }, 50); // Small delay to distinguish from swipe

      return () => clearTimeout(timeout);
    }
  }, [touchState.isPressed, touchState.isSwiping, touchState.isLongPress, handleClick]);

  return {
    ...touchState,
    handlers,
  };
}

/**
 * Implements a pull-to-refresh gesture, triggering a refresh callback when the user pulls down from the top of the page past a configurable threshold.
 *
 * @param onRefresh - Callback invoked when the pull distance exceeds the threshold; supports both synchronous and asynchronous operations.
 * @returns An object containing `isRefreshing` (refresh in progress), `pullDistance` (current pull distance in pixels), `isActive` (whether a pull gesture is active), `progress` (pull progress ratio from 0 to 1), and touch event handlers.
 */
export function usePullToRefresh(
  onRefresh: () => void | Promise<void>,
  config: { threshold?: number; enabled?: boolean } = {}
) {
  const { threshold = 80, enabled = true } = config;
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);

  const { touchState, handlers } = useTouch({
    threshold: 10,
    preventScroll: false,
    disabled: !enabled,
  });

  useEffect(() => {
    if (!touchState.isSwiping || !touchState.startPoint || !touchState.currentPoint) {
      setPullDistance(0);
      return;
    }

    const deltaY = touchState.currentPoint.y - touchState.startPoint.y;
    
    // Only trigger if pulling down from top of page
    if (deltaY > 0 && window.scrollY === 0) {
      setPullDistance(Math.min(deltaY, threshold * 1.5));
      
      // Trigger refresh when threshold is reached and touch ends
      if (deltaY >= threshold && !touchState.isPressed && !isRefreshing) {
        setIsRefreshing(true);
        
        Promise.resolve(onRefresh()).finally(() => {
          setIsRefreshing(false);
          setPullDistance(0);
        });
      }
    }
  }, [touchState, threshold, onRefresh, isRefreshing]);

  return {
    isRefreshing,
    pullDistance,
    isActive: pullDistance > 0,
    progress: Math.min(pullDistance / threshold, 1),
    handlers,
  };
}

export default useTouch;