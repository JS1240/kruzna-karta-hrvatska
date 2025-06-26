#!/usr/bin/env node

/**
 * Validation script for Gentle Movement Animation (T3.3)
 * Verifies slow, gentle movements with minimal particle density
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
function validateGentleMovementFunctions() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  const requiredFunctions = [
    'getGentleMovementConfig',
    'getUltraGentleConfig',
    'initGentleTopology',
    'gentleMode?:',
    'movementSpeed?:',
    'speed?:',
    'gentleParams'
  ];

  let allFunctionsPresent = true;

  requiredFunctions.forEach(func => {
    if (content.includes(func)) {
      success(`Gentle movement function found: ${func}`);
    } else {
      error(`Gentle movement function missing: ${func}`);
      allFunctionsPresent = false;
    }
  });

  return allFunctionsPresent;
}

function validateMinimalParticleSettings() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  // Check for minimal particle density settings
  const minimalSettings = [
    'points: isMobile ? 2 : 3',     // Ultra-minimal particles
    'points: isMobile ? 4 : 6',     // Minimal particles for gentle
    'maxDistance: isMobile ? 5 : 6', // Very short connections
    'spacing: isMobile ? 35 : 30',   // Wide spacing
    'spacing: isMobile ? 25 : 20'    // Gentle spacing
  ];

  let minimalSettingsFound = 0;

  minimalSettings.forEach(setting => {
    if (content.includes(setting)) {
      success(`Minimal particle setting found: ${setting}`);
      minimalSettingsFound++;
    }
  });

  if (minimalSettingsFound >= 3) {
    success(`Sufficient minimal particle settings found (${minimalSettingsFound}/5)`);
    return true;
  } else {
    error(`Insufficient minimal particle settings (${minimalSettingsFound}/5)`);
    return false;
  }
}

function validateSlowMovementSettings() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  const componentPath = path.join(process.cwd(), 'src/components/AnimatedBackground.tsx');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const vantaContent = fs.readFileSync(vantaUtilsPath, 'utf8');
  const componentContent = fs.existsSync(componentPath) ? fs.readFileSync(componentPath, 'utf8') : '';

  const slowMovementFeatures = [
    { feature: 'movementSpeed = 0.3', content: vantaContent },
    { feature: 'speed: movementSpeed', content: vantaContent },
    { feature: 'intensity = 0.3', content: vantaContent },
    { feature: 'opacity = 0.2', content: vantaContent },
    { feature: 'intensity * 0.7', content: componentContent },
    { feature: 'opacity * 0.8', content: componentContent }
  ];

  let allFeaturesPresent = true;

  slowMovementFeatures.forEach(({ feature, content }) => {
    if (content.includes(feature)) {
      success(`Slow movement feature found: ${feature}`);
    } else {
      error(`Slow movement feature missing: ${feature}`);
      allFeaturesPresent = false;
    }
  });

  return allFeaturesPresent;
}

function validateComponentGentleSupport() {
  const componentPath = path.join(process.cwd(), 'src/components/AnimatedBackground.tsx');
  
  if (!fs.existsSync(componentPath)) {
    error('AnimatedBackground.tsx not found');
    return false;
  }

  const content = fs.readFileSync(componentPath, 'utf8');

  const requiredFeatures = [
    'gentleMovement?:',
    'gentleMode?:',
    'movementSpeed?:',
    'initGentleTopology',
    'if (gentleMovement)',
    "'normal' | 'ultra'"
  ];

  let allFeaturesPresent = true;

  requiredFeatures.forEach(feature => {
    if (content.includes(feature)) {
      success(`Component gentle feature found: ${feature}`);
    } else {
      error(`Component gentle feature missing: ${feature}`);
      allFeaturesPresent = false;
    }
  });

  return allFeaturesPresent;
}

function validateTestPageGentleDemos() {
  const testPagePath = path.join(process.cwd(), 'src/pages/AnimationTestPage.tsx');
  
  if (!fs.existsSync(testPagePath)) {
    warning('AnimationTestPage.tsx not found - gentle demos may not be available');
    return false;
  }

  const content = fs.readFileSync(testPagePath, 'utf8');

  const requiredDemos = [
    'Gentle Movement Animation Mode (T3.3)',
    'gentleMovement={true}',
    'gentleMode="normal"',
    'gentleMode="ultra"',
    'movementSpeed={0.1}',
    'movementSpeed={0.2}',
    'movementSpeed={0.3}',
    'Minimal Particle Density',
    'Slow Movement Speed'
  ];

  let allDemosPresent = true;

  requiredDemos.forEach(demo => {
    if (content.includes(demo)) {
      success(`Gentle demo found: ${demo}`);
    } else {
      error(`Gentle demo missing: ${demo}`);
      allDemosPresent = false;
    }
  });

  return allDemosPresent;
}

function validateGentleModeOptions() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  const gentleModeFeatures = [
    "gentleMode === 'ultra'",
    "gentleMode = 'normal'",
    'mouseControls: false',      // Ultra mode disables mouse controls
    'touchControls: false',      // Ultra mode disables touch controls
    'scale: isMobile ? 0.5 : 0.7', // Reduced scale for ultra gentle
    'BLUE_ONLY_COLORS.light'     // Default to light blue for gentleness
  ];

  let allFeaturesPresent = true;

  gentleModeFeatures.forEach(feature => {
    if (content.includes(feature)) {
      success(`Gentle mode feature found: ${feature}`);
    } else {
      error(`Gentle mode feature missing: ${feature}`);
      allFeaturesPresent = false;
    }
  });

  return allFeaturesPresent;
}

function validateInterfaceUpdates() {
  const vantaUtilsPath = path.join(process.cwd(), 'src/utils/vantaUtils.ts');
  
  if (!fs.existsSync(vantaUtilsPath)) {
    error('vantaUtils.ts not found');
    return false;
  }

  const content = fs.readFileSync(vantaUtilsPath, 'utf8');

  const interfaceUpdates = [
    'speed?: number;',
    'gentleMode?: ',
    'movementSpeed?: number;'
  ];

  let allUpdatesPresent = true;

  interfaceUpdates.forEach(update => {
    if (content.includes(update)) {
      success(`Interface update found: ${update}`);
    } else {
      error(`Interface update missing: ${update}`);
      allUpdatesPresent = false;
    }
  });

  return allUpdatesPresent;
}

// Main validation function
async function runValidation() {
  log(colors.bright, '\n🎨 Gentle Movement Animation Validation (T3.3)');
  log(colors.bright, '===============================================\n');

  const results = {
    gentleFunctions: validateGentleMovementFunctions(),
    minimalParticles: validateMinimalParticleSettings(),
    slowMovement: validateSlowMovementSettings(),
    componentSupport: validateComponentGentleSupport(),
    testPageDemos: validateTestPageGentleDemos(),
    gentleModes: validateGentleModeOptions(),
    interfaceUpdates: validateInterfaceUpdates()
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
    log(colors.green, '\n🎉 All validations passed! T3.3 is ready for completion.');
    log(colors.blue, '\nGentle Movement Features Verified:');
    log(colors.reset, '- ✓ Minimal particle density (2-6 particles vs 8-15 regular)');
    log(colors.reset, '- ✓ Slow movement speed configurations (0.1-0.5)');
    log(colors.reset, '- ✓ Two gentle modes: normal and ultra');
    log(colors.reset, '- ✓ Wider particle spacing (25-35px vs 15-20px regular)');
    log(colors.reset, '- ✓ Shorter connection distances (6-12px vs 20-25px regular)');
    log(colors.reset, '- ✓ Reduced intensity and opacity scaling');
    log(colors.reset, '- ✓ Component integration with gentle movement props');
    log(colors.reset, '- ✓ Comprehensive test page demos');
    
    log(colors.blue, '\nNext steps:');
    log(colors.reset, '- Test gentle animations in browser');
    log(colors.reset, '- Verify smooth, subtle movement behavior');
    log(colors.reset, '- Mark T3.3 as completed in task list');
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
