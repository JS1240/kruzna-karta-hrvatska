/**
 * BrowserTester Component
 * 
 * Comprehensive browser compatibility testing interface for animations
 * across Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Download, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Monitor,
  Smartphone,
  Tablet
} from 'lucide-react';
import { 
  runCompatibilityTest, 
  generateCompatibilityReport, 
  testAnimationPerformance,
  type BrowserCompatibility 
} from '@/utils/browserCompatibility';
import AnimatedBackground from '@/components/AnimatedBackground';
import { TouchButton } from '@/components/mobile';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { cn } from '@/lib/utils';

export interface BrowserTesterProps {
  className?: string;
}

export interface AnimationTest {
  id: string;
  name: string;
  description: string;
  component: React.ComponentType<any>;
  props?: any;
  criticalFeatures: string[];
}

const animationTests: AnimationTest[] = [
  {
    id: 'vanta-topology',
    name: 'VANTA Topology Background',
    description: 'WebGL-based topology animation with particles',
    component: AnimatedBackground,
    props: {
      blueOnly: false,
      gentleMovement: false,
      subtleOpacity: false,
      adjustableBlur: false,
      responsive: true,
    },
    criticalFeatures: ['webgl', 'webgl-extensions', 'performance-api'],
  },
  {
    id: 'vanta-blue-gentle',
    name: 'Blue Gentle Mode',
    description: 'Brand-compliant blue-only gentle animation',
    component: AnimatedBackground,
    props: {
      blueOnly: true,
      blueIntensity: 'medium',
      gentleMovement: true,
      gentleMode: 'ultra',
      subtleOpacity: true,
      opacityMode: 'minimal',
      adjustableBlur: true,
      blurType: 'edge',
      responsive: true,
    },
    criticalFeatures: ['webgl', 'css-backdrop-filter', 'performance-api'],
  },
  {
    id: 'css-fallback',
    name: 'CSS Fallback Animation',
    description: 'Pure CSS animation fallback for low-performance devices',
    component: () => (
      <div className="w-full h-64 bg-gradient-to-br from-brand-primary/20 to-brand-secondary/20 animate-pulse rounded-lg" />
    ),
    props: {},
    criticalFeatures: ['css-animations', 'css-transitions'],
  },
  {
    id: 'reduced-motion',
    name: 'Reduced Motion Test',
    description: 'Test reduced motion preference handling',
    component: AnimatedBackground,
    props: {
      blueOnly: true,
      gentleMovement: true,
      gentleMode: 'ultra',
      subtleOpacity: true,
      opacityMode: 'static',
      responsive: true,
    },
    criticalFeatures: ['media-queries', 'prefers-reduced-motion'],
  },
];

/**
 * Browser Tester Component
 */
export const BrowserTester: React.FC<BrowserTesterProps> = ({
  className = '',
}) => {
  const [compatibility, setCompatibility] = useState<BrowserCompatibility | null>(null);
  const [selectedTest, setSelectedTest] = useState<string>(animationTests[0].id);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResults, setTestResults] = useState<{[key: string]: any}>({});
  const [performanceResults, setPerformanceResults] = useState<any>(null);
  const [testLog, setTestLog] = useState<string[]>([]);
  
  const testContainerRef = useRef<HTMLDivElement>(null);
  const { prefersReducedMotion } = useReducedMotion();

  // Run initial compatibility test
  useEffect(() => {
    const compat = runCompatibilityTest();
    setCompatibility(compat);
    addLog(`Browser detected: ${compat.browser.name} ${compat.browser.version}`);
    addLog(`Compatibility score: ${compat.score}/100`);
  }, []);

  const addLog = (message: string) => {
    setTestLog(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const runSingleTest = async (testId: string) => {
    const test = animationTests.find(t => t.id === testId);
    if (!test) return;

    addLog(`Starting test: ${test.name}`);
    setIsTestRunning(true);

    try {
      // Test performance
      const perfResults = await testAnimationPerformance();
      setPerformanceResults(perfResults);
      
      setTestResults(prev => ({
        ...prev,
        [testId]: {
          passed: perfResults.averageFPS > 30,
          fps: perfResults.averageFPS,
          frameDrops: perfResults.frameDrops,
          memoryUsage: perfResults.memoryUsage,
          timestamp: new Date().toISOString(),
        }
      }));

      addLog(`Test completed: ${perfResults.averageFPS.toFixed(1)} FPS, ${perfResults.frameDrops} frame drops`);
    } catch (error) {
      addLog(`Test failed: ${error}`);
      setTestResults(prev => ({
        ...prev,
        [testId]: {
          passed: false,
          error: String(error),
          timestamp: new Date().toISOString(),
        }
      }));
    } finally {
      setIsTestRunning(false);
    }
  };

  const runAllTests = async () => {
    addLog('Starting comprehensive test suite...');
    
    for (const test of animationTests) {
      setSelectedTest(test.id);
      await runSingleTest(test.id);
      // Wait between tests to avoid interference
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    addLog('All tests completed');
  };

  const exportResults = () => {
    const report = {
      timestamp: new Date().toISOString(),
      browser: compatibility?.browser,
      compatibility: compatibility,
      testResults: testResults,
      performanceResults: performanceResults,
      testLog: testLog,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `browser-test-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    addLog('Test results exported');
  };

  const generateTextReport = () => {
    if (!compatibility) return;
    
    const report = generateCompatibilityReport(compatibility);
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compatibility-report-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);

    addLog('Compatibility report exported');
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (score >= 50) return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };

  const currentTest = animationTests.find(t => t.id === selectedTest);
  const TestComponent = currentTest?.component;

  return (
    <div className={cn('max-w-6xl mx-auto p-6 space-y-6', className)}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Browser Animation Compatibility Tester
        </h1>
        <p className="text-gray-600">
          Test animations across Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
        </p>
      </div>

      {/* Browser Information */}
      {compatibility && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Browser Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Browser</div>
              <div className="font-semibold">{compatibility.browser.name} {compatibility.browser.version}</div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Engine</div>
              <div className="font-semibold">{compatibility.browser.engine}</div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Device Type</div>
              <div className="font-semibold flex items-center gap-1">
                {compatibility.browser.isMobile ? (
                  <>
                    <Smartphone className="h-4 w-4" />
                    Mobile
                  </>
                ) : (
                  <>
                    <Monitor className="h-4 w-4" />
                    Desktop
                  </>
                )}
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Compatibility Score</div>
              <div className={cn('font-semibold text-xl flex items-center gap-2', getScoreColor(compatibility.score))}>
                {getScoreIcon(compatibility.score)}
                {compatibility.score}/100
              </div>
            </div>
          </div>

          {/* Feature Support Summary */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-600">WebGL</div>
              <div className={cn('font-semibold', compatibility.features.webgl ? 'text-green-600' : 'text-red-600')}>
                {compatibility.features.webgl ? '✅ Supported' : '❌ Not Supported'}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-600">CSS Animations</div>
              <div className={cn('font-semibold', compatibility.features.css.animations ? 'text-green-600' : 'text-red-600')}>
                {compatibility.features.css.animations ? '✅ Supported' : '❌ Not Supported'}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-600">Reduced Motion</div>
              <div className={cn('font-semibold', compatibility.features.media.prefersReducedMotion ? 'text-green-600' : 'text-red-600')}>
                {compatibility.features.media.prefersReducedMotion ? '✅ Supported' : '❌ Not Supported'}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-600">Performance API</div>
              <div className={cn('font-semibold', compatibility.features.performance.performanceAPI ? 'text-green-600' : 'text-red-600')}>
                {compatibility.features.performance.performanceAPI ? '✅ Supported' : '❌ Not Supported'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Test Controls */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Animation Tests</h2>
        
        <div className="flex flex-wrap gap-4 mb-6">
          <TouchButton
            variant="primary"
            onClick={() => runSingleTest(selectedTest)}
            disabled={isTestRunning}
            loading={isTestRunning}
          >
            <Play className="h-4 w-4" />
            Run Selected Test
          </TouchButton>
          
          <TouchButton
            variant="secondary"
            onClick={runAllTests}
            disabled={isTestRunning}
          >
            <RotateCcw className="h-4 w-4" />
            Run All Tests
          </TouchButton>
          
          <TouchButton
            variant="ghost"
            onClick={exportResults}
            disabled={Object.keys(testResults).length === 0}
          >
            <Download className="h-4 w-4" />
            Export Results
          </TouchButton>
          
          <TouchButton
            variant="ghost"
            onClick={generateTextReport}
            disabled={!compatibility}
          >
            <Download className="h-4 w-4" />
            Export Report
          </TouchButton>
        </div>

        {/* Test Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {animationTests.map((test) => {
            const result = testResults[test.id];
            
            return (
              <button
                key={test.id}
                onClick={() => setSelectedTest(test.id)}
                className={cn(
                  'p-4 border-2 rounded-lg text-left transition-all hover:shadow-md',
                  selectedTest === test.id
                    ? 'border-brand-primary bg-brand-primary/5'
                    : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{test.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{test.description}</p>
                    
                    <div className="flex flex-wrap gap-1 mt-2">
                      {test.criticalFeatures.map((feature) => (
                        <span
                          key={feature}
                          className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {result && (
                    <div className="ml-4">
                      {result.passed ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                    </div>
                  )}
                </div>
                
                {result && (
                  <div className="mt-2 text-xs text-gray-500">
                    {result.fps && `${result.fps.toFixed(1)} FPS`}
                    {result.frameDrops !== undefined && `, ${result.frameDrops} drops`}
                    {result.error && `Error: ${result.error}`}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Test Area */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Test Area: {currentTest?.name}</h2>
        
        <div 
          ref={testContainerRef}
          className="relative w-full h-96 bg-gray-100 rounded-lg overflow-hidden"
        >
          {TestComponent && (
            <TestComponent {...currentTest?.props} />
          )}
          
          {isTestRunning && (
            <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
              <div className="bg-white rounded-lg p-4 shadow-xl">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-brand-primary"></div>
                  <span className="font-medium">Running performance test...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Performance Results */}
        {performanceResults && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Average FPS</div>
              <div className="font-semibold text-lg">
                {performanceResults.averageFPS.toFixed(1)}
              </div>
            </div>
            
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Frame Drops</div>
              <div className="font-semibold text-lg">
                {performanceResults.frameDrops}
              </div>
            </div>
            
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Memory Usage</div>
              <div className="font-semibold text-lg">
                {performanceResults.memoryUsage.toFixed(1)} MB
              </div>
            </div>
            
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Test Duration</div>
              <div className="font-semibold text-lg">
                {(performanceResults.testDuration / 1000).toFixed(1)}s
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Test Log */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Test Log</h2>
        
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-64 overflow-y-auto">
          {testLog.map((entry, index) => (
            <div key={index} className="mb-1">
              {entry}
            </div>
          ))}
          {testLog.length === 0 && (
            <div className="text-gray-500">No log entries yet...</div>
          )}
        </div>
      </div>

      {/* Warnings and Recommendations */}
      {compatibility && (compatibility.warnings.length > 0 || compatibility.recommendations.length > 0) && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Issues & Recommendations</h2>
          
          {compatibility.warnings.length > 0 && (
            <div className="mb-4">
              <h3 className="font-semibold text-red-600 mb-2 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Warnings
              </h3>
              <ul className="space-y-1">
                {compatibility.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-red-700 bg-red-50 p-2 rounded">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {compatibility.recommendations.length > 0 && (
            <div>
              <h3 className="font-semibold text-blue-600 mb-2 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Recommendations
              </h3>
              <ul className="space-y-1">
                {compatibility.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-sm text-blue-700 bg-blue-50 p-2 rounded">
                    {recommendation}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BrowserTester;