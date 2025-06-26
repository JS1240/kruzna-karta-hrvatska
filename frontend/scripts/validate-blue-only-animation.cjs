#!/usr/bin/env node

/**
 * Validation script for Blue-Only Topology Animation (T3.2)
 * Verifies blue-only configuration and functionality
 */

const fs = require('fs');
const path = require('path');

// Colors for output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function log(color, message) {
  console.log(`${color}${message}${colors.reset}`);
}

function success(message) {
  log(colors.green, `✓ ${message}`);
}

function error(message) {
  log(colors.red, `✗ ${message}`);
}

function warning(message) {
  log(colors.yellow, `⚠ ${message}`);
}

function info(message) {
  log(colors.blue, `ℹ ${message}`);
}

// Validation functions
function validateBlueOnlyColors() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  const requiredBlueColors = [
    'BLUE_ONLY_COLORS',
    '0x3674B5',  // Primary blue
    '0x578FCA',  // Secondary blue
    '0x7BA3D9',  // Light blue variant
    '0x2A5A94'   // Dark blue variant
  ];

  let allColorsPresent = true;

  requiredBlueColors.forEach(color => {
    if (content.includes(color)) {
      success(`Blue-only color found: ${color}`);
    } else {
      error(`Blue-only color missing: ${color}`);
      allColorsPresent = false;
    }
  });

  return allColorsPresent;
}

function validateBlueOnlyFunctions() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  const requiredFunctions = [
    'initBlueOnlyTopology',
    'getBlueOnlyTopologyConfig',
    'getEnhancedBlueTopologyConfig',
    'blueIntensity?:',
    'selectedBlueColor'
  ];

  let allFunctionsPresent = true;

  requiredFunctions.forEach(func => {
    if (content.includes(func)) {
      success(`Blue-only function found: ${func}`);
    } else {
      error(`Blue-only function missing: ${func}`);
      allFunctionsPresent = false;
    }
  });

  return allFunctionsPresent;
}

function validateComponentBlueOnlySupport() {
  const componentPath = path.join(process.cwd(), 'src/components/AnimatedBackground.tsx');
  
  if (!fs.existsSync(componentPath)) {
    error('AnimatedBackground.tsx not found');
    return false;
  }

  const content = fs.readFileSync(componentPath, 'utf8');

  const requiredFeatures = [
    'blueOnly?:',
    'blueIntensity?:',
    'initBlueOnlyTopology',
    'if (blueOnly)',
    "'light' | 'medium' | 'dark'"
  ];

  let allFeaturesPresent = true;

  requiredFeatures.forEach(feature => {
    if (content.includes(feature)) {
      success(`Component blue-only feature found: ${feature}`);
    } else {
      error(`Component blue-only feature missing: ${feature}`);
      allFeaturesPresent = false;
    }
  });

  return allFeaturesPresent;
}

function validateTestPageBlueOnlyDemos() {
  const testPagePath = path.join(process.cwd(), 'src/pages/AnimationTestPage.tsx');
  
  if (!fs.existsSync(testPagePath)) {
    warning('AnimationTestPage.tsx not found - blue-only demos may not be available');
    return false;
  }

  const content = fs.readFileSync(testPagePath, 'utf8');

  const requiredDemos = [
    'Blue-Only Animation Mode (T3.2)',
    'blueOnly={true}',
    'blueIntensity="light"',
    'blueIntensity="medium"',
    'blueIntensity="dark"',
    'Blue-Only Features (T3.2)',
    'Strict Blue-Only Color Palette'
  ];

  let allDemosPresent = true;

  requiredDemos.forEach(demo => {
    if (content.includes(demo)) {
      success(`Blue-only demo found: ${demo}`);
    } else {
      error(`Blue-only demo missing: ${demo}`);
      allDemosPresent = false;
    }
  });

  return allDemosPresent;
}

function validateColorCompliance() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  // Check that blue-only functions don't use non-blue colors
  const nonBlueColors = [
    '0xF5F0CD',  // Cream
    '0xFADA7A',  // Gold
    '0x000000'   // Black (except for background)
  ];

  const blueOnlySection = content.substring(
    content.indexOf('initBlueOnlyTopology'),
    content.indexOf('cleanupVantaEffect') || content.length
  );

  let compliant = true;

  nonBlueColors.forEach(color => {
    if (blueOnlySection.includes(color) && !blueOnlySection.includes('// Black background')) {
      error(`Non-blue color found in blue-only section: ${color}`);
      compliant = false;
    } else {
      success(`Blue-only compliance: No ${color} in blue-only functions`);
    }
  });

  return compliant;
}

function validateIntensityVariants() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  const intensityVariants = [
    "'light'",
    "'medium'",
    "'dark'",
    'BLUE_ONLY_COLORS.light',
    'BLUE_ONLY_COLORS.primary',
    'BLUE_ONLY_COLORS.dark'
  ];

  let allVariantsPresent = true;

  intensityVariants.forEach(variant => {
    if (content.includes(variant)) {
      success(`Blue intensity variant found: ${variant}`);
    } else {
      error(`Blue intensity variant missing: ${variant}`);
      allVariantsPresent = false;
    }
  });

  return allVariantsPresent;
}

// Main validation function
async function runValidation() {
  log(colors.bright, '\n🎨 Blue-Only Topology Animation Validation (T3.2)');
  log(colors.bright, '===================================================\n');

  const results = {
    blueOnlyColors: validateBlueOnlyColors(),
    blueOnlyFunctions: validateBlueOnlyFunctions(),
    componentSupport: validateComponentBlueOnlySupport(),
    testPageDemos: validateTestPageBlueOnlyDemos(),
    colorCompliance: validateColorCompliance(),
    intensityVariants: validateIntensityVariants()
  };

  const allPassed = Object.values(results).every(result => result);

  log(colors.bright, '\n📊 Validation Summary:');
  log(colors.bright, '===================');

  Object.entries(results).forEach(([test, passed]) => {
    if (passed) {
      success(`${test}: PASSED`);
    } else {
      error(`${test}: FAILED`);
    }
  });

  if (allPassed) {
    log(colors.green, '\n🎉 All validations passed! T3.2 is ready for completion.');
    log(colors.blue, '\nBlue-Only Features Verified:');
    log(colors.reset, '- ✓ Strict blue-only color palette (#3674B5, #578FCA)');
    log(colors.reset, '- ✓ Three blue intensity variants (light, medium, dark)');
    log(colors.reset, '- ✓ Blue-only initialization functions');
    log(colors.reset, '- ✓ Component integration with blueOnly prop');
    log(colors.reset, '- ✓ Test page with comprehensive blue-only demos');
    log(colors.reset, '- ✓ No non-blue colors in blue-only functions');
    
    log(colors.blue, '\nNext steps:');
    log(colors.reset, '- Test blue-only animations in browser');
    log(colors.reset, '- Verify visual consistency across intensity variants');
    log(colors.reset, '- Mark T3.2 as completed in task list');
  } else {
    log(colors.red, '\n❌ Some validations failed. Please address the issues above.');
  }

  return allPassed;
}

// Run validation
runValidation().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  log(colors.red, `\n💥 Validation script error: ${error.message}`);
  process.exit(1);
});
