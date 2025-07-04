/**
 * Mobile Browser Tester Component
 * 
 * Specialized testing component for mobile browser compatibility validation
 * with focus on iOS Safari 13+ and Chrome Mobile 80+
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Smartphone,
  Tablet,
  Wifi,
  Battery,
  Thermometer,
  Monitor,
  Play,
  Pause,
  RotateCcw,
  Download,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Zap,
  Eye
} from 'lucide-react';
import { 
  detectMobileCapabilities, 
  applyMobileOptimizations,
  getMobileCapabilities,
  type MobileCapabilities 
} from '@/utils/mobileOptimizations';
import { 
  runCompatibilityTest, 
  testAnimationPerformance,
  type BrowserCompatibility 
} from '@/utils/browserCompatibility';
import { initializeFallbackManager, getCurrentFallbackDecision } from '@/utils/fallbackManager';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import AnimatedBackground from '@/components/AnimatedBackground';
import CSSFallbackBackground from '@/components/CSSFallbackBackground';
import { TouchButton } from '@/components/mobile';
import { cn } from '@/lib/utils';

export interface MobileBrowserTesterProps {
  className?: string;
  debug?: boolean;
}

interface MobileTestResult {
  testId: string;
  testName: string;
  passed: boolean;
  score: number;
  details: Record<string, any>;
  timestamp: string;
  performance?: {
    fps: number;
    memoryUsage: number;
    batteryDelta?: number;
  };
  error?: string;
}

interface TouchTestResult {
  touchSupport: boolean;
  maxTouchPoints: number;
  touchEventLatency: number;
  gestureSupport: boolean;
}

interface ViewportTestResult {
  viewportWidth: number;
  viewportHeight: number;
  devicePixelRatio: number;
  orientationSupport: boolean;
  visualViewportSupport: boolean;
  safeAreaSupport: boolean;
}

/**
 * Mobile Browser Tester Component
 */
export const MobileBrowserTester: React.FC<MobileBrowserTesterProps> = ({
  className = '',
  debug = false,
}) => {
  const [mobileCapabilities, setMobileCapabilities] = useState<MobileCapabilities | null>(null);
  const [compatibility, setCompatibility] = useState<BrowserCompatibility | null>(null);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState<string>('');
  const [testResults, setTestResults] = useState<Record<string, MobileTestResult>>({});
  const [touchTestResult, setTouchTestResult] = useState<TouchTestResult | null>(null);
  const [viewportTestResult, setViewportTestResult] = useState<ViewportTestResult | null>(null);
  const [batteryInfo, setBatteryInfo] = useState<any>(null);
  const [networkInfo, setNetworkInfo] = useState<any>(null);
  const [testLog, setTestLog] = useState<string[]>([]);
  
  const testContainerRef = useRef<HTMLDivElement>(null);
  const { prefersReducedMotion, canAnimate } = useReducedMotion();

  // Initialize mobile testing environment
  useEffect(() => {
    const initializeMobileTesting = async () => {
      try {
        addLog('Initializing mobile testing environment...');
        
        // Detect mobile capabilities
        const capabilities = await detectMobileCapabilities();
        setMobileCapabilities(capabilities);
        addLog(`Mobile platform detected: ${capabilities.platform}`);
        addLog(`Device memory: ${capabilities.deviceMemory}GB`);
        addLog(`Hardware concurrency: ${capabilities.hardwareConcurrency} cores`);
        
        // Run compatibility test
        const compat = runCompatibilityTest();
        setCompatibility(compat);
        addLog(`Browser compatibility score: ${compat.score}/100`);
        
        // Initialize fallback manager
        await initializeFallbackManager({
          strategy: 'auto',
          debug: debug,
        });
        
        // Apply mobile optimizations
        if (capabilities.isMobile || capabilities.isTablet) {
          await applyMobileOptimizations({
            debug: debug,
            aggressivePowerSaving: capabilities.isLowEndDevice,
          });
          addLog('Mobile optimizations applied');
        }
        
        // Test touch capabilities
        await testTouchCapabilities();
        
        // Test viewport capabilities
        await testViewportCapabilities();
        
        // Test battery API if available
        await testBatteryAPI();
        
        // Test network information
        await testNetworkInformation();
        
        addLog('Mobile testing environment ready');
        
      } catch (error) {
        addLog(`Initialization error: ${error}`);
        console.error('Mobile testing initialization failed:', error);
      }
    };

    initializeMobileTesting();
  }, [debug]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setTestLog(prev => [...prev, `${timestamp}: ${message}`]);
    if (debug) {
      console.log(`[MobileTester] ${message}`);
    }
  };

  /**
   * Test touch capabilities
   */
  const testTouchCapabilities = async (): Promise<void> => {
    addLog('Testing touch capabilities...');
    
    const touchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const maxTouchPoints = navigator.maxTouchPoints || 0;
    
    // Test touch event latency
    let touchEventLatency = 0;
    let gestureSupport = false;
    
    if (touchSupport) {
      const startTime = performance.now();
      const touchHandler = () => {
        touchEventLatency = performance.now() - startTime;
        document.removeEventListener('touchstart', touchHandler);
      };
      
      document.addEventListener('touchstart', touchHandler);
      
      // Simulate touch event for latency test
      setTimeout(() => {
        document.removeEventListener('touchstart', touchHandler);
      }, 100);
      
      // Test gesture support
      gestureSupport = 'ongesturestart' in window;
    }
    
    const result: TouchTestResult = {
      touchSupport,
      maxTouchPoints,
      touchEventLatency,
      gestureSupport,
    };
    
    setTouchTestResult(result);
    addLog(`Touch support: ${touchSupport ? 'Yes' : 'No'} (${maxTouchPoints} points)`);
  };

  /**
   * Test viewport capabilities
   */
  const testViewportCapabilities = async (): Promise<void> => {
    addLog('Testing viewport capabilities...');
    
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const devicePixelRatio = window.devicePixelRatio || 1;
    
    // Test orientation support
    const orientationSupport = 'orientation' in screen || 'orientation' in window;
    
    // Test Visual Viewport API
    const visualViewportSupport = 'visualViewport' in window;
    
    // Test CSS safe area support
    const safeAreaSupport = CSS.supports('padding: env(safe-area-inset-top)');
    
    const result: ViewportTestResult = {
      viewportWidth,
      viewportHeight,
      devicePixelRatio,
      orientationSupport,
      visualViewportSupport,
      safeAreaSupport,
    };
    
    setViewportTestResult(result);
    addLog(`Viewport: ${viewportWidth}x${viewportHeight} @ ${devicePixelRatio}x`);
  };

  /**
   * Test Battery API
   */
  const testBatteryAPI = async (): Promise<void> => {
    addLog('Testing Battery API...');
    
    try {
      if ('getBattery' in navigator) {
        const battery = await (navigator as any).getBattery();
        const info = {
          charging: battery.charging,
          level: Math.round(battery.level * 100),
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime,
        };
        setBatteryInfo(info);
        addLog(`Battery: ${info.level}% (${info.charging ? 'charging' : 'discharging'})`);
      } else {
        addLog('Battery API not available');
      }
    } catch (error) {
      addLog(`Battery API test failed: ${error}`);
    }
  };

  /**
   * Test Network Information API
   */
  const testNetworkInformation = async (): Promise<void> => {
    addLog('Testing Network Information API...');
    
    try {
      const connection = (navigator as any).connection || 
                       (navigator as any).mozConnection || 
                       (navigator as any).webkitConnection;
      
      if (connection) {
        const info = {
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData,
        };
        setNetworkInfo(info);
        addLog(`Network: ${info.effectiveType} (${info.downlink} Mbps, ${info.rtt}ms RTT)`);
      } else {
        addLog('Network Information API not available');
      }
    } catch (error) {
      addLog(`Network Information API test failed: ${error}`);
    }
  };

  /**
   * Run iOS Safari specific tests
   */
  const runIOSSafariTests = async (): Promise<void> => {
    if (!mobileCapabilities || mobileCapabilities.platform !== 'ios') {
      addLog('Skipping iOS Safari tests - not an iOS device');
      return;
    }

    setCurrentTest('iOS Safari Compatibility');
    setIsTestRunning(true);
    addLog('Running iOS Safari 13+ compatibility tests...');

    try {
      const testStartTime = performance.now();
      let testScore = 100;
      const details: Record<string, any> = {};

      // Test 1: WebGL support on iOS
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      const webglSupported = !!gl;
      details.webglSupport = webglSupported;
      
      if (!webglSupported) {
        testScore -= 30;
        addLog('❌ WebGL not supported on iOS Safari');
      } else {
        addLog('✅ WebGL supported on iOS Safari');
        
        // Test WebGL extensions
        const extensions = gl.getSupportedExtensions() || [];
        details.webglExtensions = extensions.length;
        addLog(`WebGL extensions: ${extensions.length}`);
      }

      // Test 2: Backdrop filter support
      const backdropFilterSupported = CSS.supports('backdrop-filter', 'blur(10px)') || 
                                     CSS.supports('-webkit-backdrop-filter', 'blur(10px)');
      details.backdropFilter = backdropFilterSupported;
      
      if (!backdropFilterSupported) {
        testScore -= 10;
        addLog('❌ Backdrop filter not supported');
      } else {
        addLog('✅ Backdrop filter supported');
      }

      // Test 3: Touch events and gestures
      details.touchEvents = touchTestResult?.touchSupport || false;
      details.gestureEvents = touchTestResult?.gestureSupport || false;
      
      if (!details.touchEvents) {
        testScore -= 20;
        addLog('❌ Touch events not properly supported');
      } else {
        addLog('✅ Touch events supported');
      }

      // Test 4: Viewport meta and safe area
      details.safeAreaSupport = viewportTestResult?.safeAreaSupport || false;
      details.visualViewport = viewportTestResult?.visualViewportSupport || false;
      
      if (!details.safeAreaSupport) {
        testScore -= 5;
        addLog('⚠️ CSS safe area not supported');
      } else {
        addLog('✅ CSS safe area supported');
      }

      // Test 5: Performance test
      const perfResults = await testAnimationPerformance();
      details.performance = perfResults;
      
      if (perfResults.averageFPS < 20) {
        testScore -= 20;
        addLog(`❌ Poor performance: ${perfResults.averageFPS.toFixed(1)} FPS`);
      } else if (perfResults.averageFPS < 30) {
        testScore -= 10;
        addLog(`⚠️ Acceptable performance: ${perfResults.averageFPS.toFixed(1)} FPS`);
      } else {
        addLog(`✅ Good performance: ${perfResults.averageFPS.toFixed(1)} FPS`);
      }

      const testDuration = performance.now() - testStartTime;
      
      const result: MobileTestResult = {
        testId: 'ios-safari-13',
        testName: 'iOS Safari 13+ Compatibility',
        passed: testScore >= 70,
        score: Math.max(0, testScore),
        details,
        timestamp: new Date().toISOString(),
        performance: {
          fps: perfResults.averageFPS,
          memoryUsage: perfResults.memoryUsage,
        },
      };

      setTestResults(prev => ({ ...prev, 'ios-safari-13': result }));
      addLog(`iOS Safari test completed: ${testScore}/100`);

    } catch (error) {
      const errorResult: MobileTestResult = {
        testId: 'ios-safari-13',
        testName: 'iOS Safari 13+ Compatibility',
        passed: false,
        score: 0,
        details: {},
        timestamp: new Date().toISOString(),
        error: String(error),
      };
      
      setTestResults(prev => ({ ...prev, 'ios-safari-13': errorResult }));
      addLog(`iOS Safari test failed: ${error}`);
    } finally {
      setIsTestRunning(false);
      setCurrentTest('');
    }
  };

  /**
   * Run Chrome Mobile specific tests
   */
  const runChromeMobileTests = async (): Promise<void> => {
    if (!mobileCapabilities || 
        !(mobileCapabilities.platform === 'android' || 
          (compatibility?.browser.name === 'Chrome' && compatibility?.browser.isMobile))) {
      addLog('Skipping Chrome Mobile tests - not Chrome Mobile');
      return;
    }

    setCurrentTest('Chrome Mobile Compatibility');
    setIsTestRunning(true);
    addLog('Running Chrome Mobile 80+ compatibility tests...');

    try {
      const testStartTime = performance.now();
      let testScore = 100;
      const details: Record<string, any> = {};

      // Test 1: Chrome version check
      const chromeVersion = compatibility?.browser.majorVersion || 0;
      details.chromeVersion = chromeVersion;
      
      if (chromeVersion < 80) {
        testScore -= 50;
        addLog(`❌ Chrome version ${chromeVersion} below minimum 80`);
      } else {
        addLog(`✅ Chrome version ${chromeVersion} meets requirements`);
      }

      // Test 2: WebGL 2.0 support
      const canvas = document.createElement('canvas');
      const gl2 = canvas.getContext('webgl2');
      details.webgl2Support = !!gl2;
      
      if (!gl2) {
        testScore -= 15;
        addLog('❌ WebGL 2.0 not supported');
      } else {
        addLog('✅ WebGL 2.0 supported');
      }

      // Test 3: Device Memory API
      const deviceMemory = (navigator as any).deviceMemory;
      details.deviceMemoryAPI = !!deviceMemory;
      details.deviceMemory = deviceMemory || 'unknown';
      
      if (!deviceMemory) {
        testScore -= 5;
        addLog('⚠️ Device Memory API not available');
      } else {
        addLog(`✅ Device Memory API: ${deviceMemory}GB`);
      }

      // Test 4: Performance Observer API
      const perfObserverSupported = typeof PerformanceObserver !== 'undefined';
      details.performanceObserver = perfObserverSupported;
      
      if (!perfObserverSupported) {
        testScore -= 10;
        addLog('❌ Performance Observer not supported');
      } else {
        addLog('✅ Performance Observer supported');
      }

      // Test 5: Network Information API
      details.networkAPI = !!networkInfo;
      if (!networkInfo) {
        testScore -= 5;
        addLog('⚠️ Network Information API not available');
      } else {
        addLog('✅ Network Information API available');
      }

      // Test 6: Performance test with hardware acceleration
      const perfResults = await testAnimationPerformance();
      details.performance = perfResults;
      
      if (perfResults.averageFPS < 30) {
        testScore -= 20;
        addLog(`❌ Poor performance: ${perfResults.averageFPS.toFixed(1)} FPS`);
      } else if (perfResults.averageFPS < 45) {
        testScore -= 10;
        addLog(`⚠️ Acceptable performance: ${perfResults.averageFPS.toFixed(1)} FPS`);
      } else {
        addLog(`✅ Good performance: ${perfResults.averageFPS.toFixed(1)} FPS`);
      }

      // Test 7: Memory usage test
      if ('memory' in performance) {
        const memInfo = (performance as any).memory;
        details.memoryAPI = true;
        details.memoryUsage = memInfo.usedJSHeapSize / (1024 * 1024);
        addLog(`✅ Memory API available: ${details.memoryUsage.toFixed(1)}MB used`);
      } else {
        details.memoryAPI = false;
        testScore -= 5;
        addLog('⚠️ Memory API not available');
      }

      const result: MobileTestResult = {
        testId: 'chrome-mobile-80',
        testName: 'Chrome Mobile 80+ Compatibility',
        passed: testScore >= 70,
        score: Math.max(0, testScore),
        details,
        timestamp: new Date().toISOString(),
        performance: {
          fps: perfResults.averageFPS,
          memoryUsage: perfResults.memoryUsage,
        },
      };

      setTestResults(prev => ({ ...prev, 'chrome-mobile-80': result }));
      addLog(`Chrome Mobile test completed: ${testScore}/100`);

    } catch (error) {
      const errorResult: MobileTestResult = {
        testId: 'chrome-mobile-80',
        testName: 'Chrome Mobile 80+ Compatibility',
        passed: false,
        score: 0,
        details: {},
        timestamp: new Date().toISOString(),
        error: String(error),
      };
      
      setTestResults(prev => ({ ...prev, 'chrome-mobile-80': errorResult }));
      addLog(`Chrome Mobile test failed: ${error}`);
    } finally {
      setIsTestRunning(false);
      setCurrentTest('');
    }
  };

  /**
   * Run all mobile tests
   */
  const runAllMobileTests = async (): Promise<void> => {
    addLog('Starting comprehensive mobile browser tests...');
    
    await runIOSSafariTests();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    await runChromeMobileTests();
    
    addLog('All mobile tests completed');
  };

  /**
   * Export test results
   */
  const exportResults = (): void => {
    const report = {
      timestamp: new Date().toISOString(),
      mobileCapabilities,
      compatibility,
      testResults,
      touchTestResult,
      viewportTestResult,
      batteryInfo,
      networkInfo,
      testLog,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mobile-browser-test-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    addLog('Mobile test results exported');
  };

  /**
   * Get status color for test results
   */
  const getStatusColor = (result: MobileTestResult): string => {
    if (result.passed && result.score >= 90) return 'text-green-600';
    if (result.passed && result.score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  /**
   * Get status icon for test results
   */
  const getStatusIcon = (result: MobileTestResult): React.ReactNode => {
    if (result.passed && result.score >= 90) return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (result.passed && result.score >= 70) return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };

  return (
    <div className={cn('max-w-6xl mx-auto p-6 space-y-6', className)}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Mobile Browser Compatibility Tester
        </h1>
        <p className="text-gray-600">
          Specialized testing for iOS Safari 13+ and Chrome Mobile 80+ compatibility
        </p>
      </div>

      {/* Mobile Device Information */}
      {mobileCapabilities && compatibility && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            Mobile Device Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Platform</div>
              <div className="font-semibold flex items-center gap-1">
                {mobileCapabilities.platform === 'ios' ? (
                  <>
                    <Smartphone className="h-4 w-4" />
                    iOS
                  </>
                ) : mobileCapabilities.platform === 'android' ? (
                  <>
                    <Tablet className="h-4 w-4" />
                    Android
                  </>
                ) : (
                  <>
                    <Monitor className="h-4 w-4" />
                    {mobileCapabilities.platform}
                  </>
                )}
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Browser</div>
              <div className="font-semibold">
                {compatibility.browser.name} {compatibility.browser.version}
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Device Memory</div>
              <div className="font-semibold">{mobileCapabilities.deviceMemory}GB</div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Compatibility Score</div>
              <div className={cn('font-semibold text-xl', 
                compatibility.score >= 90 ? 'text-green-600' : 
                compatibility.score >= 70 ? 'text-yellow-600' : 'text-red-600'
              )}>
                {compatibility.score}/100
              </div>
            </div>
          </div>

          {/* Additional Mobile Info */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {batteryInfo && (
              <div className="text-center">
                <div className="text-sm text-gray-600 flex items-center justify-center gap-1">
                  <Battery className="h-4 w-4" />
                  Battery
                </div>
                <div className="font-semibold">
                  {batteryInfo.level}% {batteryInfo.charging ? '🔌' : '🔋'}
                </div>
              </div>
            )}
            
            {networkInfo && (
              <div className="text-center">
                <div className="text-sm text-gray-600 flex items-center justify-center gap-1">
                  <Wifi className="h-4 w-4" />
                  Network
                </div>
                <div className="font-semibold">{networkInfo.effectiveType}</div>
              </div>
            )}
            
            {touchTestResult && (
              <div className="text-center">
                <div className="text-sm text-gray-600">Touch Points</div>
                <div className="font-semibold">{touchTestResult.maxTouchPoints}</div>
              </div>
            )}
            
            {viewportTestResult && (
              <div className="text-center">
                <div className="text-sm text-gray-600">Pixel Ratio</div>
                <div className="font-semibold">{viewportTestResult.devicePixelRatio}x</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Test Controls */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Mobile Browser Tests</h2>
        
        <div className="flex flex-wrap gap-4 mb-6">
          <TouchButton
            variant="primary"
            onClick={runIOSSafariTests}
            disabled={isTestRunning || !mobileCapabilities?.platform}
            loading={isTestRunning && currentTest.includes('iOS')}
          >
            <Smartphone className="h-4 w-4" />
            Test iOS Safari 13+
          </TouchButton>
          
          <TouchButton
            variant="primary"
            onClick={runChromeMobileTests}
            disabled={isTestRunning}
            loading={isTestRunning && currentTest.includes('Chrome')}
          >
            <Tablet className="h-4 w-4" />
            Test Chrome Mobile 80+
          </TouchButton>
          
          <TouchButton
            variant="secondary"
            onClick={runAllMobileTests}
            disabled={isTestRunning}
            loading={isTestRunning && !currentTest.includes('iOS') && !currentTest.includes('Chrome')}
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
        </div>

        {/* Test Results */}
        <div className="space-y-4">
          {Object.values(testResults).map((result) => (
            <div
              key={result.testId}
              className="border rounded-lg p-4 bg-gray-50"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold flex items-center gap-2">
                  {getStatusIcon(result)}
                  {result.testName}
                </h3>
                <span className={cn('font-bold', getStatusColor(result))}>
                  {result.score}/100
                </span>
              </div>
              
              {result.performance && (
                <div className="text-sm text-gray-600 grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>FPS: {result.performance.fps.toFixed(1)}</div>
                  <div>Memory: {result.performance.memoryUsage.toFixed(1)}MB</div>
                  <div>Status: {result.passed ? 'Passed' : 'Failed'}</div>
                </div>
              )}
              
              {result.error && (
                <div className="text-sm text-red-600 mt-2">
                  Error: {result.error}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Test Area */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Test Area</h2>
        
        <div 
          ref={testContainerRef}
          className="relative w-full h-96 bg-gray-100 rounded-lg overflow-hidden"
        >
          {mobileCapabilities && (
            <CSSFallbackBackground
              mode="animated"
              style="gradient"
              theme="primary"
              intensity={0.5}
              opacity={0.3}
              debug={debug}
            />
          )}
          
          {isTestRunning && (
            <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
              <div className="bg-white rounded-lg p-4 shadow-xl">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-brand-primary"></div>
                  <span className="font-medium">Running {currentTest}...</span>
                </div>
              </div>
            </div>
          )}
        </div>
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
            <div className="text-gray-500">Initializing mobile testing...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MobileBrowserTester;