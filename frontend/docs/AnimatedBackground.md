# AnimatedBackground Component Documentation

## Overview

The `AnimatedBackground` component provides a sophisticated animated background using VANTA.js topology animation, integrated with the established brand color system and designed for optimal performance and accessibility.

## Features

- **Brand Color Integration**: Uses established brand colors (#3674B5, #578FCA)
- **Performance Optimization**: Automatic device detection and performance scaling
- **Accessibility Compliance**: Respects `prefers-reduced-motion` media queries
- **Responsive Design**: Adapts to different screen sizes
- **Error Handling**: Graceful fallbacks and error reporting
- **TypeScript Support**: Full type safety and IntelliSense

## Basic Usage

```tsx
import AnimatedBackground from '@/components/AnimatedBackground';

function MyComponent() {
  return (
    <AnimatedBackground intensity={0.5} opacity={0.3}>
      <div className="relative z-10 p-8">
        <h1>Your content here</h1>
      </div>
    </AnimatedBackground>
  );
}
```

## Props

### Core Configuration

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `enabled` | `boolean` | `true` | Enable/disable the animation |
| `intensity` | `number` | `0.5` | Animation intensity (0-1) |
| `opacity` | `number` | `0.3` | Background opacity (0-1) |
| `className` | `string` | `''` | Additional CSS classes |
| `children` | `ReactNode` | - | Content to render over background |

### Performance & Accessibility

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `performance` | `'high' \| 'medium' \| 'low'` | `'medium'` | Performance preset |
| `respectReducedMotion` | `boolean` | `true` | Honor reduced motion preference |
| `id` | `string` | - | Unique identifier for the effect |

### Customization

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `colors` | `{ primary?: string, secondary?: string }` | Brand colors | Custom color override |

## Performance Modes

### High Performance
```tsx
<AnimatedBackground performance="high" intensity={0.7} opacity={0.4}>
  {/* Content */}
</AnimatedBackground>
```
- **Particles**: 15
- **Max Distance**: 25
- **Spacing**: 12
- **Best for**: High-end desktops, hero sections

### Medium Performance (Default)
```tsx
<AnimatedBackground performance="medium" intensity={0.5} opacity={0.3}>
  {/* Content */}
</AnimatedBackground>
```
- **Particles**: 10-12
- **Max Distance**: 20
- **Spacing**: 20
- **Best for**: Most devices, general use

### Low Performance
```tsx
<AnimatedBackground performance="low" intensity={0.3} opacity={0.2}>
  {/* Content */}
</AnimatedBackground>
```
- **Particles**: 6-8
- **Max Distance**: 15
- **Spacing**: 25
- **Best for**: Mobile devices, older hardware

## Accessibility Features

### Reduced Motion Support
The component automatically detects and respects the user's `prefers-reduced-motion` setting:

```tsx
<AnimatedBackground respectReducedMotion={true}>
  {/* Animation will be disabled if user prefers reduced motion */}
</AnimatedBackground>
```

When reduced motion is preferred:
- Animation is completely disabled
- Falls back to a subtle gradient background
- Maintains visual consistency

### Content Overlay
Always wrap your content with relative positioning:

```tsx
<AnimatedBackground>
  <div className="relative z-10">
    {/* Your content with proper z-index */}
  </div>
</AnimatedBackground>
```

## Advanced Usage

### Custom Colors
```tsx
<AnimatedBackground
  colors={{
    primary: '#FF6B6B',
    secondary: '#4ECDC4'
  }}
  intensity={0.6}
>
  {/* Content */}
</AnimatedBackground>
```

### Conditional Animation
```tsx
const [animationEnabled, setAnimationEnabled] = useState(true);

<AnimatedBackground
  enabled={animationEnabled && !isLowBandwidth}
  performance={isMobile ? 'low' : 'high'}
>
  {/* Content */}
</AnimatedBackground>
```

### Hero Section Implementation
```tsx
<section className="min-h-screen">
  <AnimatedBackground
    performance="high"
    intensity={0.6}
    opacity={0.3}
    className="absolute inset-0"
  >
    <div className="relative z-10 container mx-auto px-4 py-16">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-brand-primary mb-6">
          Welcome to Our Platform
        </h1>
        <p className="text-xl text-brand-black/80 mb-8">
          Experience the future of digital interaction
        </p>
        <button className="bg-brand-primary text-brand-white px-8 py-4 rounded-lg">
          Get Started
        </button>
      </div>
    </div>
  </AnimatedBackground>
</section>
```

## Blue-Only Mode (T3.2)

The component supports a strict blue-only color scheme as specified in the PRD:

```tsx
<AnimatedBackground 
  blueOnly={true}
  blueIntensity="medium"
  performance="high"
>
  <div>Content with blue-only animation</div>
</AnimatedBackground>
```

### Blue Intensity Variants

- **`light`**: Lighter blue variant (0x7BA3D9)
- **`medium`**: Primary blue (0x3674B5) - default
- **`dark`**: Darker blue variant (0x2A5A94)

### Key Features

- Strictly uses only blue tones (#3674B5, #578FCA)
- Three intensity levels for varied visual effects
- Performance optimization maintained across all variants
- Full accessibility compliance with reduced motion support
- Graceful fallback to blue gradient when animation disabled

## Styling Guidelines

### Content Overlay Best Practices
```tsx
{/* ✅ Good: Proper backdrop blur and transparency */}
<div className="bg-white/80 backdrop-blur-sm rounded-lg p-6">
  <h2>Content Title</h2>
</div>

{/* ✅ Good: High contrast with brand colors */}
<div className="bg-brand-white/90 text-brand-black p-4">
  <p>Readable content</p>
</div>

{/* ❌ Avoid: Low contrast or no background */}
<div className="text-gray-500">
  <p>Hard to read content</p>
</div>
```

### Responsive Considerations
```tsx
<AnimatedBackground
  performance={isMobile ? 'low' : 'medium'}
  intensity={isMobile ? 0.3 : 0.5}
  opacity={isMobile ? 0.2 : 0.3}
  className="h-screen md:h-auto"
>
  {/* Content that adapts to screen size */}
</AnimatedBackground>
```

## Performance Optimization

### Bundle Size Impact
- **VANTA.js**: ~45KB gzipped
- **Three.js**: Shared dependency (~100KB gzipped)
- **Component**: ~2KB gzipped

### Runtime Performance
- **Desktop**: Targets 60fps
- **Mobile**: Targets 30fps minimum
- **Automatic**: Device detection and optimization

### Memory Management
The component automatically:
- Cleans up VANTA effects on unmount
- Handles window resize events
- Monitors performance and adjusts if needed

## Error Handling

### Development Mode
```tsx
{/* Error messages shown only in development */}
<AnimatedBackground>
  {/* If initialization fails, error will be shown in dev mode */}
</AnimatedBackground>
```

### Production Fallbacks
- Animation initialization failure → gradient fallback
- Performance issues → automatic downgrade
- Browser compatibility issues → static background

## Browser Support

### Fully Supported
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Fallback Support
- Older browsers receive gradient backgrounds
- No JavaScript errors or broken layouts

## Testing

### Development Testing
Visit `/dev/animations` to test different configurations:
- Performance modes
- Custom colors
- Accessibility features
- Error conditions

### Unit Testing
```tsx
import { render } from '@testing-library/react';
import AnimatedBackground from '@/components/AnimatedBackground';

test('renders with fallback when animation fails', () => {
  const { getByTestId } = render(
    <AnimatedBackground enabled={false}>
      <div>Test content</div>
    </AnimatedBackground>
  );
  
  expect(getByTestId('animated-background')).toBeInTheDocument();
});
```

## Migration Guide

### From Previous Animation Utils
```tsx
// Old approach
useEffect(() => {
  const manager = createTopologyAnimation(elementRef.current);
  manager.init();
  return () => manager.destroy();
}, []);

// New approach
<AnimatedBackground performance="medium">
  {/* Content */}
</AnimatedBackground>
```

### Integration Checklist
- [ ] Import the component
- [ ] Wrap content with relative positioning
- [ ] Test on different devices
- [ ] Verify accessibility compliance
- [ ] Check performance impact

---

**Component Location**: `src/components/AnimatedBackground.tsx`  
**Dependencies**: VANTA.js, Three.js, Brand Colors  
**Status**: ✅ Production Ready
