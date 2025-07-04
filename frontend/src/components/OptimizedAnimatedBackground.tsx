/**
 * Optimized Animated Background Component
 * 
 * Enhanced version of AnimatedBackground with bundle size optimization,
 * conditional loading, and mobile-aware performance management.
 */

import React, { useRef, useEffect, useState, lazy, Suspense } from 'react';
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
import {
  mobileOptimizationLoader,
  shouldEnableMobileOptimizations,
  getBasicMobileSettings,
  loadMobileOptimizations,
  type MobileOptimizationSettings
} from '@/utils/mobileOptimizationLoader';

// Lazy load fallback background component
const FallbackBackground = lazy(() => import('./FallbackBackground'));

export interface OptimizedAnimatedBackgroundProps {
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
  /** Performance mode: 'high' | 'medium' | 'low' | 'auto' */
  performance?: 'high' | 'medium' | 'low' | 'auto';
  /** Enable reduced motion compliance */
  respectReducedMotion?: boolean;
  /** Use blue-only color scheme */
  blueOnly?: boolean;
  /** Blue intensity for blue-only mode */
  blueIntensity?: 'light' | 'medium' | 'dark';
  /** Enable gentle movement mode */
  gentleMovement?: boolean;
  /** Gentle movement mode */
  gentleMode?: 'normal' | 'ultra';
  /** Movement speed for gentle mode */
  movementSpeed?: number;
  /** Enable subtle transparency effects */
  subtleOpacity?: boolean;
  /** Opacity mode */
  opacityMode?: 'minimal' | 'low' | 'medium' | 'adaptive';
  /** Background blur intensity */
  backgroundBlur?: number;
  /** Enable fade-in/fade-out transitions */
  opacityTransitions?: boolean;
  /** Enable adjustable blur effects */
  adjustableBlur?: boolean;
  /** Blur type */
  blurType?: 'background' | 'content' | 'edge' | 'dynamic';
  /** Blur intensity level */
  blurIntensity?: 'light' | 'medium' | 'heavy' | 'custom';
  /** Custom blur value */
  customBlurValue?: number;
  /** Content blur radius */
  contentBlur?: number;
  /** Edge blur feathering */
  edgeBlur?: number;
  /** Enable responsive behavior */
  responsive?: boolean;
  /** Responsive mode */
  responsiveMode?: 'auto' | 'manual' | 'disabled';
  /** Custom responsive breakpoints */
  responsiveBreakpoints?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  /** Mobile-specific intensity override */
  mobileIntensity?: number;
  /** Tablet-specific intensity override */
  tabletIntensity?: number;
  /** Desktop-specific intensity override */
  desktopIntensity?: number;
  /** Enable content overlay handling */
  overlayMode?: OverlayMode;
  /** Overlay style configuration */
  overlayStyle?: OverlayStyle;
  /** Text contrast settings */
  textContrast?: TextContrast;
  /** Enable mobile optimizations */
  enableMobileOptimizations?: boolean;
  /** Force mobile optimization mode */
  forceMobileMode?: boolean;
  /** Bundle size optimization mode */
  bundleOptimization?: 'minimal' | 'balanced' | 'full';
}

/**
 * Optimized Animated Background Component
 */
export const OptimizedAnimatedBackground: React.FC<OptimizedAnimatedBackgroundProps> = ({
  enabled = true,
  intensity = 0.5,
  opacity = 0.3,
  colors,
  className = '',
  children,
  id,
  performance = 'auto',
  respectReducedMotion = true,
  blueOnly = false,
  blueIntensity = 'medium',
  gentleMovement = false,
  gentleMode = 'normal',
  movementSpeed = 0.3,
  subtleOpacity = false,
  opacityMode = 'adaptive',
  backgroundBlur = 0,
  opacityTransitions = true,
  adjustableBlur = false,
  blurType = 'background',
  blurIntensity = 'light',
  customBlurValue = 10,
  contentBlur = 4,
  edgeBlur = 6,
  responsive = true,
  responsiveMode = 'auto',
  responsiveBreakpoints,
  mobileIntensity,
  tabletIntensity,
  desktopIntensity,
  overlayMode = 'smart',
  overlayStyle,
  textContrast,
  enableMobileOptimizations = true,
  forceMobileMode = false,
  bundleOptimization = 'balanced',
}) => {
  const vantaRef = useRef<HTMLDivElement>(null);
  const vantaEffect = useRef<any>(null);
  
  // State for optimization management
  const [isLoaded, setIsLoaded] = useState(false);
  const [isMobileOptimized, setIsMobileOptimized] = useState(false);
  const [useFallback, setUseFallback] = useState(false);
  const [mobileSettings, setMobileSettings] = useState<MobileOptimizationSettings | null>(null);
  const [loadedModules, setLoadedModules] = useState<any>({});
  const [optimizationLevel, setOptimizationLevel] = useState<'none' | 'basic' | 'advanced'>('none');
  
  // Performance and mobile detection
  const [deviceCapabilities, setDeviceCapabilities] = useState<any>(null);
  const [shouldOptimize, setShouldOptimize] = useState(false);
  
  /**
   * Determine if mobile optimizations should be used
   */
  useEffect(() => {
    const checkMobileOptimization = async () => {
      if (!enableMobileOptimizations && !forceMobileMode) {
        setOptimizationLevel('none');
        return;
      }
      
      // Check if mobile optimizations are needed
      const shouldUse = forceMobileMode || shouldEnableMobileOptimizations();
      setShouldOptimize(shouldUse);
      
      if (shouldUse) {
        // Start with basic settings (lightweight)
        const basicSettings = getBasicMobileSettings();
        setMobileSettings(basicSettings);
        setOptimizationLevel('basic');
        
        // Load advanced optimizations conditionally based on bundle optimization mode
        if (bundleOptimization === 'full' || (bundleOptimization === 'balanced' && performance !== 'low')) {
          try {
            const modules = await loadMobileOptimizations();
            setLoadedModules(modules);
            
            if (modules.mobileDetection) {
              const capabilities = await modules.mobileDetection.getMobileCapabilities();
              setDeviceCapabilities(capabilities);
              
              if (modules.connectionOptimization) {
                const optimizedSettings = modules.connectionOptimization.optimizeForConnection(basicSettings);
                setMobileSettings(optimizedSettings);
              }
              
              setOptimizationLevel('advanced');
            }
          } catch (error) {
            console.warn('Failed to load advanced mobile optimizations:', error);
            // Fallback to basic optimizations
            setOptimizationLevel('basic');
          }
        }
        
        setIsMobileOptimized(true);
      } else {
        setOptimizationLevel('none');
      }
      
      setIsLoaded(true);
    };
    
    checkMobileOptimization();
  }, [enableMobileOptimizations, forceMobileMode, bundleOptimization, performance]);
  
  /**
   * Get effective intensity based on mobile optimizations
   */
  const getEffectiveIntensity = (): number => {
    if (!isMobileOptimized || !mobileSettings) {
      return intensity;
    }
    
    // Apply mobile-specific intensity scaling
    const mobileIntensityScale = mobileSettings.maxParticleCount / 16; // Normalize to 0-1
    return Math.min(intensity, mobileIntensityScale);
  };
  
  /**
   * Get effective performance mode
   */
  const getEffectivePerformance = (): 'high' | 'medium' | 'low' => {
    if (performance !== 'auto') {
      return performance;
    }
    
    // Auto-detect performance mode based on mobile optimizations
    if (isMobileOptimized && mobileSettings) {
      if (mobileSettings.preferredFrameRate <= 20) return 'low';
      if (mobileSettings.preferredFrameRate <= 30) return 'medium';
      return 'high';
    }
    
    return 'medium'; // Default
  };
  
  /**
   * Check if should use fallback
   */
  const shouldUseFallback = (): boolean => {
    if (!isMobileOptimized) return false;
    
    // Use fallback for very low-end devices or extreme bundle optimization
    if (bundleOptimization === 'minimal') return true;
    
    if (mobileSettings && mobileSettings.maxParticleCount <= 4) return true;
    
    if (deviceCapabilities && deviceCapabilities.deviceClass === 'very-low-end') return true;
    
    return false;
  };
  
  /**
   * Initialize animation effect
   */
  useEffect(() => {
    if (!enabled || !isLoaded || !vantaRef.current) {
      return;
    }
    
    // Check if should use fallback
    if (shouldUseFallback()) {
      setUseFallback(true);
      return;
    }
    
    const initializeEffect = () => {
      try {
        const effectiveIntensity = getEffectiveIntensity();
        const effectivePerformance = getEffectivePerformance();
        
        // Clean up existing effect
        if (vantaEffect.current) {
          cleanupVantaEffect(vantaEffect.current);
        }
        
        // Configure VANTA options based on mobile optimizations
        const vantaOptions = {
          el: vantaRef.current,
          intensity: effectiveIntensity,
          opacity,
          performance: effectivePerformance,
          colors: colors || {
            primary: BRAND_COLORS.primary,
            secondary: BRAND_COLORS.secondary,
          },
          
          // Mobile-specific optimizations
          ...(isMobileOptimized && mobileSettings && {
            particleCount: mobileSettings.maxParticleCount,
            fps: mobileSettings.preferredFrameRate,
            textureSize: mobileSettings.maxTextureResolution,
            enableCPUThrottling: mobileSettings.enableCPUThrottling,
            enableGPUMemoryLimit: mobileSettings.enableGPUMemoryLimit,
          }),
          
          // Blue-only mode
          ...(blueOnly && {
            blueIntensity,
          }),
          
          // Gentle movement
          ...(gentleMovement && {
            gentleMode,
            movementSpeed,
          }),
          
          // Responsive settings
          ...(responsive && {
            responsiveMode,
            responsiveBreakpoints,
            mobileIntensity: mobileIntensity || effectiveIntensity * 0.7,
            tabletIntensity: tabletIntensity || effectiveIntensity * 0.85,
            desktopIntensity: desktopIntensity || effectiveIntensity,
          }),
          
          // Accessibility
          respectReducedMotion,
        };
        
        // Initialize appropriate VANTA effect
        if (blueOnly) {
          vantaEffect.current = initBlueOnlyTopology(vantaOptions);
        } else if (gentleMovement) {
          vantaEffect.current = initGentleTopology(vantaOptions);
        } else {
          vantaEffect.current = initVantaTopology(vantaOptions);
        }
        
        console.log(`Animation initialized with ${optimizationLevel} mobile optimization`);
        
      } catch (error) {
        console.error('Failed to initialize animation effect:', error);
        setUseFallback(true);
      }
    };
    
    // Small delay to ensure DOM is ready
    const timeoutId = setTimeout(initializeEffect, 100);
    
    return () => {
      clearTimeout(timeoutId);
      if (vantaEffect.current) {
        cleanupVantaEffect(vantaEffect.current);
        vantaEffect.current = null;
      }
    };
  }, [
    enabled,
    isLoaded,
    isMobileOptimized,
    mobileSettings,
    optimizationLevel,
    getEffectiveIntensity(),
    getEffectivePerformance(),
    opacity,
    colors,
    blueOnly,
    blueIntensity,
    gentleMovement,
    gentleMode,
    movementSpeed,
    respectReducedMotion,
    responsive,
    responsiveMode,
    mobileIntensity,
    tabletIntensity,
    desktopIntensity,
  ]);
  
  /**
   * Get overlay configuration
   */
  const getOverlayConfig = () => {
    if (!overlayMode || overlayMode === 'none') return null;
    
    return {
      background: generateOverlayBackground(overlayMode, overlayStyle),
      backdropFilter: getOverlayBackdropFilter(overlayMode, overlayStyle),
      textContrast: getTextContrastClasses(textContrast || 'auto'),
      classes: generateOverlayClasses(overlayMode, overlayStyle),
    };
  };
  
  const overlayConfig = getOverlayConfig();
  
  /**
   * Render loading state
   */
  if (!isLoaded) {
    return (
      <div
        className={`
          w-full h-full relative overflow-hidden
          bg-gradient-to-br from-blue-50 to-blue-100
          ${className}
        `}
        data-testid=\"optimized-animated-background-loading\"
      >
        <div className=\"absolute inset-0 flex items-center justify-center\">
          <div className=\"animate-pulse text-blue-600\">
            <div className=\"w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin\" />
          </div>
        </div>
        {children && (
          <div className=\"relative z-10 w-full h-full\">
            {children}
          </div>
        )}
      </div>
    );
  }
  
  /**
   * Render fallback mode
   */
  if (useFallback) {
    return (
      <Suspense fallback={
        <div className={`w-full h-full relative ${className}`}>
          <div className=\"absolute inset-0 bg-gradient-to-br from-blue-50 to-blue-100\" />
          {children && (
            <div className=\"relative z-10 w-full h-full\">
              {children}
            </div>
          )}
        </div>
      }>
        <FallbackBackground
          enabled={enabled}
          intensity={getEffectiveIntensity()}
          opacity={opacity}
          colors={colors}
          className={className}
        >
          {children}
        </FallbackBackground>
      </Suspense>
    );
  }
  
  /**
   * Render main animated background
   */
  return (
    <div
      className={`
        w-full h-full relative overflow-hidden
        ${className}
      `}
      data-testid=\"optimized-animated-background\"
      data-optimization-level={optimizationLevel}
      data-mobile-optimized={isMobileOptimized}
      data-bundle-optimization={bundleOptimization}
    >
      {/* VANTA Animation Container */}
      <div
        ref={vantaRef}
        className=\"absolute inset-0 w-full h-full\"
        style={{
          opacity: enabled ? 1 : 0,
          transition: opacityTransitions ? 'opacity 0.5s ease-in-out' : 'none',
        }}
      />
      
      {/* Overlay Layer */}
      {overlayConfig && (
        <div
          className={`
            absolute inset-0 w-full h-full pointer-events-none
            ${overlayConfig.classes}
          `}
          style={{
            background: overlayConfig.background,
            backdropFilter: overlayConfig.backdropFilter,
            WebkitBackdropFilter: overlayConfig.backdropFilter,
          }}
        />
      )}
      
      {/* Content Layer */}
      {children && (
        <div
          className={`
            relative z-10 w-full h-full
            ${overlayConfig?.textContrast || ''}
          `}
        >
          {children}
        </div>
      )}
      
      {/* Debug Info (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className=\"absolute bottom-2 right-2 bg-black/80 text-white px-2 py-1 rounded text-xs font-mono z-20\">
          <div>Optimization: {optimizationLevel}</div>
          <div>Mobile: {isMobileOptimized ? 'Yes' : 'No'}</div>
          <div>Bundle: {bundleOptimization}</div>
          {mobileSettings && (
            <>
              <div>Particles: {mobileSettings.maxParticleCount}</div>
              <div>FPS: {mobileSettings.preferredFrameRate}</div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default OptimizedAnimatedBackground;