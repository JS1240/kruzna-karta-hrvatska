/**
 * Type declarations for VANTA.js library
 * Since VANTA doesn't have official TypeScript support, we define basic types
 */

declare module 'vanta/dist/vanta.topology.min' {
  interface VantaTopologyOptions {
    el: HTMLElement | string;
    THREE?: any;
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
  }

  interface VantaInstance {
    destroy(): void;
    resize(): void;
    setOptions(options: Partial<VantaTopologyOptions>): void;
  }

  const VANTA: {
    TOPOLOGY(options: VantaTopologyOptions): VantaInstance;
  };

  export default VANTA;
}

declare module 'vanta' {
  const VANTA: any;
  export default VANTA;
}
