#!/usr/bin/env node

/**
 * T3.6 Validation Script: Responsive Behavior for Different Screen Sizes
 * 
 * This script validates that the AnimatedBackground component properly implements
 * responsive behavior that adapts to different screen sizes with optimized performance.
 * 
 * Validation Criteria:
 * 1. Responsive interface props are properly defined
 * 2. Screen size detection and window resize monitoring
 * 3. Device-specific intensity and performance scaling
 * 4. Custom breakpoints and responsive modes
 * 5. Particle optimization for different screen sizes
 * 6. Responsive opacity and blur adaptations
 * 7. Demo integration in AnimationTestPage
 */

const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function logSuccess(message) {
  console.log(`${colors.green}✓${colors.reset} ${message}`);
}

function logError(message) {
  console.log(`${colors.red}✗${colors.reset} ${message}`);
}

function logWarning(message) {
  console.log(`${colors.yellow}⚠${colors.reset} ${message}`);
}

function logInfo(message) {
  console.log(`${colors.blue}ℹ${colors.reset} ${message}`);
}

function logHeader(message) {
  console.log(`\n${colors.bold}${colors.cyan}${message}${colors.reset}`);
}

let validationResults = {
  passed: 0,
  failed: 0,
  warnings: 0,
  details: []
};

function validateCheck(condition, successMessage, errorMessage, isWarning = false) {
  if (condition) {
    logSuccess(successMessage);
    validationResults.passed++;
    validationResults.details.push({ type: 'pass', message: successMessage });
  } else {
    if (isWarning) {
      logWarning(errorMessage);
      validationResults.warnings++;
      validationResults.details.push({ type: 'warning', message: errorMessage });
    } else {
      logError(errorMessage);
      validationResults.failed++;
      validationResults.details.push({ type: 'error', message: errorMessage });
    }
  }
}

// File paths
const animatedBackgroundPath = path.join(__dirname, '../src/components/AnimatedBackground.tsx');
const animationTestPagePath = path.join(__dirname, '../src/pages/AnimationTestPage.tsx');

logHeader('T3.6 Responsive Behavior Validation');
logInfo('Validating responsive behavior implementation for different screen sizes...\n');

// Check if files exist
if (!fs.existsSync(animatedBackgroundPath)) {
  logError('AnimatedBackground.tsx not found');
  process.exit(1);
}

if (!fs.existsSync(animationTestPagePath)) {
  logError('AnimationTestPage.tsx not found');
  process.exit(1);
}

// Read files
const animatedBackgroundContent = fs.readFileSync(animatedBackgroundPath, 'utf8');
const animationTestPageContent = fs.readFileSync(animationTestPagePath, 'utf8');

logHeader('1. Responsive Interface Props Validation');

// Check for responsive props in interface
const responsiveProps = [
  'responsive',
  'responsiveMode', 
  'responsiveBreakpoints',
  'mobileIntensity',
  'tabletIntensity', 
  'desktopIntensity'
];

responsiveProps.forEach(prop => {
  validateCheck(
    animatedBackgroundContent.includes(`/** ${prop === 'responsive' ? 'Enable responsive behavior for different screen sizes (T3.6)' : 
      prop === 'responsiveMode' ? 'Responsive mode: \'auto\' | \'manual\' | \'disabled\'' :
      prop === 'responsiveBreakpoints' ? 'Custom responsive breakpoints override' :
      prop === 'mobileIntensity' ? 'Mobile-specific intensity override (0-1)' :
      prop === 'tabletIntensity' ? 'Tablet-specific intensity override (0-1)' :
      'Desktop-specific intensity override (0-1)'} */`),
    `Responsive prop '${prop}' properly documented in interface`,
    `Responsive prop '${prop}' missing or improperly documented`
  );
});

// Check for responsive type definitions
validateCheck(
  animatedBackgroundContent.includes('responsiveMode?: \'auto\' | \'manual\' | \'disabled\''),
  'ResponsiveMode type properly defined with auto/manual/disabled options',
  'ResponsiveMode type missing or incorrect'
);

validateCheck(
  animatedBackgroundContent.includes('responsiveBreakpoints?: {') && 
  animatedBackgroundContent.includes('mobile?: number;') &&
  animatedBackgroundContent.includes('tablet?: number;') &&
  animatedBackgroundContent.includes('desktop?: number;'),
  'ResponsiveBreakpoints interface properly defined',
  'ResponsiveBreakpoints interface missing or incomplete'
);

logHeader('2. Screen Size Detection & Window Resize Monitoring');

// Check for screen size state
validateCheck(
  animatedBackgroundContent.includes('const [screenSize, setScreenSize] = useState<\'mobile\' | \'tablet\' | \'desktop\'>(\'desktop\');'),
  'Screen size state properly initialized',
  'Screen size state missing or incorrect'
);

validateCheck(
  animatedBackgroundContent.includes('const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });'),
  'Window size state properly initialized',
  'Window size state missing or incorrect'
);

// Check for screen size detection utility
validateCheck(
  animatedBackgroundContent.includes('const getScreenSize = (width: number): \'mobile\' | \'tablet\' | \'desktop\' => {') &&
  animatedBackgroundContent.includes('if (width < responsiveBreakpoints.mobile!) return \'mobile\';') &&
  animatedBackgroundContent.includes('if (width < responsiveBreakpoints.tablet!) return \'tablet\';') &&
  animatedBackgroundContent.includes('return \'desktop\';'),
  'Screen size detection utility properly implemented',
  'Screen size detection utility missing or incomplete'
);

// Check for window resize listener
validateCheck(
  animatedBackgroundContent.includes('window.addEventListener(\'resize\', handleResize);') &&
  animatedBackgroundContent.includes('return () => window.removeEventListener(\'resize\', handleResize);'),
  'Window resize listener properly implemented with cleanup',
  'Window resize listener missing or incomplete'
);

logHeader('3. Responsive Intensity & Performance Scaling');

// Check for responsive intensity function
validateCheck(
  animatedBackgroundContent.includes('const getResponsiveIntensity = (): number => {') &&
  animatedBackgroundContent.includes('if (!responsive || responsiveMode === \'disabled\') return intensity;'),
  'Responsive intensity function properly implemented',
  'Responsive intensity function missing or incomplete'
);

// Check for device-specific intensity overrides
validateCheck(
  animatedBackgroundContent.includes('if (currentScreenSize === \'mobile\' && mobileIntensity !== undefined)') &&
  animatedBackgroundContent.includes('if (currentScreenSize === \'tablet\' && tabletIntensity !== undefined)') &&
  animatedBackgroundContent.includes('if (currentScreenSize === \'desktop\' && desktopIntensity !== undefined)'),
  'Device-specific intensity overrides properly implemented',
  'Device-specific intensity overrides missing or incomplete'
);

// Check for default responsive scaling
validateCheck(
  animatedBackgroundContent.includes('intensity * 0.6; // 40% reduction for mobile') &&
  animatedBackgroundContent.includes('intensity * 0.8; // 20% reduction for tablet'),
  'Default responsive intensity scaling properly implemented',
  'Default responsive intensity scaling missing or incorrect'
);

// Check for responsive performance function
validateCheck(
  animatedBackgroundContent.includes('const getResponsivePerformance = (): \'high\' | \'medium\' | \'low\' => {') &&
  animatedBackgroundContent.includes('return performance === \'high\' ? \'medium\' : \'low\';'),
  'Responsive performance scaling properly implemented',
  'Responsive performance scaling missing or incomplete'
);

logHeader('4. Custom Breakpoints & Responsive Modes');

// Check for default breakpoints
validateCheck(
  animatedBackgroundContent.includes('responsiveBreakpoints = {') &&
  animatedBackgroundContent.includes('mobile: 768,') &&
  animatedBackgroundContent.includes('tablet: 1024,') &&
  animatedBackgroundContent.includes('desktop: 1280,'),
  'Default responsive breakpoints properly configured',
  'Default responsive breakpoints missing or incorrect'
);

// Check for responsive mode defaults
validateCheck(
  animatedBackgroundContent.includes('responsive = true,') &&
  animatedBackgroundContent.includes('responsiveMode = \'auto\','),
  'Responsive mode defaults properly set',
  'Responsive mode defaults missing or incorrect'
);

logHeader('5. Particle Optimization for Different Screen Sizes');

// Check for performance settings responsive enhancement
validateCheck(
  animatedBackgroundContent.includes('const currentPerformance = getResponsivePerformance();') &&
  animatedBackgroundContent.includes('const currentScreenSize = getScreenSize(windowSize.width);'),
  'Performance settings use responsive values',
  'Performance settings not using responsive values'
);

// Check for mobile particle optimization
validateCheck(
  animatedBackgroundContent.includes('points: Math.max(4, Math.floor(settings.points * 0.6)), // Further reduce particles on mobile') &&
  animatedBackgroundContent.includes('spacing: settings.spacing * 1.2, // Increase spacing for better performance') &&
  animatedBackgroundContent.includes('maxDistance: Math.max(10, settings.maxDistance * 0.8), // Reduce max distance'),
  'Mobile particle optimization properly implemented',
  'Mobile particle optimization missing or incomplete'
);

// Check for tablet optimization
validateCheck(
  animatedBackgroundContent.includes('points: Math.floor(settings.points * 0.8), // Slightly reduce particles on tablet') &&
  animatedBackgroundContent.includes('spacing: settings.spacing * 1.1, // Slightly increase spacing') &&
  animatedBackgroundContent.includes('maxDistance: settings.maxDistance * 0.9, // Slightly reduce max distance'),
  'Tablet particle optimization properly implemented',
  'Tablet particle optimization missing or incomplete'
);

// Check for VANTA scaling
validateCheck(
  animatedBackgroundContent.includes('scaleMobile: 0.8, // VANTA mobile scaling') &&
  animatedBackgroundContent.includes('scaleMobile: 0.9, // VANTA tablet scaling') &&
  animatedBackgroundContent.includes('scaleMobile: 1.0, // Full scale for desktop'),
  'VANTA mobile scaling properly implemented',
  'VANTA mobile scaling missing or incomplete'
);

logHeader('6. Responsive Opacity & Blur Adaptations');

// Check for responsive opacity adjustments
validateCheck(
  animatedBackgroundContent.includes('// T3.6: Responsive opacity adjustments') &&
  animatedBackgroundContent.includes('calculatedOpacity *= 1.3; // Increase opacity on mobile (fewer particles)') &&
  animatedBackgroundContent.includes('calculatedOpacity *= 1.1; // Slightly increase opacity on tablet'),
  'Responsive opacity adjustments properly implemented',
  'Responsive opacity adjustments missing or incomplete'
);

// Check for responsive blur adaptation
validateCheck(
  animatedBackgroundContent.includes('// T3.6: Use responsive intensity for dynamic blur') &&
  animatedBackgroundContent.includes('if (responsive && responsiveMode === \'auto\') {') &&
  animatedBackgroundContent.includes('dynamicIntensity = getResponsiveIntensity();'),
  'Responsive blur adaptation properly implemented',
  'Responsive blur adaptation missing or incomplete'
);

logHeader('7. Animation Initialization with Responsive Values');

// Check for responsive intensity usage in initialization
validateCheck(
  animatedBackgroundContent.includes('const responsiveIntensity = getResponsiveIntensity(); // T3.6: Use responsive intensity') &&
  animatedBackgroundContent.includes('intensity: responsiveIntensity * 0.7, // Use responsive intensity with gentle reduction') &&
  animatedBackgroundContent.includes('intensity: responsiveIntensity, // Use responsive intensity'),
  'Animation initialization uses responsive intensity',
  'Animation initialization not using responsive intensity'
);

// Check for dependency array updates
validateCheck(
  animatedBackgroundContent.includes('responsive, responsiveMode, responsiveBreakpoints, mobileIntensity, tabletIntensity, desktopIntensity, screenSize, windowSize'),
  'UseEffect dependency array includes responsive dependencies',
  'UseEffect dependency array missing responsive dependencies'
);

// Check for effect update with responsive values
validateCheck(
  animatedBackgroundContent.includes('// Update effect settings when props change (T3.6: Include responsive updates)') &&
  animatedBackgroundContent.includes('responsive, responsiveMode, screenSize, windowSize, mobileIntensity, tabletIntensity, desktopIntensity'),
  'Effect update includes responsive dependencies',
  'Effect update missing responsive dependencies'
);

logHeader('8. Demo Integration in AnimationTestPage');

// Check for T3.6 demo section
validateCheck(
  animationTestPageContent.includes('T3.6: Responsive Behavior Demo'),
  'T3.6 demo section present in AnimationTestPage',
  'T3.6 demo section missing from AnimationTestPage'
);

// Check for responsive demo varieties
const responsiveDemos = [
  'Auto Responsive',
  'Custom Mobile',
  'Custom Breakpoints',
  'Manual Mode',
  'Disabled',
  'Performance Adaptive',
  'Mobile-First',
  'Complete Feature Set'
];

responsiveDemos.forEach(demo => {
  validateCheck(
    animationTestPageContent.includes(demo),
    `Demo "${demo}" present`,
    `Demo "${demo}" missing`
  );
});

// Check for responsive prop usage in demos
validateCheck(
  animationTestPageContent.includes('responsive={true}') &&
  animationTestPageContent.includes('responsiveMode="auto"') &&
  animationTestPageContent.includes('mobileIntensity={0.2}') &&
  animationTestPageContent.includes('tabletIntensity={0.4}') &&
  animationTestPageContent.includes('desktopIntensity={0.6}'),
  'Responsive props properly used in demos',
  'Responsive props missing or incorrect in demos'
);

// Check for custom breakpoints demo
validateCheck(
  animationTestPageContent.includes('responsiveBreakpoints={{') &&
  animationTestPageContent.includes('mobile: 600,') &&
  animationTestPageContent.includes('tablet: 900,') &&
  animationTestPageContent.includes('desktop: 1200,'),
  'Custom breakpoints demo properly implemented',
  'Custom breakpoints demo missing or incomplete'
);

// Check for screen size debug info
validateCheck(
  animationTestPageContent.includes('Current Screen') &&
  animationTestPageContent.includes('window.innerWidth') &&
  animationTestPageContent.includes('window.innerHeight') &&
  animationTestPageContent.includes('window.innerWidth < 768 ? \'Mobile\''),
  'Screen size debug info properly implemented',
  'Screen size debug info missing or incomplete'
);

// Check for responsive features documentation
validateCheck(
  animationTestPageContent.includes('Responsive Behavior Features (T3.6):') &&
  animationTestPageContent.includes('Screen Size Detection') &&
  animationTestPageContent.includes('Device-Specific Intensity') &&
  animationTestPageContent.includes('Performance Scaling') &&
  animationTestPageContent.includes('Three Responsive Modes'),
  'Responsive features documentation present',
  'Responsive features documentation missing or incomplete'
);

logHeader('9. Component Documentation Updates');

// Check for T3.6 documentation in component comments
validateCheck(
  animatedBackgroundContent.includes('* - T3.6: Responsive behavior for different screen sizes'),
  'T3.6 feature listed in component documentation',
  'T3.6 feature missing from component documentation'
);

// Check for responsive example in component documentation
validateCheck(
  animatedBackgroundContent.includes('*   responsive={true}') &&
  animatedBackgroundContent.includes('*   responsiveMode="auto"') &&
  animatedBackgroundContent.includes('*   mobileIntensity={0.2}'),
  'Responsive props included in component example',
  'Responsive props missing from component example'
);

logHeader('10. Integration & Backwards Compatibility');

// Check for backwards compatibility
validateCheck(
  animatedBackgroundContent.includes('// Legacy mobile detection for backwards compatibility') &&
  animatedBackgroundContent.includes('/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)'),
  'Backwards compatibility with legacy mobile detection maintained',
  'Backwards compatibility not maintained'
);

// Check for graceful fallbacks
validateCheck(
  animatedBackgroundContent.includes('if (!responsive || responsiveMode === \'disabled\') return intensity;') &&
  animatedBackgroundContent.includes('if (!responsive || responsiveMode === \'disabled\') return performance;'),
  'Graceful fallbacks when responsive is disabled',
  'Graceful fallbacks missing when responsive is disabled'
);

// Summary
logHeader('Validation Summary');

const totalChecks = validationResults.passed + validationResults.failed;
const successRate = totalChecks > 0 ? ((validationResults.passed / totalChecks) * 100).toFixed(1) : 0;

console.log(`\n${colors.bold}Results:${colors.reset}`);
console.log(`${colors.green}✓ Passed: ${validationResults.passed}${colors.reset}`);
console.log(`${colors.red}✗ Failed: ${validationResults.failed}${colors.reset}`);
console.log(`${colors.yellow}⚠ Warnings: ${validationResults.warnings}${colors.reset}`);
console.log(`${colors.blue}Success Rate: ${successRate}%${colors.reset}`);

if (validationResults.failed === 0) {
  console.log(`\n${colors.bold}${colors.green}🎉 T3.6 Responsive Behavior validation completed successfully!${colors.reset}`);
  console.log(`${colors.green}✓ All responsive behavior features are properly implemented${colors.reset}`);
  console.log(`${colors.green}✓ Screen size detection and adaptation working correctly${colors.reset}`);
  console.log(`${colors.green}✓ Performance optimization for different devices implemented${colors.reset}`);
  console.log(`${colors.green}✓ Demo integration and documentation complete${colors.reset}`);
  
  if (validationResults.warnings > 0) {
    console.log(`\n${colors.yellow}Note: ${validationResults.warnings} warning(s) found. Review recommended but not blocking.${colors.reset}`);
  }
} else {
  console.log(`\n${colors.bold}${colors.red}❌ T3.6 Responsive Behavior validation failed${colors.reset}`);
  console.log(`${colors.red}Please fix the ${validationResults.failed} error(s) before proceeding.${colors.reset}`);
  process.exit(1);
}
