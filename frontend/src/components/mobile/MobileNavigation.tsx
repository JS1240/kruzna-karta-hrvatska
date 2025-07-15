/**
 * MobileNavigation Component
 * 
 * Touch-optimized mobile navigation with hamburger menu,
 * swipe gestures, and accessibility features.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Menu, 
  X, 
  Home, 
  Calendar, 
  MapPin, 
  Heart, 
  User, 
  Search,
  Settings,
  ChevronRight
} from 'lucide-react';
import { useSwipe, useTouchButton } from '@/hooks/useTouch';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { detectTouchDevice, getTouchOptimizedClasses, addTouchAccessibility } from '@/utils/touchUtils';
import { cn } from '@/lib/utils';

export interface NavigationItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  external?: boolean;
}

export interface MobileNavigationProps {
  items?: NavigationItem[];
  isOpen?: boolean;
  onToggle?: (isOpen: boolean) => void;
  className?: string;
  overlayClassName?: string;
  drawerClassName?: string;
}

const defaultNavigationItems: NavigationItem[] = [
  { id: 'home', label: 'Home', href: '/', icon: Home },
  { id: 'events', label: 'Events', href: '/events', icon: Calendar },
  { id: 'destinations', label: 'Destinations', href: '/destinations', icon: MapPin },
  { id: 'favorites', label: 'Favorites', href: '/favorites', icon: Heart },
  { id: 'profile', label: 'Profile', href: '/profile', icon: User },
  { id: 'search', label: 'Search', href: '/search', icon: Search },
];

/**
 * Mobile Navigation Drawer
 */
export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  items = defaultNavigationItems,
  isOpen = false,
  onToggle,
  className = '',
  overlayClassName = '',
  drawerClassName = '',
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [internalIsOpen, setInternalIsOpen] = useState(isOpen);
  const [isAnimating, setIsAnimating] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  const {
    prefersReducedMotion,
    getClassName,
    cssCustomProperties,
  } = useReducedMotion();

  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  // Control drawer state
  const isDrawerOpen = onToggle ? isOpen : internalIsOpen;
  const setDrawerOpen = useCallback((open: boolean) => {
    if (onToggle) {
      onToggle(open);
    } else {
      setInternalIsOpen(open);
    }
  }, [onToggle]);

  // Handle swipe to close
  const { handlers: swipeHandlers } = useSwipe(
    (gesture) => {
      if (gesture.direction === 'left' && isDrawerOpen) {
        setDrawerOpen(false);
      }
    },
    {
      threshold: 50,
      hapticFeedback: true,
    }
  );

  // Handle hamburger button
  const { handlers: menuButtonHandlers } = useTouchButton(() => {
    setDrawerOpen(!isDrawerOpen);
  }, {
    hapticFeedback: true,
  });

  // Handle navigation item clicks
  const handleNavItemClick = useCallback((item: NavigationItem) => {
    if (item.external) {
      window.open(item.href, '_blank', 'noopener,noreferrer');
    } else {
      navigate(item.href);
    }
    setDrawerOpen(false);
  }, [navigate, setDrawerOpen]);

  // Handle overlay click
  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      setDrawerOpen(false);
    }
  }, [setDrawerOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDrawerOpen) {
        setDrawerOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isDrawerOpen, setDrawerOpen]);

  // Focus management
  useEffect(() => {
    if (isDrawerOpen) {
      // Focus first navigation item
      const firstNavItem = drawerRef.current?.querySelector('button, a');
      if (firstNavItem instanceof HTMLElement) {
        firstNavItem.focus();
      }
    }
  }, [isDrawerOpen]);

  // Animation classes
  const overlayClasses = getClassName(
    'fixed inset-0 bg-black/50 backdrop-blur-sm z-50',
    // Motion classes
    `transition-opacity duration-300 ${isDrawerOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`,
    // Reduced motion classes
    isDrawerOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
  );

  const drawerClasses = getClassName(
    'fixed top-0 left-0 h-full w-80 max-w-[85vw] bg-white shadow-xl z-50 overflow-y-auto',
    // Motion classes
    `transform transition-transform duration-300 ease-out ${
      isDrawerOpen ? 'translate-x-0' : '-translate-x-full'
    }`,
    // Reduced motion classes
    isDrawerOpen ? 'translate-x-0' : '-translate-x-full'
  );

  return (
    <>
      {/* Hamburger Menu Button */}
      <button
        {...menuButtonHandlers}
        className={cn(
          'p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-primary transition-colors',
          touchClasses.touchTarget,
          touchClasses.interactive,
          className
        )}
        style={cssCustomProperties}
        aria-label={isDrawerOpen ? 'Close menu' : 'Open menu'}
        aria-expanded={isDrawerOpen}
        aria-controls="mobile-navigation-drawer"
      >
        {isDrawerOpen ? (
          <X className="h-6 w-6 text-brand-primary" />
        ) : (
          <Menu className="h-6 w-6 text-brand-primary" />
        )}
      </button>

      {/* Overlay */}
      <div
        ref={overlayRef}
        className={cn(overlayClasses, overlayClassName)}
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* Navigation Drawer */}
      <nav
        ref={drawerRef}
        id="mobile-navigation-drawer"
        className={cn(drawerClasses, drawerClassName)}
        style={cssCustomProperties}
        aria-label="Mobile navigation"
        {...swipeHandlers}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-brand-primary font-sreda">
            Kružna Karta
          </h2>
          <button
            onClick={() => setDrawerOpen(false)}
            className={cn(
              'p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-primary transition-colors',
              touchClasses.touchTarget,
              touchClasses.interactive
            )}
            aria-label="Close menu"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        {/* Navigation Items */}
        <div className="py-4">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;

            return (
              <button
                key={item.id}
                onClick={() => handleNavItemClick(item)}
                className={cn(
                  'w-full flex items-center gap-4 px-6 py-4 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition-colors group',
                  touchClasses.touchTarget,
                  isActive && 'bg-brand-primary/10 border-r-4 border-brand-primary'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon 
                  className={cn(
                    'h-6 w-6 transition-colors',
                    isActive ? 'text-brand-primary' : 'text-gray-600 group-hover:text-brand-primary'
                  )} 
                />
                <span 
                  className={cn(
                    'font-medium transition-colors',
                    isActive ? 'text-brand-primary' : 'text-gray-900 group-hover:text-brand-primary'
                  )}
                >
                  {item.label}
                </span>
                {item.badge && (
                  <span className="ml-auto bg-brand-primary text-white text-xs px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
                <ChevronRight 
                  className={cn(
                    'h-4 w-4 ml-auto transition-colors',
                    isActive ? 'text-brand-primary' : 'text-gray-400 group-hover:text-brand-primary'
                  )} 
                />
              </button>
            );
          })}
        </div>

        {/* Footer Actions */}
        <div className="mt-auto p-6 border-t border-gray-200">
          <button
            onClick={() => {
              navigate('/settings');
              setDrawerOpen(false);
            }}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:text-brand-primary hover:bg-gray-50 rounded-lg transition-colors',
              touchClasses.touchTarget,
              touchClasses.interactive
            )}
          >
            <Settings className="h-5 w-5" />
            <span className="font-medium">Settings</span>
          </button>
        </div>
      </nav>
    </>
  );
};

/**
 * Mobile Bottom Navigation Bar
 */
export interface MobileBottomNavProps {
  items?: NavigationItem[];
  className?: string;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  items = defaultNavigationItems.slice(0, 5), // Limit to 5 items for bottom nav
  className = '',
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  const { getClassName, cssCustomProperties } = useReducedMotion();

  const handleItemClick = useCallback((item: NavigationItem) => {
    if (item.external) {
      window.open(item.href, '_blank', 'noopener,noreferrer');
    } else {
      navigate(item.href);
    }
  }, [navigate]);

  const navClasses = getClassName(
    'fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40',
    // Motion classes
    'transform transition-transform duration-200',
    // Reduced motion classes
    ''
  );

  return (
    <nav 
      className={cn(navClasses, className)}
      style={cssCustomProperties}
      aria-label="Bottom navigation"
    >
      <div className="flex items-center justify-around px-2 py-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;

          return (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              className={cn(
                'flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors relative',
                touchClasses.touchTarget,
                touchClasses.interactive,
                isActive ? 'text-brand-primary' : 'text-gray-600 hover:text-brand-primary'
              )}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="h-6 w-6" />
              <span className="text-xs font-medium">{item.label}</span>
              {item.badge && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {item.badge}
                </span>
              )}
              {isActive && (
                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-brand-primary rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNavigation;