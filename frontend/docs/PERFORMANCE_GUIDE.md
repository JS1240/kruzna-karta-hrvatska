# Performance Testing and Maintenance Guide

This comprehensive guide covers testing and maintaining 60fps on desktop and 30fps minimum on mobile for the animated background system.

## 🎯 Performance Targets

### Target Frame Rates
- **Desktop**: 60fps target, 55fps minimum acceptable
- **Mobile**: 30fps target, 25fps minimum acceptable  
- **Tablet**: 45fps target, 38fps minimum acceptable

### Memory Limits
- **Desktop**: 512MB maximum
- **Mobile**: 256MB maximum
- **Tablet**: 384MB maximum

### Frame Time Targets
- **Desktop**: ≤16.67ms per frame
- **Mobile**: ≤33.33ms per frame
- **Tablet**: ≤22.22ms per frame

## 🧪 Testing Framework

### Available Testing Tools

#### 1. Performance Test Runner
```bash
# Basic performance validation
npm run performance:test --test validation

# Stress testing
npm run performance:test --test stress --device mobile

# Comprehensive benchmark suite
npm run performance:test --test benchmark --scenario "High Performance"

# Continuous monitoring
npm run performance:test --continuous --duration 30000
```

#### 2. Performance Validation Script
```bash
# Validate all performance targets
npm run performance:validate

# Validate specific device
npm run performance:validate --device mobile --strict

# Validate with multiple iterations
npm run performance:validate --iterations 3 --verbose
```

#### 3. Device Testing Framework
```bash
# Run comprehensive device tests
npm run performance:test --test device-comprehensive

# Edge case validation
npm run performance:test --test edge-cases --device mobile

# Regression testing
npm run performance:test --test regression
```

#### 4. Performance Monitoring
```bash
# Start real-time monitoring
npm run performance:monitor

# Generate performance dashboard
npm run performance:dashboard

# Check performance budgets
npm run performance:budget
```

### Test Scenarios

#### Basic Scenarios
1. **Basic Animation**: Standard settings with default particle count
2. **Mobile Optimized**: Reduced complexity for mobile devices
3. **High Intensity**: Enhanced effects for high-end devices
4. **Stress Test**: Maximum load testing

#### Edge Case Scenarios
1. **Thermal Throttling**: Device overheating simulation
2. **Low Memory**: Memory pressure scenarios
3. **Slow Network**: Poor connectivity impact
4. **Low Battery**: Power saving mode testing
5. **Multitasking**: Background app interference

## 📊 Performance Monitoring

### Real-time Monitoring

```typescript
import { startGlobalPerformanceMonitoring } from '@/utils/performanceMonitor';

// Start monitoring with callbacks
const monitor = startGlobalPerformanceMonitoring(
  {
    targetFPS: 60, // Desktop target
    minFPS: 55,    // Desktop minimum
  },
  {
    onMetrics: (metrics) => {
      console.log(`Current FPS: ${metrics.fps}`);
    },
    onAlert: (alert) => {
      console.warn(`Performance alert: ${alert.message}`);
    },
  }
);
```

### Performance Budget Enforcement

```typescript
import { initializeBudgetManager } from '@/utils/performanceBudget';

// Initialize budget manager
const budgetManager = initializeBudgetManager({
  onViolation: (violation) => {
    console.error(`Budget violation: ${violation.message}`);
  },
  onOptimization: (action) => {
    console.log(`Auto-optimization applied: ${action.description}`);
  },
});

// Set strict production budget
budgetManager.setActiveBudget('production');

// Check compliance
const report = budgetManager.checkBudgetCompliance(currentMetrics);
```

### Dashboard Access

The performance dashboard provides real-time monitoring:

```bash
# Generate and open performance dashboard
npm run performance:dashboard
open dist/performance-dashboard.html
```

Dashboard features:
- Real-time FPS monitoring
- Memory usage tracking
- Device information display
- Performance alerts
- Historical trends
- Optimization recommendations

## 🔧 Performance Optimization

### Automatic Optimizations

The system includes automatic optimizations triggered by performance budgets:

1. **Particle Count Reduction**: Automatically reduces particles when FPS drops
2. **Quality Downgrade**: Lowers animation quality under stress
3. **Effect Disabling**: Disables non-essential effects
4. **Frame Rate Throttling**: Reduces target frame rate to maintain stability
5. **Memory Cleanup**: Triggers garbage collection and cleanup

### Manual Optimization Strategies

#### For Desktop (60fps target)
```typescript
// Enable high-performance mode
const desktopSettings = {
  particleCount: 24,
  intensity: 0.8,
  enableEffects: true,
  targetFPS: 60,
  adaptiveQuality: true,
};
```

#### For Mobile (30fps target)
```typescript
// Enable mobile optimizations
const mobileSettings = {
  particleCount: 6,
  intensity: 0.3,
  enableEffects: false,
  targetFPS: 30,
  enableMobileOptimizations: true,
  bundleOptimization: 'balanced',
};
```

#### Adaptive Quality System
```typescript
// Enable adaptive quality based on performance
const adaptiveSettings = {
  enableAdaptiveQuality: true,
  qualityLevels: {
    high: { particles: 24, effects: true },
    medium: { particles: 12, effects: true },
    low: { particles: 6, effects: false },
    minimal: { particles: 3, effects: false },
  },
  performanceThresholds: {
    high: 55,    // Switch to high quality above 55fps
    medium: 45,  // Switch to medium quality above 45fps
    low: 35,     // Switch to low quality above 35fps
    minimal: 25, // Switch to minimal quality above 25fps
  },
};
```

## 🔍 Debugging Performance Issues

### Common Performance Problems

#### 1. Low FPS on Desktop
**Symptoms**: FPS below 55 on high-end desktop
**Causes**:
- Too many particles
- Complex shader calculations
- Memory leaks
- Background processes

**Solutions**:
```bash
# Run stress test to identify bottleneck
npm run performance:test --test stress --device desktop

# Check memory usage
npm run performance:monitor --memory-focus

# Analyze bundle size impact
npm run bundle:analyze
```

#### 2. Poor Mobile Performance
**Symptoms**: FPS below 25 on mobile devices
**Causes**:
- Mobile optimizations not enabled
- Heavy texture usage
- Excessive draw calls
- Thermal throttling

**Solutions**:
```bash
# Test mobile-specific scenarios
npm run performance:validate --device mobile --strict

# Check mobile optimization loading
npm run performance:test --test mobile-optimized

# Validate edge cases
npm run performance:test --test edge-cases --device mobile
```

#### 3. Memory Leaks
**Symptoms**: Continuously increasing memory usage
**Causes**:
- Animation objects not cleaned up
- Event listeners not removed
- Texture objects accumulating

**Solutions**:
```bash
# Monitor memory over time
npm run performance:monitor --duration 300000 # 5 minutes

# Check for memory leaks
npm run performance:test --test memory-leak
```

#### 4. Inconsistent Performance
**Symptoms**: Performance varies widely during testing
**Causes**:
- Garbage collection pauses
- Thermal throttling
- Background applications
- Network interference

**Solutions**:
```bash
# Run regression tests
npm run performance:test --test regression

# Multiple iteration testing
npm run performance:validate --iterations 5 --verbose
```

### Performance Debugging Tools

#### 1. Browser DevTools Integration
```typescript
// Enable performance profiling
if (process.env.NODE_ENV === 'development') {
  import('@/utils/performanceProfiler').then(profiler => {
    profiler.startProfiling({
      captureFrames: true,
      captureMemory: true,
      captureCPU: true,
    });
  });
}
```

#### 2. Performance Metrics Collection
```typescript
import { quickPerformanceCheck } from '@/utils/performanceMonitor';

// Quick 5-second performance check
const report = await quickPerformanceCheck(5000);
console.log('Performance Report:', report);
```

#### 3. Device Capability Testing
```typescript
import { deviceTestingFramework } from '@/utils/deviceTestingFramework';

// Test specific device configurations
const results = await deviceTestingFramework.runComprehensiveDeviceTests(
  ['iPhone 14 Pro', 'Samsung Galaxy A54'],
  ['Thermal Throttling', 'Low Memory']
);
```

## 📋 Testing Checklist

### Pre-Release Performance Validation

- [ ] **Desktop Performance**
  - [ ] 60fps achieved in basic scenarios
  - [ ] 55fps minimum maintained under stress
  - [ ] Memory usage below 512MB
  - [ ] Smooth performance across different resolutions

- [ ] **Mobile Performance**
  - [ ] 30fps achieved with mobile optimizations
  - [ ] 25fps minimum maintained under stress  
  - [ ] Memory usage below 256MB
  - [ ] Battery impact minimized

- [ ] **Edge Case Testing**
  - [ ] Thermal throttling scenarios pass
  - [ ] Low memory conditions handled
  - [ ] Network interruption recovery
  - [ ] Background app interference

- [ ] **Cross-Device Validation**
  - [ ] High-end devices perform optimally
  - [ ] Mid-range devices meet minimum requirements
  - [ ] Low-end devices gracefully degrade

### Automated Testing Pipeline

```yaml
# Example CI/CD integration
performance-tests:
  runs-on: ubuntu-latest
  steps:
    - name: Build application
      run: npm run build
      
    - name: Validate performance targets
      run: npm run performance:validate --strict
      
    - name: Run stress tests
      run: npm run performance:test --test stress
      
    - name: Check bundle budgets
      run: npm run bundle:enforce:strict
      
    - name: Generate performance report
      run: npm run performance:dashboard
```

## 📈 Performance Metrics

### Key Performance Indicators (KPIs)

1. **Frame Rate Consistency**
   - Target: 95% of frames within target range
   - Measurement: Frame time variance analysis

2. **Memory Efficiency**
   - Target: Memory usage growth <5% per hour
   - Measurement: Memory leak detection

3. **Startup Performance**
   - Target: Animation ready within 2 seconds
   - Measurement: Time to first frame

4. **Battery Impact**
   - Target: <10% additional battery drain
   - Measurement: Power consumption monitoring

### Performance Reporting

```bash
# Generate comprehensive performance report
npm run performance:report

# Export performance data
npm run performance:export

# Compare with baseline
npm run performance:compare --baseline previous-release
```

## 🚀 Best Practices

### Development Practices

1. **Regular Performance Testing**
   - Run validation before every commit
   - Include performance tests in CI/CD
   - Monitor production performance metrics

2. **Progressive Enhancement**
   - Start with minimal settings
   - Add features based on device capability
   - Provide fallback options

3. **Device-Aware Development**
   - Test on actual devices, not just simulators
   - Consider thermal constraints
   - Account for background app interference

### Monitoring in Production

1. **Real-User Monitoring (RUM)**
   - Track actual user performance metrics
   - Monitor performance across different devices
   - Set up alerts for performance degradation

2. **Performance Budgets**
   - Enforce strict performance budgets
   - Automatically optimize based on metrics
   - Regular budget review and adjustment

3. **Continuous Optimization**
   - Regular performance profiling
   - A/B testing for optimizations
   - User feedback integration

## 📚 Additional Resources

### Performance Tools
- [Performance Test Runner](../scripts/performance-test-runner.js)
- [Validation Script](../scripts/validate-performance-targets.js)
- [Performance Dashboard](../scripts/performance-dashboard.html)
- [Bundle Monitor](../scripts/bundle-monitor.js)

### Utilities
- [Performance Monitor](../src/utils/performanceMonitor.ts)
- [Performance Budget](../src/utils/performanceBudget.ts)
- [Device Testing Framework](../src/utils/deviceTestingFramework.ts)
- [Performance Testing Suite](../src/utils/performanceTesting.ts)

### Configuration Files
- [Performance Budgets](../src/utils/performanceBudget.ts#L25-L65)
- [Device Profiles](../src/utils/deviceTestingFramework.ts#L85-L210)
- [Test Scenarios](../scripts/validate-performance-targets.js#L45-L68)

---

This guide ensures consistent 60fps desktop and 30fps mobile performance through comprehensive testing, monitoring, and optimization strategies.