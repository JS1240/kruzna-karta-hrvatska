#!/usr/bin/env node

/**
 * Validation script for AnimatedBackground component (T3.1)
 * Verifies the component structure, dependencies, and integration
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
function validateFiles() {
  const requiredFiles = [
    'src/components/AnimatedBackground.tsx',
    'src/utils/vantaUtils.ts',
    'src/utils/animationUtils.ts',
    'src/types/vanta.d.ts',
    'docs/AnimatedBackground.md'
  ];

  let allFilesExist = true;

  requiredFiles.forEach(file => {
    const filePath = path.join(process.cwd(), file);
    if (fs.existsSync(filePath)) {
      success(`Required file exists: ${file}`);
    } else {
      error(`Missing required file: ${file}`);
      allFilesExist = false;
    }
  });

  return allFilesExist;
}

function validateDependencies() {
  const packageJsonPath = path.join(process.cwd(), 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    error('package.json not found');
    return false;
  }

  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };

  const requiredDeps = {
    'vanta': '0.5.24',
    'three': '0.177.0',
    '@types/three': '0.177.0'
  };

  let allDepsPresent = true;

  Object.entries(requiredDeps).forEach(([dep, version]) => {
    if (deps[dep]) {
      success(`Dependency found: ${dep}@${deps[dep]}`);
    } else {
      error(`Missing dependency: ${dep}@${version}`);
      allDepsPresent = false;
    }
  });

  return allDepsPresent;
}

function validateComponentStructure() {
  const componentPath = path.join(process.cwd(), 'src/components/AnimatedBackground.tsx');
  
  if (!fs.existsSync(componentPath)) {
    error('AnimatedBackground.tsx not found');
    return false;
  }

  const content = fs.readFileSync(componentPath, 'utf8');

  const requiredElements = [
    'AnimatedBackgroundProps',
    'useRef',
    'useEffect',
    'useState',
    'initVantaTopology',
    'cleanupVantaEffect',
    'prefers-reduced-motion',
    'performance?:',
    'respectReducedMotion?:',
    'aria-hidden="true"'
  ];

  let allElementsPresent = true;

  requiredElements.forEach(element => {
    if (content.includes(element)) {
      success(`Component includes: ${element}`);
    } else {
      error(`Component missing: ${element}`);
      allElementsPresent = false;
    }
  });

  return allElementsPresent;
}

function validateVantaUtils() {
  const utilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(utilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(utilsPath, 'utf8');

  const requiredElements = [
    'VantaTopologyConfig',
    'BRAND_COLORS',
    'initVantaTopology',
    'cleanupVantaEffect',
    'TopologyInitOptions',
    'prefers-reduced-motion',
    'THREE'
  ];

  let allElementsPresent = true;

  requiredElements.forEach(element => {
    if (content.includes(element)) {
      success(`VantaUtils includes: ${element}`);
    } else {
      error(`VantaUtils missing: ${element}`);
      allElementsPresent = false;
    }
  });

  return allElementsPresent;
}

function validateTestPage() {
  const testPagePath = path.join(process.cwd(), 'src/pages/AnimationTestPage.tsx');
  
  if (!fs.existsSync(testPagePath)) {
    warning('AnimationTestPage.tsx not found - component demos may not be available');
    return false;
  }

  const content = fs.readFileSync(testPagePath, 'utf8');

  if (content.includes('AnimatedBackground')) {
    success('AnimatedBackground is integrated in test page');
    return true;
  } else {
    warning('AnimatedBackground not found in test page');
    return false;
  }
}

function validateBrandColors() {
  const colorUtilsPath = path.join(process.cwd(), 'src/utils/colorUtils.ts');
  
  if (!fs.existsSync(colorUtilsPath)) {
    error('colorUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(colorUtilsPath, 'utf8');

  const brandColors = [
    '#3674B5',  // Primary blue
    '#578FCA'   // Secondary blue
  ];

  let allColorsPresent = true;

  brandColors.forEach(color => {
    if (content.includes(color)) {
      success(`Brand color defined: ${color}`);
    } else {
      error(`Brand color missing: ${color}`);
      allColorsPresent = false;
    }
  });

  return allColorsPresent;
}

// Main validation function
async function runValidation() {
  log(colors.bright, '\n🎨 AnimatedBackground Component Validation (T3.1)');
  log(colors.bright, '================================================\n');

  const results = {
    files: validateFiles(),
    dependencies: validateDependencies(),
    component: validateComponentStructure(),
    vantaUtils: validateVantaUtils(),
    testPage: validateTestPage(),
    brandColors: validateBrandColors()
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
    log(colors.green, '\n🎉 All validations passed! T3.1 is ready for completion.');
    log(colors.blue, '\nNext steps:');
    log(colors.reset, '- Test the component in development environment');
    log(colors.reset, '- Verify animations work in browsers');
    log(colors.reset, '- Check accessibility features');
    log(colors.reset, '- Mark T3.1 as completed in task list');
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
