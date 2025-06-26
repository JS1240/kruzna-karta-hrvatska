import p5 from 'p5';

/**
 * P5.js utility functions for animation setup and configuration
 */

export interface P5AnimationConfig {
  containerElement: HTMLElement;
  width?: number;
  height?: number;
  backgroundColor?: string;
  alpha?: number;
}

/**
 * Creates a new p5.js instance with basic configuration
 * @param config - Configuration options for the p5 instance
 * @returns p5 instance
 */
export const createP5Instance = (
  config: P5AnimationConfig,
  sketch: (p: p5) => void
): p5 => {
  return new p5(sketch, config.containerElement);
};

/**
 * Basic sketch template for animations
 * @param config - Animation configuration
 * @returns p5 sketch function
 */
export const createBasicSketch = (config: P5AnimationConfig) => {
  return (p: p5) => {
    p.setup = () => {
      const width = config.width || config.containerElement.clientWidth;
      const height = config.height || config.containerElement.clientHeight;
      p.createCanvas(width, height);
      
      if (config.backgroundColor) {
        p.background(config.backgroundColor);
      }
    };

    p.windowResized = () => {
      const width = config.width || config.containerElement.clientWidth;
      const height = config.height || config.containerElement.clientHeight;
      p.resizeCanvas(width, height);
    };
  };
};

/**
 * Cleanup function to safely remove p5 instances
 * @param p5Instance - The p5 instance to cleanup
 */
export const cleanupP5Instance = (p5Instance: p5 | null) => {
  if (p5Instance) {
    p5Instance.remove();
  }
};

/**
 * Performance monitoring utilities for p5 animations
 */
export const P5Performance = {
  /**
   * Monitor frame rate and log performance warnings
   * @param p - p5 instance
   * @param targetFPS - Target frame rate (default: 60)
   */
  monitorFrameRate: (p: p5, targetFPS: number = 60) => {
    const currentFPS = p.frameRate();
    if (currentFPS < targetFPS * 0.5) {
      console.warn(`Low frame rate detected: ${currentFPS.toFixed(1)} FPS (target: ${targetFPS})`);
    }
  },

  /**
   * Check if device is mobile for performance optimization
   * @returns boolean indicating if device is likely mobile
   */
  isMobileDevice: (): boolean => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  },

  /**
   * Get recommended performance settings based on device
   * @returns performance configuration object
   */
  getPerformanceSettings: () => {
    const isMobile = P5Performance.isMobileDevice();
    return {
      targetFPS: isMobile ? 30 : 60,
      particleCount: isMobile ? 50 : 100,
      animationIntensity: isMobile ? 0.5 : 1.0
    };
  }
};
