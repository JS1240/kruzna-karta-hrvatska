import VANTA from 'vanta/dist/vanta.topology.min';
import * as THREE from 'three';

/**
 * VANTA.js topology animation utilities
 * Provides configuration and management for animated backgrounds
 */

export interface VantaTopologyConfig {
  el: HTMLElement | string;
  mouseControls?: boolean;
  touchControls?: boolean;
  gyroControls?: boolean;
  minHeight?: number;
  minWidth?: number;
  scale?: number;
  scaleMobile?: number;
  color?: number;
  backgroundColor?: number;
  points?: number;
  maxDistance?: number;
  spacing?: number;
  showDots?: boolean;
  forceAnimate?: boolean;
  speed?: number;
}

/**
 * Brand colors for the topology animation
 * Using only blue tones as specified in PRD
 */
export const BRAND_COLORS = {
  primary: 0x3674B5,     // #3674B5
  secondary: 0x578FCA,   // #578FCA
  background: 0xFFFFFF,  // White background
  accent1: 0xF5F0CD,     // Light cream
  accent2: 0xFADA7A,     // Gold
  black: 0x000000        // Black
};

/**
 * Blue-only color palette for topology animation (T3.2)
 * Strictly using only blue tones as specified in PRD
 */
export const BLUE_ONLY_COLORS = {
  primary: 0x3674B5,     // #3674B5 - Primary blue
  secondary: 0x578FCA,   // #578FCA - Secondary blue
  light: 0x7BA3D9,       // Lighter variant of secondary blue
  dark: 0x2A5A94,        // Darker variant of primary blue
  background: 0xFFFFFF,  // White background
  transparent: 0x3674B5  // Primary blue for transparent effects
};

/**
 * Default configuration for subtle topology animation
 * Optimized for performance and accessibility
 */
export const getDefaultTopologyConfig = (element: HTMLElement | string): VantaTopologyConfig => {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  return {
    el: element,
    mouseControls: true,
    touchControls: true,
    gyroControls: false,
    minHeight: 200.00,
    minWidth: 200.00,
    scale: 1.00,
    scaleMobile: 0.8,
    color: BRAND_COLORS.primary,     // Use primary blue color
    backgroundColor: BRAND_COLORS.background,
    points: isMobile ? 8 : 12,       // Reduced particle count for performance
    maxDistance: isMobile ? 15 : 20, // Shorter distances on mobile
    spacing: isMobile ? 18 : 15,     // Wider spacing on mobile for performance
    showDots: true,
    forceAnimate: false              // Allow reduced motion to work
  };
};

/**
 * Performance-optimized configuration for mobile devices
 */
export const getMobileTopologyConfig = (element: HTMLElement | string): VantaTopologyConfig => {
  return {
    ...getDefaultTopologyConfig(element),
    points: 6,           // Minimal particles for mobile
    maxDistance: 12,     // Very short connections
    spacing: 20,         // Wide spacing
    scaleMobile: 0.6,    // Smaller scale
    forceAnimate: false  // Respect reduced motion
  };
};

/**
 * Configuration for high-performance desktop displays
 */
export const getDesktopTopologyConfig = (element: HTMLElement | string): VantaTopologyConfig => {
  return {
    ...getDefaultTopologyConfig(element),
    points: 15,          // More particles for desktop
    maxDistance: 25,     // Longer connections
    spacing: 12,         // Tighter spacing
    scale: 1.2           // Slightly larger scale
  };
};

/**
 * VANTA topology animation manager
 */
export class VantaTopologyManager {
  private vantaInstance: any = null;
  private element: HTMLElement;
  private config: VantaTopologyConfig;

  constructor(element: HTMLElement, config?: Partial<VantaTopologyConfig>) {
    this.element = element;
    
    // Auto-detect device and apply appropriate config
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const baseConfig = isMobile ? getMobileTopologyConfig(element) : getDesktopTopologyConfig(element);
    
    this.config = { ...baseConfig, ...config };
  }

  /**
   * Initialize the VANTA topology animation
   */
  init(): void {
    try {
      // Check for reduced motion preference
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      
      if (prefersReducedMotion) {
        console.log('VANTA animation disabled due to user preference for reduced motion');
        return;
      }

      // Ensure THREE.js is available
      if (!THREE) {
        console.error('THREE.js is required for VANTA topology animations');
        return;
      }

      this.vantaInstance = VANTA.TOPOLOGY({
        ...this.config,
        THREE: THREE
      });

      console.log('VANTA topology animation initialized successfully');
    } catch (error) {
      console.error('Failed to initialize VANTA topology animation:', error);
    }
  }

  /**
   * Update animation configuration
   */
  updateConfig(newConfig: Partial<VantaTopologyConfig>): void {
    if (this.vantaInstance) {
      this.config = { ...this.config, ...newConfig };
      this.vantaInstance.setOptions(newConfig);
    }
  }

  /**
   * Destroy the animation instance
   */
  destroy(): void {
    if (this.vantaInstance) {
      this.vantaInstance.destroy();
      this.vantaInstance = null;
      console.log('VANTA topology animation destroyed');
    }
  }

  /**
   * Resize the animation when container changes
   */
  resize(): void {
    if (this.vantaInstance) {
      this.vantaInstance.resize();
    }
  }

  /**
   * Get current instance
   */
  getInstance(): any {
    return this.vantaInstance;
  }

  /**
   * Check if animation is running
   */
  isActive(): boolean {
    return this.vantaInstance !== null;
  }
}

/**
 * Utility function to create and manage VANTA topology animation
 * @param element - Target HTML element
 * @param config - Optional configuration overrides
 * @returns VantaTopologyManager instance
 */
export const createTopologyAnimation = (
  element: HTMLElement, 
  config?: Partial<VantaTopologyConfig>
): VantaTopologyManager => {
  return new VantaTopologyManager(element, config);
};

/**
 * Initialize VANTA topology animation with brand colors and performance settings
 */
export interface TopologyInitOptions {
  element: HTMLElement;
  colors?: {
    primary: string;
    secondary: string;
  };
  intensity?: number;
  opacity?: number;
  id?: string;
  maxDistance?: number;
  spacing?: number;
  points?: number;
  forceAnimate?: boolean;
  blueIntensity?: 'light' | 'medium' | 'dark';
}

/**
 * Initialize VANTA topology animation
 * @param options - Configuration options
 * @returns VANTA effect instance or null if failed
 */
export const initVantaTopology = async (options: TopologyInitOptions): Promise<any> => {
  try {
    const {
      element,
      colors,
      intensity = 0.5,
      opacity = 0.3,
      maxDistance = 20,
      spacing = 20,
      points = 10,
      forceAnimate = false,
    } = options;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion && !forceAnimate) {
      console.log('VANTA animation disabled due to user preference for reduced motion');
      return null;
    }

    // Ensure THREE.js is available
    if (!THREE) {
      console.error('THREE.js is required for VANTA topology animations');
      return null;
    }

    // Convert hex colors to numeric values for VANTA
    const hexToNumber = (hex: string): number => {
      return parseInt(hex.replace('#', ''), 16);
    };

    // Use provided colors or default to blue-only colors
    const primaryColor = colors?.primary || '#3674B5';
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    const config: VantaTopologyConfig = {
      el: element,
      mouseControls: true,
      touchControls: true,
      gyroControls: false,
      minHeight: 200.00,
      minWidth: 200.00,
      scale: isMobile ? 0.8 : 1.0,
      scaleMobile: 0.6,
      color: hexToNumber(primaryColor),
      backgroundColor: 0xFFFFFF,
      points: isMobile ? Math.max(6, Math.floor(points * 0.6)) : points,
      maxDistance: isMobile ? Math.max(12, Math.floor(maxDistance * 0.8)) : maxDistance,
      spacing: isMobile ? Math.max(18, Math.floor(spacing * 1.2)) : spacing,
      showDots: true,
      forceAnimate: forceAnimate
    };

    const vantaEffect = VANTA.TOPOLOGY({
      ...config,
      THREE: THREE
    });

    console.log('VANTA topology animation initialized successfully');
    return vantaEffect;
  } catch (error) {
    console.error('Failed to initialize VANTA topology animation:', error);
    return null;
  }
};

/**
 * Cleanup VANTA effect instance
 * @param effect - VANTA effect instance to cleanup
 */
export const cleanupVantaEffect = (effect: any): void => {
  try {
    if (effect && typeof effect.destroy === 'function') {
      effect.destroy();
      console.log('VANTA effect cleaned up successfully');
    }
  } catch (error) {
    console.error('Error cleaning up VANTA effect:', error);
  }
};

/**
 * Blue-only topology configuration
 * Uses only blue tones (#3674B5, #578FCA) as specified in T3.2
 */
export const getBlueOnlyTopologyConfig = (element: HTMLElement | string): VantaTopologyConfig => {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  return {
    el: element,
    mouseControls: true,
    touchControls: true,
    gyroControls: false,
    minHeight: 200.00,
    minWidth: 200.00,
    scale: 1.00,
    scaleMobile: 0.8,
    color: BLUE_ONLY_COLORS.primary,      // Primary blue (#3674B5)
    backgroundColor: BLUE_ONLY_COLORS.background,  // White background
    points: isMobile ? 8 : 12,            // Particle count optimized for performance
    maxDistance: isMobile ? 15 : 20,      // Connection distance
    spacing: isMobile ? 18 : 15,          // Spacing between particles
    showDots: true,                       // Show particle dots
    forceAnimate: false                   // Respect reduced motion
  };
};

/**
 * Initialize VANTA topology animation with strict blue-only configuration (T3.2)
 * Uses only blue tones (#3674B5, #578FCA) as specified in PRD
 * @param options - Configuration options for blue-only animation
 * @returns VANTA effect instance or null if failed
 */
export const initBlueOnlyTopology = async (options: TopologyInitOptions): Promise<any> => {
  try {
    const {
      element,
      intensity = 0.5,
      opacity = 0.3,
      maxDistance = 20,
      spacing = 20,
      points = 10,
      forceAnimate = false,
      blueIntensity = 'medium',
    } = options;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion && !forceAnimate) {
      console.log('VANTA blue-only animation disabled due to user preference for reduced motion');
      return null;
    }

    // Ensure THREE.js is available
    if (!THREE) {
      console.error('THREE.js is required for VANTA blue-only topology animations');
      return null;
    }

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    // Select blue tone based on intensity for blue-only mode
    const selectedBlueColor = {
      light: BLUE_ONLY_COLORS.light,      // Lighter blue variant
      medium: BLUE_ONLY_COLORS.primary,    // Primary blue (#3674B5)
      dark: BLUE_ONLY_COLORS.dark          // Darker blue variant
    }[blueIntensity];

    // Blue-only configuration - strictly using only blue tones
    const config: VantaTopologyConfig = {
      el: element,
      mouseControls: true,
      touchControls: true,
      gyroControls: false,
      minHeight: 200.00,
      minWidth: 200.00,
      scale: isMobile ? 0.8 : 1.0,
      scaleMobile: 0.6,
      color: selectedBlueColor,               // Selected blue tone based on intensity
      backgroundColor: BLUE_ONLY_COLORS.background,  // White background
      points: isMobile ? Math.max(6, Math.floor(points * 0.6)) : points,
      maxDistance: isMobile ? Math.max(12, Math.floor(maxDistance * 0.8)) : maxDistance,
      spacing: isMobile ? Math.max(18, Math.floor(spacing * 1.2)) : spacing,
      showDots: true,
      forceAnimate: forceAnimate
    };

    const vantaEffect = VANTA.TOPOLOGY({
      ...config,
      THREE: THREE
    });

    console.log('VANTA blue-only topology animation initialized successfully');
    console.log(`Animation mode: Blue-only (${blueIntensity} intensity)`);
    console.log('Animation colors: Primary Blue (#3674B5), Secondary Blue (#578FCA)');
    return vantaEffect;
  } catch (error) {
    console.error('Failed to initialize VANTA blue-only topology animation:', error);
    return null;
  }
};

/**
 * Enhanced topology configuration with multiple blue tone support
 * Provides different blue intensities for varied visual effects
 */
export const getEnhancedBlueTopologyConfig = (
  element: HTMLElement | string,
  blueIntensity: 'light' | 'medium' | 'dark' = 'medium'
): VantaTopologyConfig => {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  // Select blue tone based on intensity
  const blueColor = {
    light: BLUE_ONLY_COLORS.light,      // Lighter blue variant
    medium: BLUE_ONLY_COLORS.primary,    // Primary blue
    dark: BLUE_ONLY_COLORS.dark          // Darker blue variant
  }[blueIntensity];

  return {
    el: element,
    mouseControls: true,
    touchControls: true,
    gyroControls: false,
    minHeight: 200.00,
    minWidth: 200.00,
    scale: 1.00,
    scaleMobile: 0.8,
    color: blueColor,                     // Selected blue tone
    backgroundColor: BLUE_ONLY_COLORS.background,
    points: isMobile ? 8 : 12,
    maxDistance: isMobile ? 15 : 20,
    spacing: isMobile ? 18 : 15,
    showDots: true,
    forceAnimate: false
  };
};

/**
 * Gentle movement configuration with minimal particle density (T3.3)
 * Optimized for slow, subtle animations as specified in PRD
 */
export const getGentleMovementConfig = (element: HTMLElement | string): VantaTopologyConfig => {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  return {
    el: element,
    mouseControls: true,
    touchControls: true,
    gyroControls: false,
    minHeight: 200.00,
    minWidth: 200.00,
    scale: isMobile ? 0.7 : 0.9,      // Reduced scale for gentler effect
    scaleMobile: 0.5,                 // Even smaller on mobile
    color: BLUE_ONLY_COLORS.primary,
    backgroundColor: BLUE_ONLY_COLORS.background,
    points: isMobile ? 4 : 6,         // Minimal particle density
    maxDistance: isMobile ? 8 : 12,   // Shorter connections for subtlety
    spacing: isMobile ? 25 : 20,      // Wider spacing between particles
    showDots: true,
    forceAnimate: false,
    // Additional gentle movement parameters (if supported by VANTA)
    speed: 0.3,                       // Slow movement speed
    // Note: These parameters may need adjustment based on VANTA.TOPOLOGY capabilities
  };
};

/**
 * Ultra-gentle configuration for maximum subtlety
 */
export const getUltraGentleConfig = (element: HTMLElement | string): VantaTopologyConfig => {
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  return {
    el: element,
    mouseControls: false,             // Disabled for minimal interaction
    touchControls: false,             // Disabled for minimal interaction
    gyroControls: false,
    minHeight: 200.00,
    minWidth: 200.00,
    scale: isMobile ? 0.6 : 0.8,      // Very reduced scale
    scaleMobile: 0.4,
    color: BLUE_ONLY_COLORS.light,    // Lighter blue for subtlety
    backgroundColor: BLUE_ONLY_COLORS.background,
    points: isMobile ? 3 : 4,         // Ultra-minimal particles
    maxDistance: isMobile ? 6 : 8,    // Very short connections
    spacing: isMobile ? 30 : 25,      // Wide spacing for minimal density
    showDots: true,
    forceAnimate: false
  };
};

/**
 * Initialize VANTA topology animation with gentle movement settings (T3.3)
 * Implements slow, gentle movements with minimal particle density
 * @param options - Configuration options for gentle movement animation
 * @returns VANTA effect instance or null if failed
 */
export const initGentleTopology = async (options: TopologyInitOptions & { 
  gentleMode?: 'normal' | 'ultra';
  movementSpeed?: number;
}): Promise<any> => {
  try {
    const {
      element,
      intensity = 0.3,                // Lower default intensity for gentleness
      opacity = 0.2,                  // Lower default opacity for subtlety
      maxDistance = 10,               // Shorter connections
      spacing = 25,                   // Wider spacing for minimal density
      points = 5,                     // Minimal particle count
      forceAnimate = false,
      blueIntensity = 'light',        // Use lighter blue for gentleness
      gentleMode = 'normal',
      movementSpeed = 0.3,            // Slow movement speed
    } = options;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion && !forceAnimate) {
      console.log('VANTA gentle animation disabled due to user preference for reduced motion');
      return null;
    }

    // Ensure THREE.js is available
    if (!THREE) {
      console.error('THREE.js is required for VANTA gentle topology animations');
      return null;
    }

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    // Select blue tone based on intensity - prefer lighter tones for gentleness
    const selectedBlueColor = {
      light: BLUE_ONLY_COLORS.light,      // Lighter blue variant - preferred for gentle
      medium: BLUE_ONLY_COLORS.primary,    // Primary blue
      dark: BLUE_ONLY_COLORS.secondary     // Use secondary instead of dark for gentleness
    }[blueIntensity];

    // Gentle movement configuration parameters
    const gentleParams = gentleMode === 'ultra' ? {
      points: isMobile ? 2 : 3,
      maxDistance: isMobile ? 5 : 6,
      spacing: isMobile ? 35 : 30,
      scale: isMobile ? 0.5 : 0.7,
      scaleMobile: 0.3,
      mouseControls: false,
      touchControls: false,
    } : {
      points: isMobile ? Math.max(3, Math.floor(points * 0.5)) : Math.max(4, Math.floor(points * 0.7)),
      maxDistance: isMobile ? Math.max(6, Math.floor(maxDistance * 0.6)) : Math.max(8, Math.floor(maxDistance * 0.8)),
      spacing: isMobile ? Math.max(25, Math.floor(spacing * 1.3)) : Math.max(20, Math.floor(spacing * 1.2)),
      scale: isMobile ? 0.6 : 0.8,
      scaleMobile: 0.4,
      mouseControls: true,
      touchControls: true,
    };

    // Gentle movement configuration - optimized for slow, subtle animation
    const config: VantaTopologyConfig = {
      el: element,
      mouseControls: gentleParams.mouseControls,
      touchControls: gentleParams.touchControls,
      gyroControls: false,
      minHeight: 200.00,
      minWidth: 200.00,
      scale: gentleParams.scale,
      scaleMobile: gentleParams.scaleMobile,
      color: selectedBlueColor,
      backgroundColor: BLUE_ONLY_COLORS.background,
      points: gentleParams.points,
      maxDistance: gentleParams.maxDistance,
      spacing: gentleParams.spacing,
      showDots: true,
      forceAnimate: forceAnimate,
      speed: movementSpeed                 // Slow movement speed
    };

    const vantaEffect = VANTA.TOPOLOGY({
      ...config,
      THREE: THREE
    });

    console.log('VANTA gentle topology animation initialized successfully');
    console.log(`Gentle mode: ${gentleMode}, Movement speed: ${movementSpeed}, Particles: ${gentleParams.points}`);
    return vantaEffect;
  } catch (error) {
    console.error('Failed to initialize VANTA gentle topology animation:', error);
    return null;
  }
};
