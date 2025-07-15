import React, { useEffect, useRef, useState } from 'react';
import { initializeAnimation, destroyAnimation, getAnimation, AnimationType } from '../utils/animationUtils';
import { BRAND_COLORS, validateBrandColorContrast } from '../utils/colorUtils';
import AnimatedBackground from '../components/AnimatedBackground';
import { globalPerformanceMonitor, type PerformanceMetrics } from '../utils/performanceMonitor';

/**
 * Animation Development Test Page
 * Provides a testing environment for animations during development
 * 
 * Features:
 * - Basic animation component testing
 * - Performance monitoring demos (T5.1)
 * - FPS tracking and visualization
 * - Automatic performance adjustment testing
 * - Memory usage monitoring
 */

interface AnimationTest {
  id: string;
  name: string;
  type: AnimationType;
  intensity: 'low' | 'medium' | 'high';
  description: string;
}

interface PerformanceTestState {
  [key: string]: {
    metrics: PerformanceMetrics | null;
    isMonitoring: boolean;
    history: PerformanceMetrics[];
  };
}

const animationTests: AnimationTest[] = [
  {
    id: 'animated-background-low',
    name: 'AnimatedBackground Component - Low',
    type: 'vanta-topology',
    intensity: 'low',
    description: 'New AnimatedBackground component with low performance settings'
  },
  {
    id: 'animated-background-medium',
    name: 'AnimatedBackground Component - Medium',
    type: 'vanta-topology',
    intensity: 'medium',
    description: 'New AnimatedBackground component with medium performance settings'
  },
  {
    id: 'animated-background-high',
    name: 'AnimatedBackground Component - High',
    type: 'vanta-topology',
    intensity: 'high',
    description: 'New AnimatedBackground component with high performance settings'
  },
  {
    id: 'vanta-topology-low',
    name: 'VANTA Topology - Low Intensity',
    type: 'vanta-topology',
    intensity: 'low',
    description: 'Minimal particles, wide spacing - good for mobile'
  },
  {
    id: 'vanta-topology-medium',
    name: 'VANTA Topology - Medium Intensity',
    type: 'vanta-topology',
    intensity: 'medium',
    description: 'Balanced settings for most devices'
  },
  {
    id: 'vanta-topology-high',
    name: 'VANTA Topology - High Intensity',
    type: 'vanta-topology',
    intensity: 'high',
    description: 'More particles, closer spacing - desktop only'
  }
];

export const AnimationTestPage: React.FC = () => {
  const [activeTest, setActiveTest] = useState<string | null>(null);
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [colorValidation, setColorValidation] = useState<any[]>([]);
  const animationRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  
  // T5.1: Performance monitoring state
  const [performanceTestState, setPerformanceTestState] = useState<PerformanceTestState>({});
  const [globalPerformanceMetrics, setGlobalPerformanceMetrics] = useState<any>(null);
  const [showPerformanceDemo, setShowPerformanceDemo] = useState(false);
  const performanceUpdateInterval = useRef<number | null>(null);

  useEffect(() => {
    // Run color validation on mount
    const validation = validateBrandColorContrast();
    setColorValidation(validation);
    
    // T5.1: Setup global performance monitoring update
    const updateGlobalMetrics = () => {
      const aggregated = globalPerformanceMonitor.getAggregatedMetrics();
      setGlobalPerformanceMetrics(aggregated);
    };
    
    // Update global metrics every second
    performanceUpdateInterval.current = window.setInterval(updateGlobalMetrics, 1000);
    
    return () => {
      if (performanceUpdateInterval.current) {
        clearInterval(performanceUpdateInterval.current);
      }
    };
  }, []);

  const startTest = async (test: AnimationTest) => {
    // Stop current test
    if (activeTest) {
      stopTest(activeTest);
    }

    const element = animationRefs.current[test.id];
    if (!element) return;

    try {
      const animation = await initializeAnimation(test.id, {
        type: test.type,
        element,
        intensity: test.intensity,
        respectReducedMotion: true,
        enablePerformanceMonitoring: true
      });

      if (animation) {
        setActiveTest(test.id);
        console.log(`Started animation test: ${test.name}`);
        
        // Monitor performance
        const monitor = setInterval(() => {
          const animationInstance = getAnimation(test.id);
          if (animationInstance && (performance as any).memory) {
            const memory = (performance as any).memory;
            setPerformanceData(prev => [...prev.slice(-9), {
              timestamp: Date.now(),
              testId: test.id,
              memoryUsed: Math.round(memory.usedJSHeapSize / 1024 / 1024),
              memoryTotal: Math.round(memory.totalJSHeapSize / 1024 / 1024)
            }]);
          }
        }, 1000);

        // Clean up monitor when test stops
        setTimeout(() => {
          clearInterval(monitor);
        }, 30000); // Stop monitoring after 30 seconds
      }
    } catch (error) {
      console.error(`Failed to start animation test: ${test.name}`, error);
    }
  };

  const stopTest = (testId: string) => {
    const success = destroyAnimation(testId);
    if (success) {
      setActiveTest(null);
      console.log(`Stopped animation test: ${testId}`);
    }
  };

  const stopAllTests = () => {
    animationTests.forEach(test => {
      destroyAnimation(test.id);
    });
    setActiveTest(null);
    setPerformanceData([]);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-brand-primary mb-4">
            Animation Development Test Environment
          </h1>
          <p className="text-brand-black/70">
            Test and preview animations in development mode. Monitor performance and validate color schemes.
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Animation Controls</h2>
          <div className="flex flex-wrap gap-4 mb-4">
            {animationTests.map(test => (
              <button
                key={test.id}
                onClick={() => startTest(test)}
                disabled={activeTest === test.id}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  activeTest === test.id
                    ? 'bg-blue-500 text-white cursor-not-allowed'
                    : 'bg-gray-200 text-brand-black hover:bg-gray-300'
                }`}
              >
                {activeTest === test.id ? 'Running...' : `Start ${test.name}`}
              </button>
            ))}
          </div>
          <button
            onClick={stopAllTests}
            className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
          >
            Stop All Tests
          </button>
        </div>

        {/* Animation Test Areas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {animationTests.map(test => (
            <div key={test.id} className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold">{test.name}</h3>
                <p className="text-sm text-gray-600">{test.description}</p>
                <div className="mt-2">
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                    activeTest === test.id
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {activeTest === test.id ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              <div
                ref={el => animationRefs.current[test.id] = el}
                className="h-64 bg-white relative"
                style={{ minHeight: '256px' }}
              >
                {activeTest !== test.id && (
                  <div className="absolute inset-0 flex items-center justify-center text-gray-400">
                    Click "Start" to test animation
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Performance Monitor */}
        {performanceData.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-xl font-semibold mb-4">Performance Monitor</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left">Test ID</th>
                    <th className="px-4 py-2 text-left">Memory Used (MB)</th>
                    <th className="px-4 py-2 text-left">Memory Total (MB)</th>
                    <th className="px-4 py-2 text-left">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {performanceData.slice(-5).map((data, index) => (
                    <tr key={index} className="border-t">
                      <td className="px-4 py-2 font-mono text-sm">{data.testId}</td>
                      <td className="px-4 py-2">{data.memoryUsed}</td>
                      <td className="px-4 py-2">{data.memoryTotal}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">
                        {new Date(data.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Color Scheme Validation */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Color Scheme Validation</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium mb-3">Brand Colors</h3>
              <div className="space-y-2">
                {Object.entries(BRAND_COLORS).map(([name, color]) => (
                  <div key={name} className="flex items-center space-x-3">
                    <div
                      className="w-8 h-8 rounded border border-gray-300"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-mono text-sm">{color}</span>
                    <span className="text-sm text-gray-600 capitalize">{name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-3">WCAG Compliance</h3>
              <div className="space-y-1 text-sm">
                {colorValidation.slice(0, 8).map((validation, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="truncate">{validation.combination.slice(0, 20)}...</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      validation.isCompliant
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {validation.ratio.toFixed(1)}:1
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* AnimatedBackground Component Demo */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">AnimatedBackground Component Demo</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Low Performance Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Low Performance</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  performance="low"
                  intensity={0.3}
                  opacity={0.2}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Low Performance</h4>
                      <p className="text-sm text-brand-black/70">Minimal particles</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Medium Performance Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Medium Performance</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  performance="medium"
                  intensity={0.5}
                  opacity={0.3}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Medium Performance</h4>
                      <p className="text-sm text-brand-black/70">Balanced settings</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* High Performance Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">High Performance</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  performance="high"
                  intensity={0.7}
                  opacity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">High Performance</h4>
                      <p className="text-sm text-brand-black/70">Maximum particles</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Custom Colors Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Custom Colors</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  performance="medium"
                  intensity={0.5}
                  opacity={0.3}
                  colors={{
                    primary: '#578FCA',
                    secondary: '#3674B5'
                  }}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-secondary">Custom Colors</h4>
                      <p className="text-sm text-brand-black/70">Swapped primary/secondary</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Disabled Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Disabled Animation</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  enabled={false}
                  performance="medium"
                  intensity={0.5}
                  opacity={0.3}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Disabled</h4>
                      <p className="text-sm text-brand-black/70">Fallback gradient</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Accessibility Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Accessibility Test</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  performance="low"
                  intensity={0.2}
                  opacity={0.1}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Accessibility</h4>
                      <p className="text-sm text-brand-black/70">Respects reduced motion</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

          </div>
          
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-brand-primary mb-2">Component Features:</h4>
            <ul className="text-sm text-brand-black/80 space-y-1">
              <li>• Automatic performance optimization based on device detection</li>
              <li>• Accessibility support with <code>prefers-reduced-motion</code></li>
              <li>• Graceful fallback to gradient backgrounds</li>
              <li>• Error handling and development debugging</li>
              <li>• Smooth loading transitions</li>
              <li>• Brand color integration</li>
            </ul>
          </div>
        </div>

        {/* Blue-Only Animation Demos (T3.2) */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Blue-Only Animation Mode (T3.2)</h2>
          <p className="text-sm text-brand-black/70 mb-6">
            Strictly using only blue tones (#3674B5, #578FCA) as specified in the PRD.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Blue-Only Light Intensity */}
            <div className="space-y-3">
              <h3 className="font-medium">Light Blue Intensity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="light"
                  performance="medium"
                  intensity={0.4}
                  opacity={0.25}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-secondary">Light Blue</h4>
                      <p className="text-sm text-brand-black/70">Subtle blue tones</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Blue-Only Medium Intensity */}
            <div className="space-y-3">
              <h3 className="font-medium">Medium Blue Intensity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="medium"
                  performance="medium"
                  intensity={0.5}
                  opacity={0.3}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Medium Blue</h4>
                      <p className="text-sm text-brand-black/70">Primary blue (#3674B5)</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Blue-Only Dark Intensity */}
            <div className="space-y-3">
              <h3 className="font-medium">Dark Blue Intensity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="dark"
                  performance="medium"
                  intensity={0.6}
                  opacity={0.35}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Dark Blue</h4>
                      <p className="text-sm text-brand-black/70">Deeper blue variant</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Blue-Only High Performance */}
            <div className="space-y-3">
              <h3 className="font-medium">Blue-Only High Performance</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="medium"
                  performance="high"
                  intensity={0.7}
                  opacity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">High Performance</h4>
                      <p className="text-sm text-brand-black/70">More particles</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Blue-Only Mobile Optimized */}
            <div className="space-y-3">
              <h3 className="font-medium">Blue-Only Mobile</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="medium"
                  performance="low"
                  intensity={0.3}
                  opacity={0.2}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Mobile Optimized</h4>
                      <p className="text-sm text-brand-black/70">Low resource usage</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Blue-Only Comparison (Regular vs Blue-Only) */}
            <div className="space-y-3">
              <h3 className="font-medium">Blue-Only vs Regular</h3>
              <div className="h-48 rounded-lg overflow-hidden border flex">
                <div className="w-1/2 relative">
                  <AnimatedBackground
                    blueOnly={false}
                    performance="medium"
                    intensity={0.5}
                    opacity={0.3}
                    respectReducedMotion={true}
                  >
                    <div className="h-full flex items-center justify-center">
                      <div className="bg-white/80 backdrop-blur-sm rounded-lg p-2 text-center">
                        <h5 className="text-xs font-bold text-brand-primary">Regular</h5>
                      </div>
                    </div>
                  </AnimatedBackground>
                </div>
                <div className="w-1/2 relative">
                  <AnimatedBackground
                    blueOnly={true}
                    blueIntensity="medium"
                    performance="medium"
                    intensity={0.5}
                    opacity={0.3}
                    respectReducedMotion={true}
                  >
                    <div className="h-full flex items-center justify-center">
                      <div className="bg-white/80 backdrop-blur-sm rounded-lg p-2 text-center">
                        <h5 className="text-xs font-bold text-brand-primary">Blue-Only</h5>
                      </div>
                    </div>
                  </AnimatedBackground>
                </div>
              </div>
            </div>

          </div>
          
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-brand-primary mb-2">Blue-Only Features (T3.2):</h4>
            <ul className="text-sm text-brand-black/80 space-y-1">
              <li>• <strong>Strict Blue-Only Color Palette:</strong> Uses only #3674B5 and #578FCA</li>
              <li>• <strong>Three Blue Intensities:</strong> Light, Medium (default), and Dark variants</li>
              <li>• <strong>Performance Optimized:</strong> Same performance modes as regular animation</li>
              <li>• <strong>Brand Compliance:</strong> Strictly follows PRD color specifications</li>
              <li>• <strong>Accessibility:</strong> Maintains reduced motion and fallback support</li>
              <li>• <strong>Visual Consistency:</strong> Ensures cohesive blue theme throughout animation</li>
            </ul>
          </div>
        </div>

        {/* Gentle Movement Animation Demos (T3.3) */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Gentle Movement Animation Mode (T3.3)</h2>
          <p className="text-sm text-brand-black/70 mb-6">
            Slow, gentle movements with minimal particle density for subtle visual effects.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Gentle Normal Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Gentle Normal Mode</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  gentleMode="normal"
                  movementSpeed={0.3}
                  performance="medium"
                  intensity={0.4}
                  opacity={0.25}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Gentle Normal</h4>
                      <p className="text-sm text-brand-black/70">Slow & subtle</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Gentle Ultra Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Gentle Ultra Mode</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  gentleMode="ultra"
                  movementSpeed={0.2}
                  performance="medium"
                  intensity={0.3}
                  opacity={0.2}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Gentle Ultra</h4>
                      <p className="text-sm text-brand-black/70">Minimal particles</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Gentle with Slow Speed */}
            <div className="space-y-3">
              <h3 className="font-medium">Very Slow Movement</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  gentleMode="normal"
                  movementSpeed={0.1}
                  performance="medium"
                  intensity={0.4}
                  opacity={0.25}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Very Slow</h4>
                      <p className="text-sm text-brand-black/70">Speed: 0.1</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Gentle + Blue-Only Combined */}
            <div className="space-y-3">
              <h3 className="font-medium">Gentle + Blue-Only</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  blueOnly={true}
                  blueIntensity="light"
                  gentleMode="normal"
                  movementSpeed={0.3}
                  performance="medium"
                  intensity={0.3}
                  opacity={0.2}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-secondary">Combined Mode</h4>
                      <p className="text-sm text-brand-black/70">Gentle + Light Blue</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Gentle Mobile Optimized */}
            <div className="space-y-3">
              <h3 className="font-medium">Gentle Mobile</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  gentleMode="ultra"
                  movementSpeed={0.2}
                  performance="low"
                  intensity={0.2}
                  opacity={0.15}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Mobile Ultra</h4>
                      <p className="text-sm text-brand-black/70">Minimum resources</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Comparison: Regular vs Gentle */}
            <div className="space-y-3">
              <h3 className="font-medium">Regular vs Gentle</h3>
              <div className="h-48 rounded-lg overflow-hidden border flex">
                <div className="w-1/2 relative">
                  <AnimatedBackground
                    gentleMovement={false}
                    performance="medium"
                    intensity={0.5}
                    opacity={0.3}
                    respectReducedMotion={true}
                  >
                    <div className="h-full flex items-center justify-center">
                      <div className="bg-white/80 backdrop-blur-sm rounded-lg p-2 text-center">
                        <h5 className="text-xs font-bold text-brand-primary">Regular</h5>
                      </div>
                    </div>
                  </AnimatedBackground>
                </div>
                <div className="w-1/2 relative">
                  <AnimatedBackground
                    gentleMovement={true}
                    gentleMode="normal"
                    movementSpeed={0.3}
                    performance="medium"
                    intensity={0.3}
                    opacity={0.2}
                    respectReducedMotion={true}
                  >
                    <div className="h-full flex items-center justify-center">
                      <div className="bg-white/80 backdrop-blur-sm rounded-lg p-2 text-center">
                        <h5 className="text-xs font-bold text-brand-primary">Gentle</h5>
                      </div>
                    </div>
                  </AnimatedBackground>
                </div>
              </div>
            </div>

          </div>
          
          <div className="mt-4 p-4 bg-green-50 rounded-lg">
            <h4 className="font-medium text-brand-primary mb-2">Gentle Movement Features (T3.3):</h4>
            <ul className="text-sm text-brand-black/80 space-y-1">
              <li>• <strong>Minimal Particle Density:</strong> Uses 2-6 particles (vs 8-15 in regular mode)</li>
              <li>• <strong>Slow Movement Speed:</strong> Configurable 0.1-0.5 speed (default: 0.3)</li>
              <li>• <strong>Two Gentle Modes:</strong> Normal (subtle) and Ultra (maximum subtlety)</li>
              <li>• <strong>Wider Spacing:</strong> 25-35px spacing for less visual density</li>
              <li>• <strong>Shorter Connections:</strong> 6-12px max distance for minimal visual impact</li>
              <li>• <strong>Reduced Intensity:</strong> Auto-scales intensity to 70% of input value</li>
              <li>• <strong>Light Blue Default:</strong> Uses lighter blue tones for enhanced subtlety</li>
              <li>• <strong>Mobile Optimized:</strong> Ultra-minimal settings for mobile devices</li>
            </ul>
          </div>
        </div>

        {/* Subtle Opacity & Transparency Effects (T3.4) */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Subtle Opacity & Transparency Effects (T3.4)</h2>
          <p className="text-sm text-brand-black/70 mb-6">
            Low opacity and transparency effects for maximum subtlety and layering.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Minimal Opacity Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Minimal Opacity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  subtleOpacity={true}
                  opacityMode="minimal"
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Minimal (0.05)</h4>
                      <p className="text-sm text-brand-black/70">Barely visible</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Low Opacity Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Low Opacity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  subtleOpacity={true}
                  opacityMode="low"
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Low (0.15)</h4>
                      <p className="text-sm text-brand-black/70">Subtle background</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Medium Opacity Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Medium Opacity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  subtleOpacity={true}
                  opacityMode="medium"
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Medium (0.25)</h4>
                      <p className="text-sm text-brand-black/70">Balanced effect</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Adaptive Opacity Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Adaptive Opacity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  subtleOpacity={true}
                  opacityMode="adaptive"
                  performance="high"
                  intensity={0.6}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Adaptive</h4>
                      <p className="text-sm text-brand-black/70">Context-aware</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Background Blur Effect */}
            <div className="space-y-3">
              <h3 className="font-medium">With Background Blur</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  subtleOpacity={true}
                  opacityMode="low"
                  backgroundBlur={8}
                  performance="medium"
                  intensity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Blur (8px)</h4>
                      <p className="text-sm text-brand-black/70">Layered effect</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Gentle + Subtle Combined */}
            <div className="space-y-3">
              <h3 className="font-medium">Gentle + Subtle</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  gentleMode="ultra"
                  subtleOpacity={true}
                  opacityMode="adaptive"
                  movementSpeed={0.2}
                  backgroundBlur={4}
                  performance="low"
                  intensity={0.3}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/85 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Ultra Subtle</h4>
                      <p className="text-sm text-brand-black/70">Maximum subtlety</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Opacity Transitions Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Opacity Transitions</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  subtleOpacity={true}
                  opacityMode="medium"
                  opacityTransitions={true}
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Smooth Transitions</h4>
                      <p className="text-sm text-brand-black/70">Fade effects</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Blue-Only + Subtle Combined */}
            <div className="space-y-3">
              <h3 className="font-medium">Blue + Subtle</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="light"
                  subtleOpacity={true}
                  opacityMode="low"
                  backgroundBlur={6}
                  performance="medium"
                  intensity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/85 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-secondary">Blue + Subtle</h4>
                      <p className="text-sm text-brand-black/70">Light blue, low opacity</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* All Features Combined */}
            <div className="space-y-3">
              <h3 className="font-medium">All Features Combined</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="light"
                  gentleMovement={true}
                  gentleMode="normal"
                  movementSpeed={0.25}
                  subtleOpacity={true}
                  opacityMode="adaptive"
                  backgroundBlur={5}
                  opacityTransitions={true}
                  performance="medium"
                  intensity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Complete</h4>
                      <p className="text-sm text-brand-black/70">All T3.1-T3.4</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

          </div>
          
          <div className="mt-4 p-4 bg-purple-50 rounded-lg">
            <h4 className="font-medium text-brand-primary mb-2">Subtle Opacity Features (T3.4):</h4>
            <ul className="text-sm text-brand-black/80 space-y-1">
              <li>• <strong>Four Opacity Modes:</strong> Minimal (0.05), Low (0.15), Medium (0.25), Adaptive (context-aware)</li>
              <li>• <strong>Background Blur Effects:</strong> 0-20px blur intensity for layered transparency</li>
              <li>• <strong>Opacity Transitions:</strong> Smooth fade-in/fade-out animations</li>
              <li>• <strong>Adaptive Calculations:</strong> Auto-adjusts based on performance, device, and gentle mode</li>
              <li>• <strong>Fallback Styling:</strong> Applies to both animation and fallback gradient backgrounds</li>
              <li>• <strong>Integration Ready:</strong> Combines with blue-only and gentle movement modes</li>
              <li>• <strong>Performance Aware:</strong> Lower opacity for high-particle modes, optimized for mobile</li>
              <li>• <strong>Accessibility Compliant:</strong> Respects reduced motion preferences</li>
            </ul>
          </div>
        </div>

        {/* Adjustable Blur Effects (T3.5) */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Adjustable Blur Effects (T3.5)</h2>
          <p className="text-sm text-brand-black/70 mb-6">
            Advanced blur effects with multiple types and adjustable intensity levels.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Background Blur Type */}
            <div className="space-y-3">
              <h3 className="font-medium">Background Blur</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="background"
                  blurIntensity="medium"
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Background Blur</h4>
                      <p className="text-sm text-brand-black/70">Standard backdrop filter</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Content Blur Type */}
            <div className="space-y-3">
              <h3 className="font-medium">Content Blur</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="content"
                  blurIntensity="light"
                  contentBlur={3}
                  performance="medium"
                  intensity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/85 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Content Aware</h4>
                      <p className="text-sm text-brand-black/70">Preserves readability</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Edge Blur Type */}
            <div className="space-y-3">
              <h3 className="font-medium">Edge Blur</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="edge"
                  blurIntensity="medium"
                  edgeBlur={8}
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Edge Feather</h4>
                      <p className="text-sm text-brand-black/70">Smooth transitions</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Dynamic Blur Type */}
            <div className="space-y-3">
              <h3 className="font-medium">Dynamic Blur</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="dynamic"
                  blurIntensity="medium"
                  performance="high"
                  intensity={0.7}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/85 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Dynamic</h4>
                      <p className="text-sm text-brand-black/70">Intensity-adaptive</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Light Blur Intensity */}
            <div className="space-y-3">
              <h3 className="font-medium">Light Intensity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="background"
                  blurIntensity="light"
                  performance="medium"
                  intensity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Light (3px)</h4>
                      <p className="text-sm text-brand-black/70">Subtle blur</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Heavy Blur Intensity */}
            <div className="space-y-3">
              <h3 className="font-medium">Heavy Intensity</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="background"
                  blurIntensity="heavy"
                  performance="medium"
                  intensity={0.3}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Heavy (15px)</h4>
                      <p className="text-sm text-brand-black/70">Dramatic effect</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Custom Blur Value */}
            <div className="space-y-3">
              <h3 className="font-medium">Custom Blur</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  adjustableBlur={true}
                  blurType="background"
                  blurIntensity="custom"
                  customBlurValue={12}
                  performance="medium"
                  intensity={0.5}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/85 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Custom (12px)</h4>
                      <p className="text-sm text-brand-black/70">User-defined</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Gentle + Adjustable Combined */}
            <div className="space-y-3">
              <h3 className="font-medium">Gentle + Adjustable</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  gentleMovement={true}
                  gentleMode="ultra"
                  adjustableBlur={true}
                  blurType="dynamic"
                  blurIntensity="light"
                  movementSpeed={0.2}
                  performance="low"
                  intensity={0.3}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Ultra Gentle Blur</h4>
                      <p className="text-sm text-brand-black/70">Maximum subtlety</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Complete T3.1-T3.5 Feature Demo */}
            <div className="space-y-3">
              <h3 className="font-medium">Complete Feature Set</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  blueOnly={true}
                  blueIntensity="light"
                  gentleMovement={true}
                  gentleMode="normal"
                  movementSpeed={0.25}
                  subtleOpacity={true}
                  opacityMode="adaptive"
                  adjustableBlur={true}
                  blurType="dynamic"
                  blurIntensity="medium"
                  contentBlur={4}
                  edgeBlur={6}
                  opacityTransitions={true}
                  performance="medium"
                  intensity={0.4}
                  respectReducedMotion={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 text-center">
                      <h4 className="font-bold text-brand-primary">Complete</h4>
                      <p className="text-sm text-brand-black/70">All T3.1-T3.5</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

          </div>
          
          <div className="mt-4 p-4 bg-emerald-50 rounded-lg">
            <h4 className="font-medium text-brand-primary mb-2">Adjustable Blur Features (T3.5):</h4>
            <ul className="text-sm text-brand-black/80 space-y-1">
              <li>• <strong>Four Blur Types:</strong> Background, Content-aware, Edge feathering, Dynamic intensity-adaptive</li>
              <li>• <strong>Four Intensity Levels:</strong> Light (3px), Medium (8px), Heavy (15px), Custom (user-defined)</li>
              <li>• <strong>Content Blur Control:</strong> 0-20px radius for text-preserving blur effects</li>
              <li>• <strong>Edge Blur Feathering:</strong> 0-15px smooth transition effects with drop shadows</li>
              <li>• <strong>Dynamic Blur Adaptation:</strong> Auto-adjusts blur based on animation intensity and gentle mode</li>
              <li>• <strong>Enhanced Transitions:</strong> Smooth blur transitions with CSS filter and backdrop-filter</li>
              <li>• <strong>Backwards Compatible:</strong> Falls back to T3.4 backgroundBlur when adjustableBlur is disabled</li>
              <li>• <strong>Performance Optimized:</strong> Uses efficient CSS filters and backdrop-filter for hardware acceleration</li>
            </ul>
          </div>
        </div>

        {/* T3.6: Responsive Behavior Demo */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4 text-brand-primary">T3.6: Responsive Behavior Demo</h2>
          <p className="text-brand-black/70 mb-6">
            Test responsive animation behavior that adapts to different screen sizes with optimized performance.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            
            {/* Responsive Auto Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Auto Responsive</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="auto"
                  intensity={0.6}
                  performance="medium"
                  blueOnly={true}
                  blueIntensity="medium"
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Auto</h4>
                      <p className="text-xs text-brand-black/70">Screen-Adaptive</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Custom Mobile Intensity */}
            <div className="space-y-3">
              <h3 className="font-medium">Custom Mobile</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="auto"
                  intensity={0.6}
                  mobileIntensity={0.2}
                  tabletIntensity={0.4}
                  desktopIntensity={0.6}
                  performance="medium"
                  gentleMovement={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Custom</h4>
                      <p className="text-xs text-brand-black/70">Per-Device</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Custom Breakpoints */}
            <div className="space-y-3">
              <h3 className="font-medium">Custom Breakpoints</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="auto"
                  responsiveBreakpoints={{
                    mobile: 600,
                    tablet: 900,
                    desktop: 1200,
                  }}
                  intensity={0.5}
                  performance="medium"
                  blueOnly={true}
                  subtleOpacity={true}
                  opacityMode="adaptive"
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Breakpoints</h4>
                      <p className="text-xs text-brand-black/70">600/900/1200</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Manual Mode */}
            <div className="space-y-3">
              <h3 className="font-medium">Manual Mode</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="manual"
                  intensity={0.7}
                  performance="high"
                  blueOnly={true}
                  blueIntensity="dark"
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Manual</h4>
                      <p className="text-xs text-brand-black/70">Fixed Settings</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Disabled Responsive */}
            <div className="space-y-3">
              <h3 className="font-medium">Disabled</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={false}
                  intensity={0.6}
                  performance="medium"
                  gentleMovement={true}
                  gentleMode="ultra"
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Disabled</h4>
                      <p className="text-xs text-brand-black/70">Static</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Performance Adaptive */}
            <div className="space-y-3">
              <h3 className="font-medium">Performance Adaptive</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="auto"
                  intensity={0.8}
                  performance="high"
                  adjustableBlur={true}
                  blurType="dynamic"
                  blurIntensity="medium"
                  subtleOpacity={true}
                  opacityMode="adaptive"
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Adaptive</h4>
                      <p className="text-xs text-brand-black/70">All Features</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Mobile-First */}
            <div className="space-y-3">
              <h3 className="font-medium">Mobile-First</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="auto"
                  mobileIntensity={0.4}
                  tabletIntensity={0.3}
                  desktopIntensity={0.2}
                  performance="low"
                  gentleMovement={true}
                  subtleOpacity={true}
                  opacityMode="minimal"
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Mobile-First</h4>
                      <p className="text-xs text-brand-black/70">Reverse Scale</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Complete Responsive */}
            <div className="space-y-3">
              <h3 className="font-medium">Complete Feature Set</h3>
              <div className="h-48 rounded-lg overflow-hidden border">
                <AnimatedBackground
                  responsive={true}
                  responsiveMode="auto"
                  mobileIntensity={0.2}
                  tabletIntensity={0.4}
                  desktopIntensity={0.6}
                  performance="medium"
                  blueOnly={true}
                  blueIntensity="light"
                  gentleMovement={true}
                  gentleMode="normal"
                  subtleOpacity={true}
                  opacityMode="adaptive"
                  adjustableBlur={true}
                  blurType="dynamic"
                  blurIntensity="medium"
                  opacityTransitions={true}
                >
                  <div className="h-full flex items-center justify-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-lg p-3 text-center">
                      <h4 className="font-bold text-brand-primary">Complete</h4>
                      <p className="text-xs text-brand-black/70">T3.1-T3.6</p>
                    </div>
                  </div>
                </AnimatedBackground>
              </div>
            </div>

            {/* Screen Size Debug */}
            <div className="space-y-3">
              <h3 className="font-medium">Debug Info</h3>
              <div className="h-48 rounded-lg overflow-hidden border bg-slate-50">
                <div className="h-full flex items-center justify-center">
                  <div className="bg-white rounded-lg p-4 text-center shadow-sm">
                    <h4 className="font-bold text-brand-primary mb-2">Current Screen</h4>
                    <p className="text-sm text-brand-black/70 mb-1">
                      Width: <span className="font-mono">{typeof window !== 'undefined' ? window.innerWidth : 0}px</span>
                    </p>
                    <p className="text-sm text-brand-black/70 mb-1">
                      Height: <span className="font-mono">{typeof window !== 'undefined' ? window.innerHeight : 0}px</span>
                    </p>
                    <p className="text-xs text-brand-black/50">
                      Breakpoint: <span className="font-mono">
                        {typeof window !== 'undefined' 
                          ? window.innerWidth < 768 ? 'Mobile' 
                          : window.innerWidth < 1024 ? 'Tablet' 
                          : 'Desktop'
                          : 'Unknown'
                        }
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </div>

          </div>
          
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-brand-primary mb-2">Responsive Behavior Features (T3.6):</h4>
            <ul className="text-sm text-brand-black/80 space-y-1">
              <li>• <strong>Screen Size Detection:</strong> Automatic mobile/tablet/desktop detection with window resize monitoring</li>
              <li>• <strong>Custom Breakpoints:</strong> Configurable responsive breakpoints (default: 768px/1024px/1280px)</li>
              <li>• <strong>Device-Specific Intensity:</strong> Custom intensity values for mobile, tablet, and desktop</li>
              <li>• <strong>Performance Scaling:</strong> Automatic performance degradation on smaller screens (high→medium→low)</li>
              <li>• <strong>Particle Optimization:</strong> Reduced particle count and increased spacing on mobile for better performance</li>
              <li>• <strong>Responsive Opacity:</strong> Adaptive opacity adjustments based on screen size and particle density</li>
              <li>• <strong>Dynamic Blur Adaptation:</strong> Responsive blur intensity calculations for optimal visual effect</li>
              <li>• <strong>Three Responsive Modes:</strong> Auto (responsive), Manual (custom), Disabled (static)</li>
            </ul>
          </div>
        </div>

        {/* T5.1: Performance Monitoring Demo */}
        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-brand-primary">Performance Monitoring Demo (T5.1)</h2>
            <button
              onClick={() => setShowPerformanceDemo(!showPerformanceDemo)}
              className="px-4 py-2 bg-brand-primary text-white rounded-lg hover:bg-brand-primary/90 transition-colors"
            >
              {showPerformanceDemo ? 'Hide' : 'Show'} Performance Demo
            </button>
          </div>
          
          {showPerformanceDemo && (
            <div className="space-y-6">
              {/* Global Performance Metrics */}
              <div className="bg-white p-4 rounded-lg border">
                <h3 className="font-semibold mb-3 text-brand-primary">Global Performance Metrics</h3>
                {globalPerformanceMetrics ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-3 rounded">
                      <div className="text-sm font-medium text-brand-primary">Total Animations</div>
                      <div className="text-2xl font-bold">{globalPerformanceMetrics.totalAnimations}</div>
                    </div>
                    <div className="bg-green-50 p-3 rounded">
                      <div className="text-sm font-medium text-brand-primary">Average FPS</div>
                      <div className="text-2xl font-bold">{globalPerformanceMetrics.averageFPS.toFixed(1)}</div>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded">
                      <div className="text-sm font-medium text-brand-primary">Lowest FPS</div>
                      <div className="text-2xl font-bold">{globalPerformanceMetrics.lowestFPS.toFixed(1)}</div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded">
                      <div className="text-sm font-medium text-brand-primary">Highest FPS</div>
                      <div className="text-2xl font-bold">{globalPerformanceMetrics.highestFPS.toFixed(1)}</div>
                    </div>
                  </div>
                ) : (
                  <p className="text-brand-black/70">No active performance monitoring</p>
                )}
              </div>
              
              {/* Performance Test Animations */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* FPS Monitoring Test */}
                <div className="space-y-3">
                  <h3 className="font-medium text-brand-primary">FPS Monitoring Test</h3>
                  <div className="h-64 rounded-lg overflow-hidden border">
                    <AnimatedBackground
                      id="fps-monitor-test"
                      performance="high"
                      intensity={0.8}
                      opacity={0.4}
                      enableFrameRateMonitoring={true}
                      showFPSOverlay={true}
                      autoPerformanceAdjustment={false}
                      onPerformanceChange={(mode, metrics) => {
                        console.log('Performance change:', mode, metrics);
                        setPerformanceTestState(prev => ({
                          ...prev,
                          'fps-monitor-test': {
                            metrics,
                            isMonitoring: true,
                            history: prev['fps-monitor-test']?.history ? [...prev['fps-monitor-test'].history.slice(-19), metrics] : [metrics]
                          }
                        }));
                      }}
                      onPerformanceUpdate={(metrics) => {
                        setPerformanceTestState(prev => ({
                          ...prev,
                          'fps-monitor-test': {
                            ...prev['fps-monitor-test'],
                            metrics,
                            isMonitoring: true
                          }
                        }));
                      }}
                    >
                      <div className="h-full flex items-center justify-center">
                        <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                          <h4 className="font-bold text-brand-primary mb-2">FPS Monitor Test</h4>
                          <p className="text-sm text-brand-black/70 mb-2">High intensity with live FPS overlay</p>
                          {performanceTestState['fps-monitor-test']?.metrics && (
                            <div className="text-xs space-y-1">
                              <div>FPS: {performanceTestState['fps-monitor-test'].metrics.currentFPS.toFixed(1)}</div>
                              <div>Mode: {performanceTestState['fps-monitor-test'].metrics.performanceMode}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </AnimatedBackground>
                  </div>
                </div>
                
                {/* Auto Performance Adjustment Test */}
                <div className="space-y-3">
                  <h3 className="font-medium text-brand-primary">Auto Performance Adjustment</h3>
                  <div className="h-64 rounded-lg overflow-hidden border">
                    <AnimatedBackground
                      id="auto-performance-test"
                      performance="high"
                      intensity={1.0}
                      opacity={0.5}
                      enableFrameRateMonitoring={true}
                      showFPSOverlay={true}
                      autoPerformanceAdjustment={true}
                      performanceThresholds={{
                        mediumThreshold: 45,
                        lowThreshold: 30,
                        criticalThreshold: 20
                      }}
                      onPerformanceChange={(mode, metrics) => {
                        console.log('Auto-adjustment triggered:', mode, metrics);
                      }}
                    >
                      <div className="h-full flex items-center justify-center">
                        <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                          <h4 className="font-bold text-brand-primary mb-2">Auto Adjustment</h4>
                          <p className="text-sm text-brand-black/70">Performance auto-adjusts when FPS drops</p>
                        </div>
                      </div>
                    </AnimatedBackground>
                  </div>
                </div>
                
                {/* Memory Usage Monitoring */}
                <div className="space-y-3">
                  <h3 className="font-medium text-brand-primary">Memory Usage Monitor</h3>
                  <div className="h-64 rounded-lg overflow-hidden border">
                    <AnimatedBackground
                      id="memory-monitor-test"
                      performance="high"
                      intensity={0.9}
                      opacity={0.4}
                      enableFrameRateMonitoring={true}
                      showFPSOverlay={true}
                      onHighMemoryUsage={(metrics) => {
                        console.warn('High memory usage detected:', metrics);
                      }}
                    >
                      <div className="h-full flex items-center justify-center">
                        <div className="bg-white/90 backdrop-blur-sm rounded-lg p-4 text-center">
                          <h4 className="font-bold text-brand-primary mb-2">Memory Monitor</h4>
                          <p className="text-sm text-brand-black/70">Tracks memory usage in real-time</p>
                        </div>
                      </div>
                    </AnimatedBackground>
                  </div>
                </div>
                
                {/* Performance Comparison */}
                <div className="space-y-3">
                  <h3 className="font-medium text-brand-primary">Performance Comparison</h3>
                  <div className="grid grid-cols-3 gap-2 h-64">
                    <div className="rounded border overflow-hidden">
                      <AnimatedBackground
                        id="comparison-low"
                        performance="low"
                        intensity={0.3}
                        opacity={0.2}
                        enableFrameRateMonitoring={true}
                        showFPSOverlay={true}
                      >
                        <div className="h-full flex items-center justify-center">
                          <div className="bg-white/90 backdrop-blur-sm rounded p-2 text-center">
                            <div className="text-xs font-bold text-brand-primary">Low</div>
                          </div>
                        </div>
                      </AnimatedBackground>
                    </div>
                    <div className="rounded border overflow-hidden">
                      <AnimatedBackground
                        id="comparison-medium"
                        performance="medium"
                        intensity={0.5}
                        opacity={0.3}
                        enableFrameRateMonitoring={true}
                        showFPSOverlay={true}
                      >
                        <div className="h-full flex items-center justify-center">
                          <div className="bg-white/90 backdrop-blur-sm rounded p-2 text-center">
                            <div className="text-xs font-bold text-brand-primary">Medium</div>
                          </div>
                        </div>
                      </AnimatedBackground>
                    </div>
                    <div className="rounded border overflow-hidden">
                      <AnimatedBackground
                        id="comparison-high"
                        performance="high"
                        intensity={0.8}
                        opacity={0.4}
                        enableFrameRateMonitoring={true}
                        showFPSOverlay={true}
                      >
                        <div className="h-full flex items-center justify-center">
                          <div className="bg-white/90 backdrop-blur-sm rounded p-2 text-center">
                            <div className="text-xs font-bold text-brand-primary">High</div>
                          </div>
                        </div>
                      </AnimatedBackground>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Performance Monitoring Features */}
              <div className="bg-white p-4 rounded-lg border">
                <h3 className="font-semibold mb-3 text-brand-primary">Performance Monitoring Features (T5.1)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-2 text-brand-primary">Real-time FPS Tracking</h4>
                    <ul className="text-sm text-brand-black/80 space-y-1">
                      <li>• RequestAnimationFrame-based FPS calculation</li>
                      <li>• Rolling average FPS over configurable time window</li>
                      <li>• Device-specific targets (60fps desktop, 30fps mobile)</li>
                      <li>• Performance threshold detection and warnings</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2 text-brand-primary">Automatic Optimization</h4>
                    <ul className="text-sm text-brand-black/80 space-y-1">
                      <li>• Performance mode auto-switching (high→medium→low→critical)</li>
                      <li>• Memory usage monitoring and warnings</li>
                      <li>• Frame drop detection and reporting</li>
                      <li>• Visibility change handling (pause/resume)</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2 text-brand-primary">Developer Tools</h4>
                    <ul className="text-sm text-brand-black/80 space-y-1">
                      <li>• Live FPS overlay with color-coded status</li>
                      <li>• Performance statistics and history</li>
                      <li>• Memory usage display (when available)</li>
                      <li>• Performance event callbacks for custom handling</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2 text-brand-primary">Integration</h4>
                    <ul className="text-sm text-brand-black/80 space-y-1">
                      <li>• Seamless integration with AnimatedBackground component</li>
                      <li>• VANTA.js topology animation monitoring</li>
                      <li>• Global performance manager for multiple animations</li>
                      <li>• Non-intrusive monitoring with minimal overhead</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Development Notes */}
        <div className="bg-blue-50 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 text-brand-primary">Development Notes</h2>
          <ul className="space-y-2 text-brand-primary/80">
            <li>• Animations respect <code>prefers-reduced-motion</code> settings</li>
            <li>• Performance monitoring shows memory usage in real-time</li>
            <li>• Frame rate monitoring with automatic performance optimization (T5.1)</li>
            <li>• Real-time FPS tracking with device-specific targets (60fps desktop, 30fps mobile)</li>
            <li>• Automatic performance mode switching when FPS drops below thresholds</li>
            <li>• Mobile devices automatically use lower intensity settings</li>
            <li>• All color combinations are validated for WCAG 2.1 AA compliance</li>
            <li>• Animations automatically resize when window size changes</li>
            <li>• Background animations pause when tab is hidden to save resources</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
