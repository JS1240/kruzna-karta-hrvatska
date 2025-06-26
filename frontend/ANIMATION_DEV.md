# Animation Development Environment

This development environment provides tools for testing and developing the animated background system.

## Quick Start

### 1. Start Development Server with Animation Testing
```bash
npm run dev:animations
```
This starts the dev server and makes the animation test page available at:
`http://localhost:5173/dev/animations`

### 2. Performance Testing Mode
```bash
npm run test:animations
```
Starts the dev server with performance monitoring enabled and opens the test page automatically.

### 3. Check TypeScript and Build
```bash
npm run check:animations
npm run build:check
```

## Animation Test Page Features

### 🎨 Animation Testing
- **VANTA Topology Tests**: Low, medium, and high intensity settings
- **Real-time Switching**: Start/stop animations on demand
- **Performance Monitoring**: Memory usage tracking
- **Mobile Optimization**: Automatic device detection

### 🎯 Color Validation
- **Brand Color Preview**: Visual display of all brand colors
- **WCAG Compliance**: Automatic contrast ratio validation
- **Accessibility Checks**: Real-time compliance status

### 📊 Performance Monitoring
- **Memory Usage**: Track JavaScript heap usage
- **Frame Rate**: Monitor animation performance
- **Bundle Size**: Validate against 500KB limit

## Development Scripts

| Command | Description |
|---------|-------------|
| `npm run dev:animations` | Start dev server with animation testing |
| `npm run test:animations` | Performance testing mode with browser auto-open |
| `npm run check:animations` | TypeScript validation |
| `npm run build:check` | Build and validate bundle sizes |

## Manual Script Usage

You can also use the development script directly:

```bash
# Start development server
./scripts/dev-animations.sh start

# Performance testing
./scripts/dev-animations.sh perf

# TypeScript checks
./scripts/dev-animations.sh check

# Build and size validation
./scripts/dev-animations.sh build

# Color validation
./scripts/dev-animations.sh colors
```

## Animation Types Available

### VANTA Topology
- **Low Intensity**: 4-8 particles, wide spacing, minimal connections
- **Medium Intensity**: 6-12 particles, balanced settings (default)
- **High Intensity**: 8-16 particles, close spacing, more connections

### Performance Targets
- **Desktop**: 60fps target, high intensity allowed
- **Mobile**: 30fps minimum, automatic low intensity
- **Bundle Size**: <500KB for animation libraries

## Accessibility Features

- **Reduced Motion**: Automatically disabled when user prefers reduced motion
- **Performance Fallbacks**: Lower settings for low-performance devices
- **Memory Monitoring**: Automatic warnings for high memory usage
- **Tab Visibility**: Animations pause when tab is hidden

## Color Scheme

The development environment validates the complete brand color palette:

- **Primary**: #3674B5, #578FCA (buttons, links, headers)
- **Accent**: #F5F0CD, #FADA7A (highlights, accents)
- **Contrast**: #000000, #FFFFFF (text, high contrast)
- **Animation**: Blue tones only (#3674B5, #578FCA)

All color combinations are automatically validated for WCAG 2.1 AA compliance.

## Troubleshooting

### Common Issues

1. **Script Permission Denied**
   ```bash
   chmod +x scripts/dev-animations.sh
   ```

2. **TypeScript Errors**
   - Existing project errors are expected and not related to animation code
   - Focus on animation-specific files for validation

3. **Animation Not Loading**
   - Check browser console for error messages
   - Verify VANTA and three.js libraries are loaded
   - Check for `prefers-reduced-motion` settings

4. **Performance Issues**
   - Use low intensity settings for testing
   - Monitor memory usage in the test page
   - Check frame rate in browser dev tools

### Browser Support

- **Chrome 80+**: Full support
- **Firefox 75+**: Full support  
- **Safari 13+**: Full support
- **Edge 80+**: Full support
- **Mobile**: Automatic optimization

## Next Steps

1. Visit the test page to validate animations
2. Test performance across different devices
3. Validate color contrast compliance
4. Check bundle sizes meet requirements
5. Test accessibility features
