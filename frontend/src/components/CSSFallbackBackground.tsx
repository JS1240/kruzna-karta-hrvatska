/**
 * CSS Fallback Background Component
 * 
 * Provides CSS-based animations when WebGL is not available,
 * with intelligent fallback selection based on browser capabilities
 */

import React, { useEffect, useState, useRef } from 'react';
import { getCurrentFallbackDecision, getRecommendedAnimationSettings } from '@/utils/fallbackManager';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { BRAND_COLORS } from '@/utils/colorUtils';

export interface CSSFallbackBackgroundProps {
  /** Background mode: 'animated' | 'static' */
  mode?: 'animated' | 'static';
  /** Animation style: 'particles' | 'gradient' | 'pattern' */
  style?: 'particles' | 'gradient' | 'pattern';
  /** Color theme: 'primary' | 'accent' | 'monochrome' | 'dark' */
  theme?: 'primary' | 'accent' | 'monochrome' | 'dark';
  /** Animation intensity (0-1) */
  intensity?: number;
  /** Background opacity (0-1) */
  opacity?: number;
  /** Enable debug mode */
  debug?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Children to render over the background */
  children?: React.ReactNode;
}

/**
 * CSS Fallback Background Component
 */
export const CSSFallbackBackground: React.FC<CSSFallbackBackgroundProps> = ({
  mode = 'animated',
  style = 'gradient',
  theme = 'primary',
  intensity = 0.5,
  opacity = 0.3,
  debug = false,
  className = '',
  children,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [particleCount, setParticleCount] = useState(0);
  const [animationSettings, setAnimationSettings] = useState<any>(null);
  const { prefersReducedMotion, canAnimate } = useReducedMotion();

  // Get fallback decision and settings
  useEffect(() => {
    const decision = getCurrentFallbackDecision();
    const settings = getRecommendedAnimationSettings();
    
    setAnimationSettings(settings);
    
    // Determine particle count based on capabilities
    if (style === 'particles' && mode === 'animated' && canAnimate) {
      const baseCount = Math.floor(settings.particleCount * intensity);
      const deviceModifier = window.innerWidth < 768 ? 0.5 : window.innerWidth < 1024 ? 0.8 : 1;
      setParticleCount(Math.max(10, Math.floor(baseCount * deviceModifier)));
    } else {
      setParticleCount(0);
    }

    if (debug) {
      console.log('CSS Fallback settings:', {
        decision,
        settings,
        particleCount: Math.floor(settings.particleCount * intensity),
        mode,
        style,
        canAnimate,
        prefersReducedMotion,
      });
    }
  }, [intensity, style, mode, canAnimate, debug]);

  // Generate particle elements
  const renderParticles = () => {
    if (particleCount === 0 || prefersReducedMotion) return null;

    return Array.from({ length: particleCount }, (_, index) => {
      const size = Math.random() < 0.3 ? 'small' : Math.random() < 0.7 ? 'medium' : 'large';
      const animationType = Math.floor(Math.random() * 5) + 1;
      const duration = 12 + Math.random() * 8; // 12-20 seconds
      const delay = Math.random() * 10; // 0-10 seconds
      
      // Random positioning
      const left = Math.random() * 100;
      const top = Math.random() * 100;
      
      return (
        <div
          key={`particle-${index}`}
          className={`fallback-particle fallback-particle--${size} fallback-particle--animation-${animationType}`}
          style={{
            left: `${left}%`,
            top: `${top}%`,
            '--particle-duration': `${duration}s`,
            '--particle-delay': `${delay}s`,
            backgroundColor: getParticleColor(index),
          } as React.CSSProperties}
        />
      );
    });
  };

  // Get particle color based on theme and index
  const getParticleColor = (index: number): string => {
    const colors = getThemeColors();
    return colors[index % colors.length];
  };

  // Get theme colors
  const getThemeColors = (): string[] => {
    switch (theme) {
      case 'primary':
        return [
          BRAND_COLORS.primary,
          BRAND_COLORS.secondary,
          `${BRAND_COLORS.primary}80`, // With opacity
          `${BRAND_COLORS.secondary}80`,
        ];
      case 'accent':
        return [
          BRAND_COLORS.accent1,
          BRAND_COLORS.accent2,
          `${BRAND_COLORS.accent1}80`,
          `${BRAND_COLORS.accent2}80`,
        ];
      case 'monochrome':
        return ['#666666', '#999999', '#CCCCCC', '#E0E0E0'];
      case 'dark':
        return ['#333333', '#555555', BRAND_COLORS.primary, BRAND_COLORS.secondary];
      default:
        return [BRAND_COLORS.primary, BRAND_COLORS.secondary];
    }
  };

  // Get CSS custom properties for the theme
  const getThemeCustomProperties = (): React.CSSProperties => {
    const colors = getThemeColors();
    return {
      '--pattern-color-1': colors[0],
      '--pattern-color-2': colors[1],
      '--pattern-color-3': colors[2] || colors[0],
      '--pattern-color-4': colors[3] || colors[1],
    } as React.CSSProperties;
  };

  // Determine background style classes
  const getBackgroundStyleClasses = (): string => {
    const baseClasses = ['fallback-animation-container', `fallback-theme--${theme}`];
    
    if (mode === 'static') {
      // Static patterns
      switch (style) {
        case 'particles':
          baseClasses.push('fallback-static-pattern', 'fallback-pattern--geometric-dots');
          break;
        case 'gradient':
          baseClasses.push('fallback-static-pattern', 'fallback-pattern--solid-gradient');
          break;
        case 'pattern':
          baseClasses.push('fallback-static-pattern', 'fallback-pattern--brand-waves');
          break;
      }
    } else {
      // Animated backgrounds
      switch (style) {
        case 'gradient':
          baseClasses.push('fallback-gradient-animation', 'fallback-gradient--flow');
          break;
        case 'pattern':
          baseClasses.push('fallback-gradient-animation', 'fallback-gradient--wave');
          break;
        // Particles are handled separately
      }
    }

    // Add motion state classes
    if (prefersReducedMotion) {
      baseClasses.push('fallback-animation--paused');
    }

    if (debug) {
      baseClasses.push('fallback-debug');
    }

    return baseClasses.join(' ');
  };

  // Get overlay background for gradient animations
  const getGradientBackground = (): string => {
    if (style !== 'gradient' && style !== 'pattern') return '';
    
    const colors = getThemeColors();
    
    if (mode === 'static') {
      // Static gradient
      return `linear-gradient(135deg, ${colors[0]}${Math.floor(opacity * 255).toString(16).padStart(2, '0')}, ${colors[1]}${Math.floor(opacity * 255).toString(16).padStart(2, '0')})`;
    } else {
      // Animated gradient
      const opacityHex = Math.floor(opacity * 255).toString(16).padStart(2, '0');
      return `
        linear-gradient(135deg, ${colors[0]}${opacityHex} 0%, transparent 30%),
        linear-gradient(225deg, ${colors[1]}${opacityHex} 0%, transparent 30%),
        radial-gradient(circle at 50% 50%, ${colors[0]}${opacityHex} 0%, transparent 50%)
      `;
    }
  };

  return (
    <div
      ref={containerRef}
      className={`${getBackgroundStyleClasses()} ${className}`}
      style={{
        ...getThemeCustomProperties(),
        opacity: opacity,
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Gradient/Pattern Background */}
      {(style === 'gradient' || style === 'pattern') && (
        <div
          className="fallback-animation-overlay"
          style={{
            background: getGradientBackground(),
            backgroundSize: mode === 'animated' ? '400% 400%' : '100% 100%',
          }}
        />
      )}

      {/* Particle Animation */}
      {style === 'particles' && mode === 'animated' && renderParticles()}

      {/* Static Pattern for Particle Mode */}
      {style === 'particles' && mode === 'static' && (
        <div
          className="fallback-static-pattern fallback-pattern--geometric-dots"
          style={{ opacity: opacity * 0.6 }}
        />
      )}

      {/* Debug Information */}
      {debug && (
        <div
          style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'monospace',
            zIndex: 1000,
            pointerEvents: 'none',
          }}
        >
          <div>Mode: {mode}</div>
          <div>Style: {style}</div>
          <div>Theme: {theme}</div>
          <div>Particles: {particleCount}</div>
          <div>Can Animate: {canAnimate ? 'Yes' : 'No'}</div>
          <div>Reduced Motion: {prefersReducedMotion ? 'Yes' : 'No'}</div>
          {animationSettings && (
            <>
              <div>Quality: {animationSettings.quality}</div>
              <div>Recommended Particles: {animationSettings.particleCount}</div>
            </>
          )}
        </div>
      )}

      {/* Children */}
      {children}
    </div>
  );
};

export default CSSFallbackBackground;