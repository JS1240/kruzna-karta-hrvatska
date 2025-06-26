/**
 * Brand color utilities for the new color scheme
 * Provides easy access to CSS custom properties and color conversions
 */

/**
 * Brand color definitions matching CSS custom properties
 */
export const BRAND_COLORS = {
  // Primary brand colors (for buttons, links, headers)
  primary: '#3674B5',
  secondary: '#578FCA',
  
  // Accent colors (for highlights and accents)
  accentCream: '#F5F0CD',
  accentGold: '#FADA7A',
  
  // Contrast colors (for text and high contrast)
  black: '#000000',
  white: '#FFFFFF'
} as const;

/**
 * CSS custom property names for the brand colors
 */
export const CSS_VARIABLES = {
  primary: '--brand-primary',
  secondary: '--brand-secondary',
  accentCream: '--brand-accent-cream',
  accentGold: '--brand-accent-gold',
  black: '--brand-black',
  white: '--brand-white',
  animationPrimary: '--animation-primary',
  animationSecondary: '--animation-secondary',
  animationBackground: '--animation-background'
} as const;

/**
 * Get CSS custom property value
 * @param propertyName - CSS custom property name (with or without --)
 * @returns CSS custom property value or null if not found
 */
export const getCSSVariable = (propertyName: string): string | null => {
  const propName = propertyName.startsWith('--') ? propertyName : `--${propertyName}`;
  return getComputedStyle(document.documentElement).getPropertyValue(propName).trim();
};

/**
 * Set CSS custom property value
 * @param propertyName - CSS custom property name (with or without --)
 * @param value - CSS value to set
 */
export const setCSSVariable = (propertyName: string, value: string): void => {
  const propName = propertyName.startsWith('--') ? propertyName : `--${propertyName}`;
  document.documentElement.style.setProperty(propName, value);
};

/**
 * Convert hex color to HSL values for CSS custom properties
 * @param hex - Hex color string (e.g., '#3674B5')
 * @returns HSL string suitable for CSS custom properties (e.g., '54 100% 35%')
 */
export const hexToHSL = (hex: string): string => {
  // Remove hash if present
  const cleanHex = hex.replace('#', '');
  
  // Parse RGB values
  const r = parseInt(cleanHex.substr(0, 2), 16) / 255;
  const g = parseInt(cleanHex.substr(2, 2), 16) / 255;
  const b = parseInt(cleanHex.substr(4, 2), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }

  // Convert to degrees and percentages, round to nearest integer
  const hDeg = Math.round(h * 360);
  const sPercent = Math.round(s * 100);
  const lPercent = Math.round(l * 100);

  return `${hDeg} ${sPercent}% ${lPercent}%`;
};

/**
 * Convert hex color to RGB values
 * @param hex - Hex color string (e.g., '#3674B5')
 * @returns RGB object with r, g, b values (0-255)
 */
export const hexToRGB = (hex: string): { r: number; g: number; b: number } => {
  const cleanHex = hex.replace('#', '');
  return {
    r: parseInt(cleanHex.substr(0, 2), 16),
    g: parseInt(cleanHex.substr(2, 2), 16),
    b: parseInt(cleanHex.substr(4, 2), 16)
  };
};

/**
 * Convert hex color to decimal for VANTA.js animations
 * @param hex - Hex color string (e.g., '#3674B5')
 * @returns Decimal color value for VANTA.js
 */
export const hexToDecimal = (hex: string): number => {
  const cleanHex = hex.replace('#', '');
  return parseInt(cleanHex, 16);
};

/**
 * WCAG 2.1 AA color contrast checker
 * @param color1 - First color in hex format
 * @param color2 - Second color in hex format
 * @returns Object with contrast ratio and compliance status
 */
export const checkColorContrast = (color1: string, color2: string): {
  ratio: number;
  isAACompliant: boolean;
  isAAACompliant: boolean;
} => {
  const getLuminance = (hex: string): number => {
    const rgb = hexToRGB(hex);
    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  const lum1 = getLuminance(color1);
  const lum2 = getLuminance(color2);
  const ratio = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);

  return {
    ratio: Math.round(ratio * 100) / 100,
    isAACompliant: ratio >= 4.5,
    isAAACompliant: ratio >= 7.0
  };
};

/**
 * Validate all brand color combinations for WCAG compliance
 * @returns Array of validation results
 */
export const validateBrandColorContrast = (): Array<{
  combination: string;
  ratio: number;
  isCompliant: boolean;
}> => {
  const validations = [];
  
  // Test text colors against background colors
  const textColors = [BRAND_COLORS.black, BRAND_COLORS.white];
  const backgroundColors = [
    BRAND_COLORS.primary,
    BRAND_COLORS.secondary,
    BRAND_COLORS.accentCream,
    BRAND_COLORS.accentGold,
    BRAND_COLORS.white
  ];

  textColors.forEach(textColor => {
    backgroundColors.forEach(bgColor => {
      if (textColor !== bgColor) {
        const result = checkColorContrast(textColor, bgColor);
        validations.push({
          combination: `${textColor} on ${bgColor}`,
          ratio: result.ratio,
          isCompliant: result.isAACompliant
        });
      }
    });
  });

  return validations;
};

/**
 * Generate Tailwind-compatible color configuration
 * @returns Object suitable for Tailwind CSS configuration
 */
export const generateTailwindColors = () => {
  return {
    'brand-primary': 'hsl(var(--brand-primary))',
    'brand-secondary': 'hsl(var(--brand-secondary))',
    'brand-accent-cream': 'hsl(var(--brand-accent-cream))',
    'brand-accent-gold': 'hsl(var(--brand-accent-gold))',
    'brand-black': 'hsl(var(--brand-black))',
    'brand-white': 'hsl(var(--brand-white))'
  };
};

/**
 * Tailwind CSS class mappings for brand colors
 */
export const TAILWIND_CLASSES = {
  // Background classes
  background: {
    primary: 'bg-brand-primary',
    secondary: 'bg-brand-secondary',
    accentCream: 'bg-brand-accent-cream',
    accentGold: 'bg-brand-accent-gold',
    black: 'bg-brand-black',
    white: 'bg-brand-white',
    primaryLight: 'bg-brand-primary-light',
    primaryDark: 'bg-brand-primary-dark',
    secondaryLight: 'bg-brand-secondary-light',
    secondaryDark: 'bg-brand-secondary-dark'
  },
  
  // Text classes
  text: {
    primary: 'text-brand-primary',
    secondary: 'text-brand-secondary',
    accentCream: 'text-brand-accent-cream',
    accentGold: 'text-brand-accent-gold',
    black: 'text-brand-black',
    white: 'text-brand-white',
    primaryLight: 'text-brand-primary-light',
    primaryDark: 'text-brand-primary-dark',
    secondaryLight: 'text-brand-secondary-light',
    secondaryDark: 'text-brand-secondary-dark'
  },
  
  // Border classes
  border: {
    primary: 'border-brand-primary',
    secondary: 'border-brand-secondary',
    accentCream: 'border-brand-accent-cream',
    accentGold: 'border-brand-accent-gold',
    black: 'border-brand-black',
    white: 'border-brand-white',
    primaryLight: 'border-brand-primary-light',
    primaryDark: 'border-brand-primary-dark',
    secondaryLight: 'border-brand-secondary-light',
    secondaryDark: 'border-brand-secondary-dark'
  },

  // Animation background classes
  animation: {
    background: 'bg-animation-background',
    primary: 'bg-animation-primary',
    secondary: 'bg-animation-secondary'
  },

  // Accent classes for highlights and special elements
  accent: {
    cream: 'bg-accent-cream',
    gold: 'bg-accent-gold',
    creamText: 'text-accent-cream',
    goldText: 'text-accent-gold',
    creamBorder: 'border-accent-cream',
    goldBorder: 'border-accent-gold'
  },

  // UI utility classes for highlights and focus states
  focus: {
    ring: 'focus:ring-focus-ring focus:ring-2 focus:ring-offset-2',
    outline: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring'
  },

  // Notification and badge accent classes
  notification: {
    accent: 'bg-notification-accent',
    highlight: 'bg-highlight-bg'
  }
} as const;

/**
 * Get appropriate text color class for a given background color
 * @param bgColor - Background color key from TAILWIND_CLASSES.background
 * @returns Appropriate text color class for good contrast
 */
export const getContrastTextClass = (bgColor: keyof typeof TAILWIND_CLASSES.background): string => {
  const darkBackgrounds = ['primary', 'primaryDark', 'black'];
  const lightBackgrounds = ['accentCream', 'accentGold', 'white', 'primaryLight', 'secondaryLight'];
  const mediumBackgrounds = ['secondary', 'secondaryDark']; // These need black text for better contrast
  
  if (darkBackgrounds.includes(bgColor)) {
    return TAILWIND_CLASSES.text.white;
  } else if (mediumBackgrounds.includes(bgColor)) {
    // Secondary blue (#578FCA) needs black text for WCAG AA compliance (contrast 7.12:1)
    return TAILWIND_CLASSES.text.black;
  } else if (lightBackgrounds.includes(bgColor)) {
    return TAILWIND_CLASSES.text.black;
  }
  
  // Default to black text for unknown backgrounds
  return TAILWIND_CLASSES.text.black;
};

/**
 * Generate a complete className string with background and appropriate text color
 * @param bgColor - Background color key
 * @param additionalClasses - Additional CSS classes to include
 * @returns Complete className string
 */
export const generateColorClasses = (
  bgColor: keyof typeof TAILWIND_CLASSES.background,
  additionalClasses: string = ''
): string => {
  const bgClass = TAILWIND_CLASSES.background[bgColor];
  const textClass = getContrastTextClass(bgColor);
  
  return [bgClass, textClass, additionalClasses].filter(Boolean).join(' ');
};
