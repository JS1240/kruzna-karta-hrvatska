/**
 * T4.3 Content Overlay Utilities
 * 
 * Provides standardized overlay handling with proper blur effects
 * for content over animated backgrounds.
 */

export type OverlayMode = 'none' | 'light' | 'medium' | 'heavy' | 'custom';
export type OverlayStyle = 'glass' | 'frosted' | 'solid' | 'gradient';
export type TextContrast = 'auto' | 'light' | 'dark' | 'high-contrast';

export interface OverlayConfig {
  mode: OverlayMode;
  style: OverlayStyle;
  color?: string;
  opacity?: number;
  textContrast: TextContrast;
  padding?: string;
}

/**
 * Default overlay configurations for common use cases
 */
export const OVERLAY_PRESETS: Record<string, OverlayConfig> = {
  heroSection: {
    mode: 'light',
    style: 'glass',
    textContrast: 'auto',
    padding: 'p-8',
  },
  contentCard: {
    mode: 'medium',
    style: 'frosted',
    textContrast: 'auto',
    padding: 'p-6',
  },
  callToAction: {
    mode: 'heavy',
    style: 'solid',
    textContrast: 'dark',
    padding: 'p-8',
  },
  transitionZone: {
    mode: 'light',
    style: 'gradient',
    textContrast: 'auto',
    padding: 'p-4',
  },
  navigationOverlay: {
    mode: 'medium',
    style: 'glass',
    textContrast: 'auto',
    padding: 'p-4',
  },
};

/**
 * Calculate overlay opacity based on mode and custom settings
 */
export const getOverlayOpacity = (mode: OverlayMode, customOpacity?: number): number => {
  if (customOpacity !== undefined) {
    return Math.max(0, Math.min(1, customOpacity));
  }

  switch (mode) {
    case 'light':
      return 0.1;
    case 'medium':
      return 0.2;
    case 'heavy':
      return 0.4;
    case 'custom':
      return customOpacity || 0.2;
    case 'none':
    default:
      return 0;
  }
};

/**
 * Generate overlay background based on style and mode
 */
export const generateOverlayBackground = (
  mode: OverlayMode,
  style: OverlayStyle,
  color?: string,
  customOpacity?: number
): string => {
  if (mode === 'none') return 'transparent';

  const opacity = getOverlayOpacity(mode, customOpacity);
  const baseColor = color || '#ffffff';

  // Parse hex color to RGB
  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 255, g: 255, b: 255 };
  };

  const rgb = hexToRgb(baseColor);

  switch (style) {
    case 'glass':
      return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
    case 'frosted':
      return `rgba(${Math.min(rgb.r + 8, 255)}, ${Math.min(rgb.g + 10, 255)}, ${Math.min(rgb.b + 12, 255)}, ${opacity + 0.1})`;
    case 'solid':
      return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${Math.min(opacity + 0.3, 0.9)})`;
    case 'gradient':
      return `linear-gradient(135deg, rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity}) 0%, rgba(${Math.min(rgb.r + 8, 255)}, ${Math.min(rgb.g + 10, 255)}, ${Math.min(rgb.b + 12, 255)}, ${opacity + 0.05}) 100%)`;
    default:
      return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
  }
};

/**
 * Get backdrop filter for overlay style
 */
export const getOverlayBackdropFilter = (mode: OverlayMode, style: OverlayStyle): string => {
  if (mode === 'none') return 'none';

  switch (style) {
    case 'glass':
      return 'blur(8px) saturate(180%)';
    case 'frosted':
      return 'blur(12px) saturate(200%) brightness(110%)';
    case 'solid':
      return 'blur(2px) saturate(120%)';
    case 'gradient':
      return 'blur(6px) saturate(160%) brightness(105%)';
    default:
      return 'blur(8px) saturate(180%)';
  }
};

/**
 * Get appropriate text contrast classes
 */
export const getTextContrastClasses = (
  mode: OverlayMode,
  textContrast: TextContrast,
  customOpacity?: number
): string => {
  if (mode === 'none') {
    switch (textContrast) {
      case 'light':
        return 'text-white drop-shadow-sm';
      case 'dark':
        return 'text-brand-black drop-shadow-sm';
      case 'high-contrast':
        return 'text-brand-black drop-shadow-lg font-medium';
      case 'auto':
      default:
        return 'text-brand-black drop-shadow-sm';
    }
  }

  // With overlay, adjust based on overlay opacity and style
  const opacity = getOverlayOpacity(mode, customOpacity);
  
  if (textContrast === 'high-contrast') {
    return 'text-brand-black font-medium drop-shadow-lg';
  }

  if (textContrast === 'light') {
    return 'text-white drop-shadow-lg';
  }

  if (textContrast === 'dark') {
    return 'text-brand-black drop-shadow-md';
  }

  // Auto mode - choose based on overlay opacity with smart shadows
  if (opacity > 0.3) {
    return 'text-brand-black drop-shadow-sm'; // Dark text on light overlay
  } else if (opacity > 0.1) {
    return 'text-brand-black drop-shadow-md'; // Dark text with stronger shadow for medium overlay
  } else {
    return 'text-white drop-shadow-lg'; // Light text with strong shadow for minimal overlay
  }
};

/**
 * Get animation-aware text shadow classes based on background animation intensity
 */
export const getAnimationAwareTextShadow = (
  animationIntensity: number = 0.5,
  textContrast: TextContrast = 'auto',
  backgroundType: 'light' | 'medium' | 'dark' = 'medium'
): string => {
  // Calculate shadow intensity based on animation intensity
  const shadowIntensity = Math.min(animationIntensity * 1.5, 1);
  
  // Base shadow classes by intensity
  const shadows = {
    minimal: 'drop-shadow-sm',
    light: 'drop-shadow-md', 
    medium: 'drop-shadow-lg',
    heavy: 'drop-shadow-xl'
  };
  
  // Select shadow intensity based on animation and background
  let shadowClass: string;
  if (shadowIntensity < 0.3) {
    shadowClass = shadows.minimal;
  } else if (shadowIntensity < 0.6) {
    shadowClass = shadows.light;
  } else if (shadowIntensity < 0.8) {
    shadowClass = shadows.medium;
  } else {
    shadowClass = shadows.heavy;
  }
  
  // Adjust for text contrast mode
  if (textContrast === 'high-contrast') {
    shadowClass = shadows.heavy; // Always use heavy shadow for high contrast
  } else if (textContrast === 'light' && backgroundType === 'dark') {
    shadowClass = shadows.heavy; // Light text on dark background needs strong shadow
  }
  
  return shadowClass;
};

/**
 * Get performance-aware text styling based on device capabilities
 */
export const getPerformanceAwareTextStyling = (
  isMobile: boolean = false,
  isLowPerformance: boolean = false
): string => {
  if (isLowPerformance) {
    // Minimal shadows for low-performance devices
    return 'drop-shadow-sm';
  } else if (isMobile) {
    // Medium shadows for mobile devices
    return 'drop-shadow-md';
  } else {
    // Full shadows for desktop
    return 'drop-shadow-lg';
  }
};

/**
 * Generate complete overlay classes
 */
export const generateOverlayClasses = (
  mode: OverlayMode,
  style: OverlayStyle,
  padding: string = 'p-8'
): string => {
  if (mode === 'none') return 'relative z-10';

  const baseClasses = 'relative z-10 rounded-lg';
  const shadowClasses = style === 'solid' ? 'shadow-lg' : 'shadow-md';
  const borderClasses = style === 'glass' ? 'border border-white/20' : '';
  
  return `${baseClasses} ${shadowClasses} ${borderClasses} ${padding}`.trim();
};

/**
 * Generate complete overlay styling object
 */
export const generateOverlayStyle = (config: OverlayConfig): React.CSSProperties => {
  return {
    background: generateOverlayBackground(config.mode, config.style, config.color, config.opacity),
    backdropFilter: getOverlayBackdropFilter(config.mode, config.style),
    WebkitBackdropFilter: getOverlayBackdropFilter(config.mode, config.style),
  };
};

/**
 * Get responsive overlay configuration
 * Reduces overlay intensity on mobile for better performance
 */
export const getResponsiveOverlayConfig = (
  baseConfig: OverlayConfig,
  isMobile: boolean = false
): OverlayConfig => {
  if (!isMobile) return baseConfig;

  // Reduce overlay intensity on mobile
  const mobileMode: OverlayMode = 
    baseConfig.mode === 'heavy' ? 'medium' :
    baseConfig.mode === 'medium' ? 'light' :
    baseConfig.mode;

  const mobileStyle: OverlayStyle =
    baseConfig.style === 'frosted' ? 'glass' : baseConfig.style;

  return {
    ...baseConfig,
    mode: mobileMode,
    style: mobileStyle,
    opacity: baseConfig.opacity ? baseConfig.opacity * 0.8 : undefined,
  };
};

/**
 * Validate overlay configuration
 */
export const validateOverlayConfig = (config: Partial<OverlayConfig>): string[] => {
  const errors: string[] = [];

  if (config.opacity !== undefined && (config.opacity < 0 || config.opacity > 1)) {
    errors.push('Overlay opacity must be between 0 and 1');
  }

  if (config.color && !/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(config.color)) {
    errors.push('Overlay color must be a valid hex color');
  }

  return errors;
};