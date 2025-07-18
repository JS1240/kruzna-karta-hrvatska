import React from 'react';
import { cn } from '@/lib/utils';

type LogoVariant = 'full' | 'compact' | 'icon';
type LogoSize = 'fluid' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface LogoProps {
  variant?: LogoVariant;
  size?: LogoSize;
  maxWidth?: string;
  minWidth?: string;
  className?: string;
  'aria-label'?: string;
  responsive?: boolean;
}

/**
 * Responsive Diidemo.hr logo component with accessibility and design system integration
 * 
 * Features:
 * - Multiple variants: full (with tagline), compact (no tagline), icon-only
 * - Responsive sizing with fluid scaling
 * - Accessibility compliant with ARIA labels and screen reader support
 * - Design system integration with theme colors and typography
 * - Mobile-first approach with proper touch targets
 */
export const Logo: React.FC<LogoProps> = ({
  variant = 'compact',
  size = 'fluid',
  maxWidth,
  minWidth,
  className,
  'aria-label': ariaLabel,
  responsive = true,
}) => {
  // Size classes for different sizing strategies
  const sizeClasses = {
    fluid: 'h-auto',
    xs: 'h-6',
    sm: 'h-8',
    md: 'h-12',
    lg: 'h-16',
    xl: 'h-20',
  };

  // Responsive width constraints
  const getResponsiveStyles = () => {
    if (!responsive) return {};
    
    const styles: React.CSSProperties = {};
    
    if (size === 'fluid') {
      // Fluid sizing with clamp for responsive behavior
      if (variant === 'full') {
        styles.width = 'clamp(200px, 40vw, 400px)';
        styles.maxWidth = maxWidth || '400px';
        styles.minWidth = minWidth || '200px';
      } else if (variant === 'compact') {
        styles.width = 'clamp(120px, 25vw, 240px)';
        styles.maxWidth = maxWidth || '240px';
        styles.minWidth = minWidth || '120px';
      } else {
        styles.width = 'clamp(32px, 8vw, 48px)';
        styles.maxWidth = maxWidth || '48px';
        styles.minWidth = minWidth || '32px';
      }
    } else {
      if (maxWidth) styles.maxWidth = maxWidth;
      if (minWidth) styles.minWidth = minWidth;
    }
    
    return styles;
  };

  // Generate appropriate aria-label
  const getAriaLabel = () => {
    if (ariaLabel) return ariaLabel;
    
    switch (variant) {
      case 'full':
        return 'Diidemo.hr logo - Because NoThInG t0 d0 is not an option';
      case 'compact':
        return 'Diidemo.hr logo';
      case 'icon':
        return 'Diidemo.hr icon';
      default:
        return 'Diidemo.hr logo';
    }
  };

  // Icon-only variant
  if (variant === 'icon') {
    return (
      <div 
        className={cn('inline-flex items-center justify-center', className)}
        style={getResponsiveStyles()}
      >
        <svg
          viewBox="0 0 100 100"
          className={cn('w-full', sizeClasses[size])}
          role="img"
          aria-label={getAriaLabel()}
          xmlns="http://www.w3.org/2000/svg"
        >
          <title>Diidemo.hr Icon</title>
          <desc>Circular icon with orange dot representing the Diidemo.hr brand</desc>
          
          {/* Brand circle background */}
          <circle 
            cx="50" 
            cy="50" 
            r="45" 
            fill="currentColor" 
            className="text-primary-500"
          />
          
          {/* Orange accent dot */}
          <circle 
            cx="50" 
            cy="50" 
            r="12" 
            fill="currentColor" 
            className="text-accent-500"
          />
          
          {/* Subtle letter D */}
          <path
            d="M35 30 L35 70 L50 70 A15 15 0 0 0 50 30 Z"
            fill="white"
            opacity="0.9"
          />
        </svg>
      </div>
    );
  }

  // Compact variant (no tagline)
  if (variant === 'compact') {
    return (
      <div 
        className={cn('inline-flex items-center', className)}
        style={getResponsiveStyles()}
      >
        <svg
          viewBox="0 0 300 80"
          className={cn('w-full', sizeClasses[size])}
          role="img"
          aria-label={getAriaLabel()}
          xmlns="http://www.w3.org/2000/svg"
        >
          <title>Diidemo.hr</title>
          <desc>Diidemo.hr logo with brand name and orange accent dot</desc>
          
          <defs>
            <style>
              {`.logo-text-compact { 
                font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; 
                font-weight: 700; 
                font-size: 32px; 
                fill: currentColor; 
                dominant-baseline: middle;
                text-anchor: start;
              }`}
            </style>
          </defs>
          
          {/* Main logo text */}
          <text x="10" y="40" className="logo-text-compact">
            Diidemo.hr
          </text>
          
          {/* Orange accent dot */}
          <circle 
            cx="240" 
            cy="32" 
            r="6" 
            fill="currentColor" 
            className="text-accent-500"
          />
        </svg>
      </div>
    );
  }

  // Full variant (with tagline)
  return (
    <div 
      className={cn('inline-flex flex-col items-start', className)}
      style={getResponsiveStyles()}
    >
      <svg
        viewBox="0 0 400 120"
        className={cn('w-full', sizeClasses[size])}
        role="img"
        aria-label={getAriaLabel()}
        xmlns="http://www.w3.org/2000/svg"
      >
        <title>Diidemo.hr</title>
        <desc>Diidemo.hr logo with brand name, tagline "Because NoThInG t0 d0 is not an option", and orange accent dot</desc>
        
        <defs>
          <style>
            {`.logo-text-main { 
              font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; 
              font-weight: 700; 
              font-size: 36px; 
              fill: currentColor; 
              dominant-baseline: middle;
              text-anchor: start;
            }
            .logo-text-tagline { 
              font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; 
              font-weight: 400; 
              font-size: 14px; 
              fill: currentColor; 
              dominant-baseline: middle;
              text-anchor: start;
            }`}
          </style>
        </defs>
        
        {/* Main logo text */}
        <text x="10" y="35" className="logo-text-main">
          Diidemo
        </text>
        <text x="190" y="35" className="logo-text-main">
          .hr
        </text>
        
        {/* Orange accent dot */}
        <circle 
          cx="270" 
          cy="28" 
          r="6" 
          fill="currentColor" 
          className="text-accent-500"
        />
        
        {/* Tagline */}
        <text x="10" y="70" className="logo-text-tagline text-primary-600">
          Because "NoThInG t0 d0" is not an option
        </text>
      </svg>
    </div>
  );
};