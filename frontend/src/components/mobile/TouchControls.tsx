/**
 * TouchControls Components
 * 
 * Collection of touch-optimized interactive components including
 * swipe actions, touch buttons, and mobile-specific UI elements.
 */

import React, { useState, useRef, useCallback } from 'react';
import { 
  Heart, 
  Share2, 
  Bookmark, 
  MoreVertical, 
  Check, 
  X,
  Plus,
  Minus,
  RefreshCw
} from 'lucide-react';
import { useSwipe, useLongPress, useTouchButton, usePullToRefresh } from '@/hooks/useTouch';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { detectTouchDevice, getTouchOptimizedClasses, triggerHapticFeedback } from '@/utils/touchUtils';
import { cn } from '@/lib/utils';

/**
 * Swipe Action Component
 */
export interface SwipeAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'red' | 'blue' | 'green' | 'yellow' | 'gray';
  onAction: () => void;
}

export interface SwipeActionsProps {
  children: React.ReactNode;
  leftActions?: SwipeAction[];
  rightActions?: SwipeAction[];
  threshold?: number;
  className?: string;
  onSwipeStart?: () => void;
  onSwipeEnd?: () => void;
}

export const SwipeActions: React.FC<SwipeActionsProps> = ({
  children,
  leftActions = [],
  rightActions = [],
  threshold = 80,
  className = '',
  onSwipeStart,
  onSwipeEnd,
}) => {
  const [swipeState, setSwipeState] = useState<{
    offset: number;
    direction: 'left' | 'right' | null;
    isActive: boolean;
  }>({
    offset: 0,
    direction: null,
    isActive: false,
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const { getClassName, cssCustomProperties } = useReducedMotion();
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  const { handlers } = useSwipe(
    (gesture) => {
      const actions = gesture.direction === 'left' ? rightActions : leftActions;
      
      if (actions.length === 0 || Math.abs(gesture.distance) < threshold) {
        resetSwipe();
        return;
      }

      // Trigger first action if swipe is far enough
      if (Math.abs(gesture.distance) >= threshold * 1.5 && actions[0]) {
        actions[0].onAction();
        triggerHapticFeedback('success');
        resetSwipe();
      }
    },
    {
      threshold: 20,
      hapticFeedback: true,
    }
  );

  const resetSwipe = useCallback(() => {
    setSwipeState({ offset: 0, direction: null, isActive: false });
    onSwipeEnd?.();
  }, [onSwipeEnd]);

  const executeAction = useCallback((action: SwipeAction) => {
    action.onAction();
    triggerHapticFeedback('selection');
    resetSwipe();
  }, [resetSwipe]);

  const getActionColor = (color: SwipeAction['color']) => {
    const colors = {
      red: 'bg-red-500 text-white',
      blue: 'bg-blue-500 text-white',
      green: 'bg-green-500 text-white',
      yellow: 'bg-yellow-500 text-black',
      gray: 'bg-gray-500 text-white',
    };
    return colors[color];
  };

  const containerClasses = getClassName(
    'relative overflow-hidden',
    'transform transition-transform duration-200 ease-out',
    ''
  );

  return (
    <div 
      ref={containerRef}
      className={cn(containerClasses, className)}
      style={{ 
        transform: `translateX(${swipeState.offset}px)`,
        ...cssCustomProperties 
      }}
      {...handlers}
    >
      {/* Left Actions */}
      {leftActions.length > 0 && (
        <div className="absolute left-0 top-0 bottom-0 flex items-center -translate-x-full">
          {leftActions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.id}
                onClick={() => executeAction(action)}
                className={cn(
                  'flex items-center justify-center h-full px-6 transition-all duration-200',
                  touchClasses.touchTarget,
                  getActionColor(action.color)
                )}
                aria-label={action.label}
              >
                <Icon className="h-6 w-6" />
              </button>
            );
          })}
        </div>
      )}

      {/* Main Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Right Actions */}
      {rightActions.length > 0 && (
        <div className="absolute right-0 top-0 bottom-0 flex items-center translate-x-full">
          {rightActions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.id}
                onClick={() => executeAction(action)}
                className={cn(
                  'flex items-center justify-center h-full px-6 transition-all duration-200',
                  touchClasses.touchTarget,
                  getActionColor(action.color)
                )}
                aria-label={action.label}
              >
                <Icon className="h-6 w-6" />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

/**
 * Touch Button Component
 */
export interface TouchButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  haptic?: boolean;
  loading?: boolean;
  leftIcon?: React.ComponentType<{ className?: string }>;
  rightIcon?: React.ComponentType<{ className?: string }>;
}

export const TouchButton: React.FC<TouchButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  haptic = true,
  loading = false,
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  onClick,
  className = '',
  disabled,
  ...props
}) => {
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);
  const { getClassName } = useReducedMotion();

  const { handlers } = useTouchButton(
    () => onClick?.(new MouseEvent('click') as any),
    { hapticFeedback: haptic, disabled: disabled || loading }
  );

  const variantClasses = {
    primary: 'bg-brand-primary text-white hover:bg-brand-primary/90',
    secondary: 'bg-brand-secondary text-white hover:bg-brand-secondary/90',
    ghost: 'bg-transparent text-brand-primary hover:bg-brand-primary/10',
    danger: 'bg-red-500 text-white hover:bg-red-600',
  };

  const sizeClasses = {
    small: 'px-3 py-2 text-sm',
    medium: 'px-4 py-3 text-base',
    large: 'px-6 py-4 text-lg',
  };

  const buttonClasses = getClassName(
    'flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-primary/50 disabled:opacity-50 disabled:cursor-not-allowed',
    `${variantClasses[variant]} ${sizeClasses[size]}`,
    ''
  );

  return (
    <button
      className={cn(
        buttonClasses,
        touchClasses.touchTarget,
        touchClasses.interactive,
        className
      )}
      disabled={disabled || loading}
      {...handlers}
      {...props}
    >
      {loading && (
        <RefreshCw className="h-4 w-4 animate-spin" />
      )}
      {!loading && LeftIcon && (
        <LeftIcon className="h-4 w-4" />
      )}
      {children}
      {!loading && RightIcon && (
        <RightIcon className="h-4 w-4" />
      )}
    </button>
  );
};

/**
 * Touch Counter Component
 */
export interface TouchCounterProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  haptic?: boolean;
  showInput?: boolean;
  className?: string;
}

export const TouchCounter: React.FC<TouchCounterProps> = ({
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  disabled = false,
  haptic = true,
  showInput = false,
  className = '',
}) => {
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);
  const { getClassName } = useReducedMotion();

  const canDecrement = value > min;
  const canIncrement = value < max;

  const handleDecrement = useCallback(() => {
    if (canDecrement && !disabled) {
      onChange(Math.max(min, value - step));
      if (haptic) triggerHapticFeedback('selection');
    }
  }, [value, min, step, onChange, disabled, haptic, canDecrement]);

  const handleIncrement = useCallback(() => {
    if (canIncrement && !disabled) {
      onChange(Math.min(max, value + step));
      if (haptic) triggerHapticFeedback('selection');
    }
  }, [value, max, step, onChange, disabled, haptic, canIncrement]);

  const { handlers: decrementHandlers } = useTouchButton(handleDecrement, {
    hapticFeedback: haptic,
    disabled: !canDecrement || disabled,
  });

  const { handlers: incrementHandlers } = useTouchButton(handleIncrement, {
    hapticFeedback: haptic,
    disabled: !canIncrement || disabled,
  });

  const containerClasses = getClassName(
    'flex items-center gap-3',
    '',
    ''
  );

  const buttonClasses = getClassName(
    'flex items-center justify-center rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
    touchClasses.touchTarget,
    ''
  );

  return (
    <div className={cn(containerClasses, className)}>
      <button
        {...decrementHandlers}
        disabled={!canDecrement || disabled}
        className={cn(buttonClasses, touchClasses.interactive)}
        aria-label="Decrease value"
      >
        <Minus className="h-4 w-4" />
      </button>

      {showInput ? (
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(Number(e.target.value))}
          disabled={disabled}
          className="w-16 px-2 py-1 text-center border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-brand-primary/50"
        />
      ) : (
        <span className="min-w-[3rem] text-center font-medium text-lg">
          {value}
        </span>
      )}

      <button
        {...incrementHandlers}
        disabled={!canIncrement || disabled}
        className={cn(buttonClasses, touchClasses.interactive)}
        aria-label="Increase value"
      >
        <Plus className="h-4 w-4" />
      </button>
    </div>
  );
};

/**
 * Pull to Refresh Component
 */
export interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => void | Promise<void>;
  threshold?: number;
  disabled?: boolean;
  className?: string;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  threshold = 80,
  disabled = false,
  className = '',
}) => {
  const { 
    isRefreshing, 
    pullDistance, 
    isActive, 
    progress, 
    handlers 
  } = usePullToRefresh(onRefresh, { threshold, enabled: !disabled });

  const { getClassName } = useReducedMotion();

  const containerClasses = getClassName(
    'relative',
    'transition-transform duration-200',
    ''
  );

  const indicatorClasses = getClassName(
    'absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full bg-white rounded-b-lg shadow-lg px-4 py-2 flex items-center gap-2 text-sm text-gray-600',
    'transition-all duration-200',
    ''
  );

  return (
    <div 
      className={cn(containerClasses, className)}
      style={{ transform: `translateY(${Math.min(pullDistance, threshold)}px)` }}
      {...handlers}
    >
      {/* Pull indicator */}
      {isActive && (
        <div 
          className={indicatorClasses}
          style={{ 
            opacity: progress,
            transform: `translateX(-50%) translateY(${-100 + progress * 100}%)`,
          }}
        >
          {isRefreshing ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Refreshing...</span>
            </>
          ) : progress >= 1 ? (
            <>
              <Check className="h-4 w-4 text-green-500" />
              <span>Release to refresh</span>
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" style={{ transform: `rotate(${progress * 180}deg)` }} />
              <span>Pull to refresh</span>
            </>
          )}
        </div>
      )}

      {/* Content */}
      {children}
    </div>
  );
};

/**
 * Long Press Menu Component
 */
export interface LongPressMenuProps {
  children: React.ReactNode;
  menuItems: Array<{
    id: string;
    label: string;
    icon?: React.ComponentType<{ className?: string }>;
    onSelect: () => void;
    destructive?: boolean;
  }>;
  disabled?: boolean;
  className?: string;
}

export const LongPressMenu: React.FC<LongPressMenuProps> = ({
  children,
  menuItems,
  disabled = false,
  className = '',
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  const { handlers } = useLongPress(
    () => {
      if (!disabled) {
        setShowMenu(true);
        triggerHapticFeedback('warning');
      }
    },
    { disabled }
  );

  const handleMenuItemSelect = useCallback((item: typeof menuItems[0]) => {
    item.onSelect();
    setShowMenu(false);
    triggerHapticFeedback('selection');
  }, []);

  const handleCloseMenu = useCallback(() => {
    setShowMenu(false);
  }, []);

  return (
    <>
      <div className={cn('relative', className)} {...handlers}>
        {children}
      </div>

      {/* Menu overlay */}
      {showMenu && (
        <div 
          className="fixed inset-0 z-50 bg-black/20"
          onClick={handleCloseMenu}
        >
          <div 
            className="absolute bg-white rounded-lg shadow-xl border border-gray-200 py-2 min-w-[200px]"
            style={{
              left: Math.min(menuPosition.x, window.innerWidth - 220),
              top: Math.min(menuPosition.y, window.innerHeight - menuItems.length * 48 - 20),
            }}
          >
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => handleMenuItemSelect(item)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors',
                    touchClasses.touchTarget,
                    item.destructive ? 'text-red-600' : 'text-gray-900'
                  )}
                >
                  {Icon && <Icon className="h-5 w-5" />}
                  <span className="font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
};

export default {
  SwipeActions,
  TouchButton,
  TouchCounter,
  PullToRefresh,
  LongPressMenu,
};