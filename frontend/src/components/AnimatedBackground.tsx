import React, { useRef, useEffect, useState } from 'react';
import { initVantaTopology, cleanupVantaEffect, initBlueOnlyTopology, initGentleTopology } from '@/utils/vantaUtils';
import { BRAND_COLORS } from '@/utils/colorUtils';
import { 
  generateOverlayBackground, 
  getOverlayBackdropFilter, 
  getTextContrastClasses, 
  generateOverlayClasses,
  type OverlayMode,
  type OverlayStyle,
  type TextContrast 
} from '@/utils/overlayUtils';

export interface AnimatedBackgroundProps {
  /** Enable/disable the animation */
  enabled?: boolean;
  /** Animation intensity (0-1, default: 0.5) */
  intensity?: number;
  /** Background opacity (0-1, default: 0.3) */
  opacity?: number;
  /** Custom colors override (uses brand colors by default) */
  colors?: {
    primary?: string;
    secondary?: string;
  };
  /** Additional CSS classes */
  className?: string;
  /** Children to render over the animated background */
  children?: React.ReactNode;
  /** Unique identifier for the VANTA effect */
  id?: string;
  /** Performance mode: 'high' | 'medium' | 'low' */
  performance?: 'high' | 'medium' | 'low';
  /** Enable reduced motion compliance */
  respectReducedMotion?: boolean;
  /** Use blue-only color scheme (T3.2) */
  blueOnly?: boolean;
  /** Blue intensity for blue-only mode: 'light' | 'medium' | 'dark' */
  blueIntensity?: 'light' | 'medium' | 'dark';
  /** Enable gentle movement mode (T3.3) */
  gentleMovement?: boolean;
  /** Gentle movement mode: 'normal' | 'ultra' */
  gentleMode?: 'normal' | 'ultra';
  /** Movement speed for gentle mode (0-1, default: 0.3) */
  movementSpeed?: number;
  /** Enable subtle transparency effects (T3.4) */
  subtleOpacity?: boolean;
  /** Opacity mode: 'minimal' | 'low' | 'medium' | 'adaptive' */
  opacityMode?: 'minimal' | 'low' | 'medium' | 'adaptive';
  /** Background blur intensity for layered transparency (0-20, default: 0) */
  backgroundBlur?: number;
  /** Enable fade-in/fade-out transitions */
  opacityTransitions?: boolean;
  /** Enable adjustable blur effects (T3.5) */
  adjustableBlur?: boolean;
  /** Blur type: 'background' | 'content' | 'edge' | 'dynamic' */
  blurType?: 'background' | 'content' | 'edge' | 'dynamic';
  /** Blur intensity level: 'light' | 'medium' | 'heavy' | 'custom' */
  blurIntensity?: 'light' | 'medium' | 'heavy' | 'custom';
  /** Custom blur value when blurIntensity is 'custom' (0-50, default: 10) */
  customBlurValue?: number;
  /** Content blur radius for content-aware blur (0-20, default: 4) */
  contentBlur?: number;
  /** Edge blur feathering for smoother transitions (0-15, default: 6) */
  edgeBlur?: number;
  /** Enable responsive behavior for different screen sizes (T3.6) */
  responsive?: boolean;
  /** Responsive mode: 'auto' | 'manual' | 'disabled' */
  responsiveMode?: 'auto' | 'manual' | 'disabled';
  /** Custom responsive breakpoints override */
  responsiveBreakpoints?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  /** Mobile-specific intensity override (0-1) */
  mobileIntensity?: number;
  /** Tablet-specific intensity override (0-1) */
  tabletIntensity?: number;
  /** Desktop-specific intensity override (0-1) */
  desktopIntensity?: number;
  /** Enable content overlay handling (T4.3) */
  overlayMode?: OverlayMode;
  /** Overlay visual style type */
  overlayStyle?: OverlayStyle;
  /** Custom overlay background color (hex or rgba) */
  overlayColor?: string;
  /** Custom overlay opacity (0-1, default: auto-calculated) */
  overlayOpacity?: number;
  /** Automatic text contrast adjustment */
  textContrast?: TextContrast;
  /** Overlay padding override (default: 'p-8') */
  overlayPadding?: string;
}

/**
 * AnimatedBackground component using VANTA.js topology animation
 * 
 * Features:
 * - Brand color integration (#3674B5, #578FCA)
 * - Performance optimization with device detection
 * - Accessibility support with prefers-reduced-motion
 * - Responsive behavior
 * - Smooth initialization and cleanup
 * - T3.1: Base VANTA topology animation
 * - T3.2: Blue-only color schemes with intensity variants
 * - T3.3: Gentle movement modes for subtle animations
 * - T3.4: Subtle opacity and transparency effects
 * - T3.5: Adjustable blur effects with multiple blur types
 * - T3.6: Responsive behavior for different screen sizes
 * - T4.3: Content overlay handling with proper blur effects
 * 
 * @example
 * ```tsx
 * <AnimatedBackground 
 *   intensity={0.3} 
 *   opacity={0.2}
 *   adjustableBlur={true}
 *   blurType="dynamic"
 *   blurIntensity="medium"
 *   responsive={true}
 *   responsiveMode="auto"
 *   mobileIntensity={0.2}
 *   overlayMode="medium"
 *   overlayStyle="glass"
 *   textContrast="auto"
 * >
 *   <div>Your content here</div>
 * </AnimatedBackground>
 * ```
 */
export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({
  enabled = true,
  intensity = 0.5,
  opacity = 0.3,
  colors,
  className = '',
  children,
  id,
  performance = 'medium',
  respectReducedMotion = true,
  blueOnly = false,
  blueIntensity = 'medium',
  gentleMovement = false,
  gentleMode = 'normal',
  movementSpeed = 0.3,
  subtleOpacity = false,
  opacityMode = 'medium',
  backgroundBlur = 0,
  opacityTransitions = true,
  adjustableBlur = false,
  blurType = 'background',
  blurIntensity = 'medium',
  customBlurValue = 10,
  contentBlur = 4,
  edgeBlur = 6,
  responsive = true,
  responsiveMode = 'auto',
  responsiveBreakpoints = {
    mobile: 768,
    tablet: 1024,
    desktop: 1280,
  },
  mobileIntensity,
  tabletIntensity,
  desktopIntensity,
  overlayMode = 'none',
  overlayStyle = 'glass',
  overlayColor,
  overlayOpacity,
  textContrast = 'auto',
  overlayPadding = 'p-8',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const vantaEffectRef = useRef<any>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for reduced motion preference
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  
  // T3.6: Responsive behavior state
  const [screenSize, setScreenSize] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  // T3.6: Screen size detection utility
  const getScreenSize = (width: number): 'mobile' | 'tablet' | 'desktop' => {
    if (width < responsiveBreakpoints.mobile!) return 'mobile';
    if (width < responsiveBreakpoints.tablet!) return 'tablet';
    return 'desktop';
  };

  // T3.6: Get responsive intensity based on screen size
  const getResponsiveIntensity = (): number => {
    if (!responsive || responsiveMode === 'disabled') return intensity;
    
    const currentScreenSize = getScreenSize(windowSize.width);
    
    // Use device-specific intensity if provided
    if (currentScreenSize === 'mobile' && mobileIntensity !== undefined) {
      return mobileIntensity;
    }
    if (currentScreenSize === 'tablet' && tabletIntensity !== undefined) {
      return tabletIntensity;
    }
    if (currentScreenSize === 'desktop' && desktopIntensity !== undefined) {
      return desktopIntensity;
    }
    
    // Default responsive scaling
    switch (currentScreenSize) {
      case 'mobile':
        return intensity * 0.6; // 40% reduction for mobile
      case 'tablet':
        return intensity * 0.8; // 20% reduction for tablet
      default:
        return intensity; // Full intensity for desktop
    }
  };

  // T3.6: Get responsive performance mode
  const getResponsivePerformance = (): 'high' | 'medium' | 'low' => {
    if (!responsive || responsiveMode === 'disabled') return performance;
    
    const currentScreenSize = getScreenSize(windowSize.width);
    
    switch (currentScreenSize) {
      case 'mobile':
        return performance === 'high' ? 'medium' : 'low';
      case 'tablet':
        return performance === 'high' ? 'medium' : performance;
      default:
        return performance;
    }
  };

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // T3.6: Window resize detection and screen size tracking
  useEffect(() => {
    const updateWindowSize = () => {
      const newSize = {
        width: window.innerWidth,
        height: window.innerHeight,
      };
      setWindowSize(newSize);
      
      if (responsive && responsiveMode === 'auto') {
        const newScreenSize = getScreenSize(newSize.width);
        if (newScreenSize !== screenSize) {
          setScreenSize(newScreenSize);
        }
      }
    };

    // Set initial size
    updateWindowSize();

    // Add resize listener
    const handleResize = () => {
      updateWindowSize();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [responsive, responsiveMode, screenSize, responsiveBreakpoints]);

  // Performance settings based on performance mode and responsive behavior
  const getPerformanceSettings = () => {
    const currentPerformance = getResponsivePerformance();
    const currentScreenSize = getScreenSize(windowSize.width);
    
    const baseSettings = {
      high: {
        maxDistance: 25,
        spacing: 18,
        points: 12,
        forceAnimate: true,
      },
      medium: {
        maxDistance: 20,
        spacing: 20,
        points: 10,
        forceAnimate: false,
      },
      low: {
        maxDistance: 15,
        spacing: 25,
        points: 8,
        forceAnimate: false,
      },
    };

    const settings = baseSettings[currentPerformance];

    // T3.6: Apply responsive adjustments
    if (responsive && responsiveMode === 'auto') {
      switch (currentScreenSize) {
        case 'mobile':
          return {
            ...settings,
            points: Math.max(4, Math.floor(settings.points * 0.6)), // Further reduce particles on mobile
            spacing: settings.spacing * 1.2, // Increase spacing for better performance
            maxDistance: Math.max(10, settings.maxDistance * 0.8), // Reduce max distance
            scaleMobile: 0.8, // VANTA mobile scaling
          };
        case 'tablet':
          return {
            ...settings,
            points: Math.floor(settings.points * 0.8), // Slightly reduce particles on tablet
            spacing: settings.spacing * 1.1, // Slightly increase spacing
            maxDistance: settings.maxDistance * 0.9, // Slightly reduce max distance
            scaleMobile: 0.9, // VANTA tablet scaling
          };
        default:
          return {
            ...settings,
            scaleMobile: 1.0, // Full scale for desktop
          };
      }
    }

    return settings;
  };

  useEffect(() => {
    // Don't initialize if disabled, reduced motion is preferred, or no container
    if (!enabled || !containerRef.current || (respectReducedMotion && prefersReducedMotion)) {
      setIsLoaded(true);
      return;
    }

    const initializeAnimation = async () => {
      try {
        // Use provided colors or default to brand colors
        const animationColors = {
          primary: colors?.primary || BRAND_COLORS.primary,
          secondary: colors?.secondary || BRAND_COLORS.secondary,
        };

        const performanceSettings = getPerformanceSettings();
        const optimalOpacity = getOptimalOpacity();
        const responsiveIntensity = getResponsiveIntensity(); // T3.6: Use responsive intensity

        let effect;
        // Initialize VANTA effect with appropriate configuration mode
        if (gentleMovement) {
          // Gentle movement mode (T3.3) - slow, subtle animations with minimal particles
          effect = await initGentleTopology({
            element: containerRef.current!,
            intensity: responsiveIntensity * 0.7, // Use responsive intensity with gentle reduction
            opacity: optimalOpacity * 0.8, // Use calculated opacity with gentle reduction
            id: id || 'default-animated-bg',
            blueIntensity: blueIntensity || 'light', // Default to light blue for gentleness
            gentleMode,
            movementSpeed,
            ...performanceSettings,
          });
        } else if (blueOnly) {
          // Blue-only mode (T3.2)
          effect = await initBlueOnlyTopology({
            element: containerRef.current!,
            intensity: responsiveIntensity, // Use responsive intensity
            opacity: optimalOpacity, // Use calculated optimal opacity
            id: id || 'default-animated-bg',
            blueIntensity,
            ...performanceSettings,
          });
        } else {
          // Regular mode
          effect = await initVantaTopology({
            element: containerRef.current!,
            colors: animationColors,
            intensity: responsiveIntensity, // Use responsive intensity
            opacity: optimalOpacity, // Use calculated optimal opacity
            id: id || 'default-animated-bg',
            ...performanceSettings,
          });
        }

        if (effect) {
          vantaEffectRef.current = effect;
          setIsLoaded(true);
          setError(null);
        } else {
          throw new Error('Failed to initialize VANTA effect');
        }
      } catch (err) {
        console.error('AnimatedBackground initialization error:', err);
        setError(err instanceof Error ? err.message : 'Animation initialization failed');
        setIsLoaded(true); // Still mark as loaded to show fallback
      }
    };

    // Small delay to ensure DOM is ready
    const timeoutId = setTimeout(initializeAnimation, 100);

    return () => {
      clearTimeout(timeoutId);
      if (vantaEffectRef.current) {
        cleanupVantaEffect(vantaEffectRef.current);
        vantaEffectRef.current = null;
      }
    };
  }, [enabled, intensity, opacity, colors, id, performance, prefersReducedMotion, respectReducedMotion, blueOnly, blueIntensity, gentleMovement, gentleMode, movementSpeed, subtleOpacity, opacityMode, backgroundBlur, opacityTransitions, adjustableBlur, blurType, blurIntensity, customBlurValue, contentBlur, edgeBlur, responsive, responsiveMode, responsiveBreakpoints, mobileIntensity, tabletIntensity, desktopIntensity, screenSize, windowSize]);

  // Update effect settings when props change (T3.6: Include responsive updates)
  useEffect(() => {
    if (vantaEffectRef.current && vantaEffectRef.current.setOptions) {
      const performanceSettings = getPerformanceSettings();
      const responsiveIntensity = getResponsiveIntensity();
      
      vantaEffectRef.current.setOptions({
        ...performanceSettings,
        // Update responsive intensity and performance if VANTA effect supports it
      });
    }
  }, [intensity, opacity, performance, responsive, responsiveMode, screenSize, windowSize, mobileIntensity, tabletIntensity, desktopIntensity]);

  // Calculate optimal opacity based on opacity mode and settings (T3.4)
  const getOptimalOpacity = () => {
    if (!subtleOpacity) {
      return opacity; // Use provided opacity if subtleOpacity is disabled
    }

    const baseOpacities = {
      minimal: 0.05,   // Barely visible - for maximum subtlety
      low: 0.15,       // Low visibility - subtle background effect
      medium: 0.25,    // Moderate visibility - balanced effect
      adaptive: 0.2    // Adaptive - adjusts based on context
    };

    let calculatedOpacity = baseOpacities[opacityMode];

    // Adaptive mode adjustments
    if (opacityMode === 'adaptive') {
      // Reduce opacity further for gentle movement
      if (gentleMovement) {
        calculatedOpacity *= 0.7;
      }
      
      // Reduce opacity for high performance mode (more particles = lower individual opacity)
      if (performance === 'high') {
        calculatedOpacity *= 0.8;
      }
      
      // T3.6: Responsive opacity adjustments
      if (responsive && responsiveMode === 'auto') {
        const currentScreenSize = getScreenSize(windowSize.width);
        switch (currentScreenSize) {
          case 'mobile':
            calculatedOpacity *= 1.3; // Increase opacity on mobile (fewer particles)
            break;
          case 'tablet':
            calculatedOpacity *= 1.1; // Slightly increase opacity on tablet
            break;
          // Desktop keeps default opacity
        }
      } else {
        // Legacy mobile detection for backwards compatibility
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (isMobile) {
          calculatedOpacity *= 1.2;
        }
      }
    }

    // Ensure opacity stays within reasonable bounds
    return Math.max(0.05, Math.min(calculatedOpacity, opacity));
  };

  // Calculate blur value based on intensity level (T3.5)
  const getBlurValue = (): number => {
    if (!adjustableBlur) {
      return backgroundBlur; // Fall back to T3.4 background blur if adjustableBlur is disabled
    }

    const blurIntensityMap = {
      light: 3,      // Subtle blur for minimal interference
      medium: 8,     // Balanced blur for moderate depth
      heavy: 15,     // Strong blur for dramatic effect
      custom: customBlurValue || 10 // User-defined blur value
    };

    return blurIntensityMap[blurIntensity];
  };

  // Generate CSS filter string based on blur type (T3.5)
  const getBlurFilter = (): string => {
    if (!adjustableBlur) {
      return ''; // No additional filters if adjustableBlur is disabled
    }

    const blurValue = getBlurValue();
    const filters: string[] = [];

    switch (blurType) {
      case 'background':
        // Standard backdrop filter for background blur
        return ''; // Handled by backdrop-filter in getBackgroundStyling
        
      case 'content':
        // Content-aware blur that preserves text readability
        filters.push(`blur(${Math.min(blurValue * 0.3, contentBlur)}px)`);
        filters.push(`contrast(1.1)`); // Slightly increase contrast to offset blur
        break;
        
      case 'edge':
        // Edge feathering for smooth transitions
        filters.push(`blur(${Math.min(blurValue * 0.5, edgeBlur)}px)`);
        filters.push(`drop-shadow(0 0 ${edgeBlur}px rgba(0,0,0,0.1))`);
        break;
        
      case 'dynamic':
        // Dynamic blur that adapts to animation intensity and responsive behavior
        let dynamicIntensity = intensity;
        
        // T3.6: Use responsive intensity for dynamic blur
        if (responsive && responsiveMode === 'auto') {
          dynamicIntensity = getResponsiveIntensity();
        }
        
        const dynamicBlur = blurValue * (dynamicIntensity * 0.8 + 0.2);
        filters.push(`blur(${dynamicBlur}px)`);
        
        // Add brightness adjustment for gentle movement
        if (gentleMovement) {
          filters.push(`brightness(1.05)`);
        }
        break;
    }

    return filters.length > 0 ? filters.join(' ') : '';
  };

  // Get comprehensive blur styling combining T3.4 and T3.5 features
  const getBlurStyling = (): React.CSSProperties => {
    const blurValue = getBlurValue();
    const contentFilter = getBlurFilter();
    
    const styling: React.CSSProperties = {};

    // T3.5: Adjustable blur effects
    if (adjustableBlur) {
      // Background blur using backdrop-filter
      if (blurType === 'background' || blurType === 'dynamic') {
        styling.backdropFilter = `blur(${blurValue}px)`;
        styling.WebkitBackdropFilter = `blur(${blurValue}px)`;
      }
      
      // Content blur using CSS filter
      if (contentFilter) {
        styling.filter = contentFilter;
      }

      // Edge blur with additional shadow effects
      if (blurType === 'edge') {
        styling.boxShadow = `inset 0 0 ${edgeBlur * 2}px rgba(0,0,0,0.05)`;
      }
      
      // Dynamic blur transitions
      if (blurType === 'dynamic' && opacityTransitions) {
        styling.transition = 'backdrop-filter 1s ease-in-out, filter 0.8s ease-in-out';
      }
    } else {
      // T3.4: Simple background blur fallback
      if (backgroundBlur > 0) {
        styling.backdropFilter = `blur(${backgroundBlur}px)`;
        styling.WebkitBackdropFilter = `blur(${backgroundBlur}px)`;
      }
    }

    return styling;
  };


  // Get background styling with blur and transparency effects
  const getBackgroundStyling = () => {
    const finalOpacity = getOptimalOpacity();
    const blurStyling = getBlurStyling(); // T3.5: Use new comprehensive blur styling
    
    const styling: React.CSSProperties = {
      opacity: finalOpacity,
      ...blurStyling, // Merge T3.5 blur effects
    };

    // Add transition effects if enabled
    if (opacityTransitions) {
      const baseTransition = 'opacity 0.8s ease-in-out';
      const blurTransition = adjustableBlur ? ', backdrop-filter 0.5s ease-in-out, filter 0.5s ease-in-out' : ', backdrop-filter 0.5s ease-in-out';
      styling.transition = baseTransition + blurTransition;
    }

    return styling;
  };

  // Fallback background when animation is disabled or failed
  const fallbackStyle = {
    background: !enabled || prefersReducedMotion || error 
      ? `linear-gradient(135deg, ${colors?.primary || BRAND_COLORS.primary}20, ${colors?.secondary || BRAND_COLORS.secondary}10)`
      : undefined,
    // Apply subtle opacity and blur effects
    ...getBackgroundStyling(),
  };

  return (
    <div
      ref={containerRef}
      className={`
        relative w-full h-full
        ${!isLoaded ? 'opacity-0' : 'opacity-100'}
        ${opacityTransitions ? 'transition-opacity duration-500 ease-in-out' : ''}
        ${className}
      `}
      style={fallbackStyle}
      data-testid="animated-background"
      aria-hidden="true" // Animation is decorative
    >
      {/* Loading state */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-pulse text-brand-primary/50">
            <div className="w-8 h-8 border-2 border-current border-t-transparent rounded-full animate-spin" />
          </div>
        </div>
      )}

      {/* Error state */}
      {error && import.meta.env.DEV && (
        <div className="absolute top-2 right-2 bg-red-100 text-red-800 px-2 py-1 rounded text-xs">
          Animation Error: {error}
        </div>
      )}

      {/* Reduced motion notice (development only) */}
      {respectReducedMotion && prefersReducedMotion && import.meta.env.DEV && (
        <div className="absolute bottom-2 right-2 bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
          Reduced Motion: Animation disabled
        </div>
      )}

      {/* Content overlay with T4.3 overlay handling */}
      {children && (
        <div 
          className={`w-full h-full ${generateOverlayClasses(overlayMode, overlayStyle, overlayPadding)}`}
          style={{
            background: generateOverlayBackground(overlayMode, overlayStyle, overlayColor, overlayOpacity),
            backdropFilter: getOverlayBackdropFilter(overlayMode, overlayStyle),
            WebkitBackdropFilter: getOverlayBackdropFilter(overlayMode, overlayStyle),
          }}
        >
          <div className={getTextContrastClasses(overlayMode, textContrast, overlayOpacity)}>
            {children}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnimatedBackground;
