# Browser Compatibility Quick Reference

## Key Components

### Browser Tester
```tsx
import BrowserTester from '@/components/testing/BrowserTester';
<BrowserTester debug={true} />
```

### Enhanced Animated Background
```tsx
import AnimatedBackground from '@/components/AnimatedBackground';

<AnimatedBackground
  enableFallbacks={true}
  showFallbackDebug={true}
  autoPerformanceAdjustment={true}
/>
```

## Core Utilities

### Compatibility Testing
```typescript
import { runCompatibilityTest } from '@/utils/browserCompatibility';

const compatibility = runCompatibilityTest();
// Score: 0-100, Features: object, Browser: info
```

### Fallback Manager
```typescript
import { initializeFallbackManager } from '@/utils/fallbackManager';

const decision = await initializeFallbackManager({
  strategy: 'auto', // 'auto' | 'force-webgl' | 'force-css' | 'force-static'
  debug: true,
});
```

### Polyfills
```typescript
import { loadPolyfills } from '@/utils/polyfills';

await loadPolyfills({ debug: true });
```

### Mobile Optimizations
```typescript
import { applyMobileOptimizations } from '@/utils/mobileOptimizations';

await applyMobileOptimizations({
  enableBatteryOptimization: true,
  aggressivePowerSaving: false,
  debug: true,
});
```

## Browser Support Matrix

| Feature | Chrome 80+ | Firefox 75+ | Safari 13+ | Edge 80+ |
|---------|------------|-------------|-------------|----------|
| WebGL | ✅ | ✅ | ✅ | ✅ |
| CSS Animations | ✅ | ✅ | ✅ | ✅ |
| Backdrop Filter | ✅ | ✅ | ✅ | ✅ |
| Performance API | ✅ | ⚠️ | ⚠️ | ✅ |
| Memory API | ✅ | ❌ | ❌ | ✅ |

## Fallback Strategy

1. **Auto Mode:** Automatically selects best option
2. **WebGL:** High-performance 3D animations
3. **CSS Animated:** CSS-based particle animations
4. **CSS Static:** Static gradient patterns
5. **None:** No animations (reduced motion)

## Performance Thresholds

- **Desktop:** 60 FPS target, < 100MB memory
- **Mobile:** 30 FPS target, < 50MB memory
- **Low-end:** 20 FPS minimum, static fallbacks

## Quick Debug Commands

```javascript
// Check current browser
console.log(runCompatibilityTest().browser);

// Test performance
testAnimationPerformance().then(console.log);

// Get mobile capabilities
detectMobileCapabilities().then(console.log);

// Check current fallback
console.log(getCurrentFallbackDecision());
```

## Common Issues

### WebGL Context Lost
```typescript
canvas.addEventListener('webglcontextlost', () => {
  // Automatically handled by fallback system
});
```

### iOS Memory Issues
```typescript
// Automatically detected and optimized
// Check: mobileCapabilities.isLowEndDevice
```

### Firefox Performance
```typescript
// Automatically applies Firefox optimizations
// Check: compatibility.browser.name === 'Firefox'
```

## CSS Classes for Manual Control

```css
/* Force static fallback */
.force-static .vanta-canvas { display: none !important; }

/* Disable animations for reduced motion */
@media (prefers-reduced-motion: reduce) {
  .respect-motion * { animation: none !important; }
}

/* Mobile optimizations */
@media (max-width: 768px) {
  .mobile-optimized .fallback-particle {
    animation-duration: 30s !important;
  }
}
```

## Events

```typescript
// Listen for fallback changes
window.addEventListener('animation-fallback', (e) => {
  console.log('Fallback activated:', e.detail);
});

// Listen for performance issues
window.addEventListener('memory-warning', (e) => {
  console.log('Memory warning:', e.detail);
});

// Listen for thermal throttling
window.addEventListener('thermal-throttle-detected', () => {
  console.log('Device overheating - animations paused');
});
```

## Testing Checklist

- [ ] Test in Chrome 80+
- [ ] Test in Firefox 75+
- [ ] Test in Safari 13+ (macOS/iOS)
- [ ] Test in Edge 80+
- [ ] Test on mobile devices
- [ ] Test with reduced motion
- [ ] Test WebGL fallbacks
- [ ] Test performance monitoring
- [ ] Verify memory usage
- [ ] Check console for errors