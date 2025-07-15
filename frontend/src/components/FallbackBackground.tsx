import React, { useEffect, useRef, useState } from 'react';
import { BRAND_COLORS } from '@/utils/colorUtils';
import { 
  getDeviceCapabilities, 
  getFallbackRecommendation,
  type DeviceCapabilities,
  type FallbackRecommendation 
} from '@/utils/deviceDetection';
import {
  FallbackConfigGenerator,
  FallbackStylesInjector,
  fallbackAnimationManager,
  initializeFallbackAnimation,
  cleanupFallbackAnimation,
  type FallbackMode,
  type CSSAnimationType,
  type StaticPatternType
} from '@/utils/fallbackAnimations';
import '../styles/fallbackAnimations.css';

export interface FallbackBackgroundProps {
  /** Enable/disable the fallback animation */
  enabled?: boolean;
  /** Force specific fallback mode (overrides auto-detection) */
  fallbackMode?: FallbackMode;
  /** Force specific CSS animation type */
  cssAnimationType?: CSSAnimationType;
  /** Force specific static pattern type */
  staticPatternType?: StaticPatternType;
  /** Animation intensity (0-1, default: 0.5) */
  intensity?: number;
  /** Background opacity (0-1, default: 0.3) */
  opacity?: number;
  /** Custom colors override */
  colors?: {
    primary?: string;
    secondary?: string;
    accent1?: string;
    accent2?: string;
  };
  /** Additional CSS classes */
  className?: string;
  /** Children to render over the fallback background */
  children?: React.ReactNode;
  /** Unique identifier for the animation */
  id?: string;
  /** Enable smooth transitions between fallback modes */
  enableTransitions?: boolean;
  /** Show debug information in development */
  showDebugInfo?: boolean;
  /** User preferences */
  userPreferences?: {
    preferPerformance?: boolean;
    preferQuality?: boolean;
    reducedMotion?: boolean;
  };
  /** Callbacks */
  onFallbackModeChange?: (mode: FallbackMode, reason: string) => void;
  onDeviceCapabilitiesDetected?: (capabilities: DeviceCapabilities) => void;
}

/**
 * FallbackBackground Component (T5.2)
 * 
 * Provides CSS-based and static background alternatives for devices
 * that cannot handle WebGL animations efficiently.
 * 
 * Features:
 * - Automatic device capability detection
 * - Smart fallback mode selection
 * - CSS particle animations
 * - Gradient-based animations
 * - Static pattern backgrounds
 * - Performance optimization
 * - Accessibility compliance
 * 
 * @example
 * ```tsx
 * <FallbackBackground 
 *   intensity={0.6}
 *   opacity={0.4}
 *   enableTransitions={true}
 *   showDebugInfo={process.env.NODE_ENV === 'development'}
 *   onFallbackModeChange={(mode, reason) => console.log('Fallback mode:', mode, reason)}
 * >
 *   <div>Your content here</div>
 * </FallbackBackground>
 * ```
 */
export const FallbackBackground: React.FC<FallbackBackgroundProps> = ({
  enabled = true,
  fallbackMode,
  cssAnimationType,
  staticPatternType,
  intensity = 0.5,
  opacity = 0.3,
  colors,
  className = '',
  children,
  id,
  enableTransitions = true,
  showDebugInfo = false,
  userPreferences,
  onFallbackModeChange,
  onDeviceCapabilitiesDetected,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deviceCapabilities, setDeviceCapabilities] = useState<DeviceCapabilities | null>(null);
  const [recommendation, setRecommendation] = useState<FallbackRecommendation | null>(null);
  const [currentMode, setCurrentMode] = useState<FallbackMode>('none');
  
  // Animation ID for cleanup
  const animationId = id || 'fallback-background-default';
  
  // Check for reduced motion preference
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);
  
  // Device detection and fallback recommendation
  useEffect(() => {
    if (!enabled) {
      setIsLoaded(true);
      return;
    }
    
    const detectAndRecommend = async () => {
      try {
        // Detect device capabilities
        const capabilities = await getDeviceCapabilities();
        setDeviceCapabilities(capabilities);
        
        if (onDeviceCapabilitiesDetected) {
          onDeviceCapabilitiesDetected(capabilities);
        }
        
        // Get fallback recommendation
        const rec = await getFallbackRecommendation(capabilities, {
          ...userPreferences,
          reducedMotion: prefersReducedMotion
        });
        setRecommendation(rec);
        
        // Determine final fallback mode
        const finalMode = fallbackMode || rec.mode;
        setCurrentMode(finalMode);
        
        if (onFallbackModeChange) {
          onFallbackModeChange(finalMode, rec.reason);
        }
        
        console.log('Fallback recommendation:', rec);
        
      } catch (err) {
        console.error('Device detection error:', err);
        setError(err instanceof Error ? err.message : 'Device detection failed');
        
        // Fallback to safe mode
        setCurrentMode('static');
        setRecommendation({
          mode: 'static',
          cssAnimationType: 'minimal',
          staticPatternType: 'solid',
          enableTransitions: false,
          performanceSettings: {
            particleCount: 0,
            maxDistance: 0,
            spacing: 0,
            opacity: 0.1,
            updateFrequency: 0
          },
          reason: 'Device detection failed, using safe fallback'
        });
      } finally {
        setIsLoaded(true);
      }
    };
    
    detectAndRecommend();
  }, [enabled, fallbackMode, userPreferences, prefersReducedMotion, onFallbackModeChange, onDeviceCapabilitiesDetected]);
  
  // Initialize fallback animation
  useEffect(() => {
    if (!enabled || !isLoaded || !containerRef.current || !recommendation) {
      return;
    }
    
    const initializeAnimation = () => {
      try {
        // Clean up any existing animation
        cleanupFallbackAnimation(animationId);
        
        // Inject CSS styles if needed
        FallbackStylesInjector.injectStyles();
        
        // Override recommendation with props if provided
        const finalRecommendation: FallbackRecommendation = {
          ...recommendation,
          mode: fallbackMode || recommendation.mode,
          cssAnimationType: cssAnimationType || recommendation.cssAnimationType,
          staticPatternType: staticPatternType || recommendation.staticPatternType,
          enableTransitions: enableTransitions
        };
        
        // Apply intensity and opacity overrides
        if (intensity !== 0.5 || opacity !== 0.3) {
          finalRecommendation.performanceSettings = {
            ...finalRecommendation.performanceSettings,
            opacity: opacity,
            particleCount: Math.round(finalRecommendation.performanceSettings.particleCount * intensity)
          };
        }
        
        // Initialize the appropriate fallback animation
        initializeFallbackAnimation(
          containerRef.current!,
          finalRecommendation,
          colors,
          animationId
        );
        
        console.log(`Fallback animation initialized: ${finalRecommendation.mode} mode`);
        
      } catch (err) {
        console.error('Fallback animation initialization error:', err);
        setError(err instanceof Error ? err.message : 'Animation initialization failed');
      }
    };
    
    // Small delay to ensure DOM is ready
    const timeoutId = setTimeout(initializeAnimation, 50);
    
    return () => {
      clearTimeout(timeoutId);
      cleanupFallbackAnimation(animationId);
    };
  }, [enabled, isLoaded, recommendation, fallbackMode, cssAnimationType, staticPatternType, intensity, opacity, colors, enableTransitions, animationId]);
  
  // Generate CSS custom properties for theming
  const cssVariables = {
    '--pattern-color-1': colors?.primary || BRAND_COLORS.primary,
    '--pattern-color-2': colors?.secondary || BRAND_COLORS.secondary,
    '--pattern-color-3': colors?.accent1 || BRAND_COLORS.accent1,
    '--pattern-color-4': colors?.accent2 || BRAND_COLORS.accent2,
    '--particle-duration': `${Math.max(8, 20 - (intensity * 12))}s`,
    '--animation-duration': `${Math.max(10, 25 - (intensity * 15))}s`,
  } as React.CSSProperties;
  
  // Generate theme class based on colors
  const getThemeClass = () => {
    if (colors?.primary === BRAND_COLORS.accent1 || colors?.primary === BRAND_COLORS.accent2) {
      return 'fallback-theme--accent';
    }
    if (colors?.primary === '#000000' || colors?.primary === '#666666') {
      return 'fallback-theme--monochrome';
    }
    return 'fallback-theme--primary';
  };
  
  // Fallback background style for when animation is disabled
  const fallbackStyle: React.CSSProperties = {
    background: !enabled || prefersReducedMotion || error || currentMode === 'none'
      ? `linear-gradient(135deg, ${colors?.primary || BRAND_COLORS.primary}15, ${colors?.secondary || BRAND_COLORS.secondary}10)`
      : undefined,
    ...cssVariables
  };
  
  return (
    <div
      ref={containerRef}
      className={`
        fallback-animation-container
        ${getThemeClass()}
        ${!isLoaded ? 'opacity-0' : 'opacity-100'}
        ${enableTransitions ? 'fallback-transition--fade' : ''}
        ${showDebugInfo ? 'fallback-debug' : ''}
        ${className}
      `}
      style={fallbackStyle}
      data-testid="fallback-background"
      data-fallback-mode={currentMode}
      data-device-class={deviceCapabilities?.deviceClass}
      aria-hidden="true" // Animation is decorative
    >
      {/* Loading state */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-pulse" style={{ color: colors?.primary || BRAND_COLORS.primary }}>
            <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin opacity-50" />
          </div>
        </div>
      )}

      {/* Error state */}
      {error && import.meta.env.DEV && (
        <div className="absolute top-2 right-2 bg-red-100 text-red-800 px-2 py-1 rounded text-xs z-10">
          Fallback Error: {error}
        </div>
      )}

      {/* Reduced motion notice */}
      {prefersReducedMotion && import.meta.env.DEV && (
        <div className="absolute bottom-2 right-2 bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs z-10">
          Reduced Motion: Animations disabled
        </div>
      )}

      {/* Debug information */}
      {showDebugInfo && deviceCapabilities && recommendation && import.meta.env.DEV && (
        <div className="absolute top-2 left-2 bg-black/80 text-white px-3 py-2 rounded text-xs font-mono space-y-1 z-10">
          <div className="font-bold text-cyan-300">Fallback Debug Info</div>
          <div>Mode: {currentMode}</div>
          <div>Device: {deviceCapabilities.deviceClass}</div>
          <div>WebGL: {deviceCapabilities.webglSupport}</div>
          <div>Score: {deviceCapabilities.performanceScore}</div>
          <div>Particles: {recommendation.performanceSettings.particleCount}</div>
          <div>Opacity: {recommendation.performanceSettings.opacity.toFixed(2)}</div>
          <div>Reason: {recommendation.reason}</div>
          {deviceCapabilities.memoryEstimate && (
            <div>Memory: {Math.round(deviceCapabilities.memoryEstimate / 1024)}GB</div>
          )}
          {deviceCapabilities.batteryLevel && (
            <div>Battery: {Math.round(deviceCapabilities.batteryLevel * 100)}%</div>
          )}
        </div>
      )}

      {/* Animation overlay container */}
      <div className="fallback-animation-overlay">
        {/* Animation elements will be inserted here by the animation manager */}
      </div>

      {/* Content layer */}
      {children && (
        <div className="relative z-10 w-full h-full">
          {children}
        </div>
      )}
    </div>
  );
};

export default FallbackBackground;