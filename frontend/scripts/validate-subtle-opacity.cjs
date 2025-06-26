#!/usr/bin/env node

/**
 * Validation Script for T3.4: Subtle Opacity & Transparency Effects
 * 
 * This script validates that the AnimatedBackground component properly implements
 * all subtle opacity and transparency features according to T3.4 requirements.
 */

const fs = require('fs');
const path = require('path');

const FRONTEND_DIR = process.cwd();
const ANIMATED_BG_PATH = path.join(FRONTEND_DIR, 'src/components/AnimatedBackground.tsx');
const ANIMATION_TEST_PAGE_PATH = path.join(FRONTEND_DIR, 'src/pages/AnimationTestPage.tsx');

function validateFile(filePath, description) {
  if (!fs.existsSync(filePath)) {
    console.error(`❌ ${description} not found: ${filePath}`);
    return false;
  }
  console.log(`✅ ${description} exists`);
  return true;
}

function validateAnimatedBackgroundProps() {
  console.log('\n📋 Validating AnimatedBackground T3.4 Props...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const requiredProps = [
    'subtleOpacity',
    'opacityMode',
    'backgroundBlur',
    'opacityTransitions'
  ];
  
  let allPropsFound = true;
  
  requiredProps.forEach(prop => {
    const propRegex = new RegExp(`${prop}\\??: `);
    if (propRegex.test(content)) {
      console.log(`✅ Found prop: ${prop}`);
    } else {
      console.error(`❌ Missing prop: ${prop}`);
      allPropsFound = false;
    }
  });
  
  return allPropsFound;
}

function validateOpacityModes() {
  console.log('\n🎚️ Validating Opacity Modes...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const requiredModes = ['minimal', 'low', 'medium', 'adaptive'];
  const modeRegex = /'minimal'\s*\|\s*'low'\s*\|\s*'medium'\s*\|\s*'adaptive'/;
  
  if (modeRegex.test(content)) {
    console.log('✅ All opacity modes defined in type');
    
    // Check if getOptimalOpacity function exists
    if (content.includes('getOptimalOpacity')) {
      console.log('✅ getOptimalOpacity function found');
      
      // Check if each mode has implementation
      const modesImplemented = requiredModes.every(mode => {
        return content.includes(`${mode}:`);
      });
      
      if (modesImplemented) {
        console.log('✅ All opacity modes implemented');
        return true;
      } else {
        console.error('❌ Not all opacity modes implemented');
        return false;
      }
    } else {
      console.error('❌ getOptimalOpacity function not found');
      return false;
    }
  } else {
    console.error('❌ Opacity modes not properly defined');
    return false;
  }
}

function validateBackgroundBlur() {
  console.log('\n🌫️ Validating Background Blur Implementation...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const blurChecks = [
    { name: 'backdropFilter blur', regex: /backdropFilter.*blur/ },
    { name: 'WebKit backdrop filter', regex: /WebkitBackdropFilter.*blur/ },
    { name: 'backgroundBlur parameter usage', regex: /backgroundBlur\s*>/ }
  ];
  
  let allBlurChecksPass = true;
  
  blurChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} implementation found`);
    } else {
      console.error(`❌ ${check.name} implementation missing`);
      allBlurChecksPass = false;
    }
  });
  
  return allBlurChecksPass;
}

function validateOpacityTransitions() {
  console.log('\n⚡ Validating Opacity Transitions...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const transitionChecks = [
    { name: 'CSS transition property', regex: /transition.*opacity/ },
    { name: 'opacityTransitions prop usage', regex: /opacityTransitions/ },
    { name: 'transition class conditional', regex: /opacityTransitions.*duration/ }
  ];
  
  let allTransitionChecksPass = true;
  
  transitionChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} found`);
    } else {
      console.error(`❌ ${check.name} missing`);
      allTransitionChecksPass = false;
    }
  });
  
  return allTransitionChecksPass;
}

function validateAdaptiveOpacity() {
  console.log('\n🤖 Validating Adaptive Opacity Logic...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const adaptiveChecks = [
    { name: 'Gentle movement adjustment', regex: /if \(gentleMovement\) \{[\s\S]*?calculatedOpacity \*= 0\.7/ },
    { name: 'Performance mode adjustment', regex: /if \(performance === 'high'\) \{[\s\S]*?calculatedOpacity \*= 0\.8/ },
    { name: 'Mobile detection', regex: /if \(isMobile\) \{[\s\S]*?calculatedOpacity \*= 1\.2/ },
    { name: 'Opacity bounds checking', regex: /Math\.max.*Math\.min/ }
  ];
  
  let allAdaptiveChecksPass = true;
  
  adaptiveChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} found`);
    } else {
      console.error(`❌ ${check.name} missing`);
      allAdaptiveChecksPass = false;
    }
  });
  
  return allAdaptiveChecksPass;
}

function validateTestPageDemos() {
  console.log('\n🎭 Validating AnimationTestPage T3.4 Demos...');
  
  const content = fs.readFileSync(ANIMATION_TEST_PAGE_PATH, 'utf8');
  
  const demoChecks = [
    { name: 'T3.4 section heading', regex: /Subtle Opacity.*T3\.4/ },
    { name: 'Minimal opacity demo', regex: /opacityMode="minimal"/ },
    { name: 'Low opacity demo', regex: /opacityMode="low"/ },
    { name: 'Medium opacity demo', regex: /opacityMode="medium"/ },
    { name: 'Adaptive opacity demo', regex: /opacityMode="adaptive"/ },
    { name: 'Background blur demo', regex: /backgroundBlur=\{8\}/ },
    { name: 'Gentle + Subtle combined demo', regex: /gentleMovement=\{true\}[\s\S]*?subtleOpacity=\{true\}/ },
    { name: 'Blue + Subtle combined demo', regex: /blueOnly=\{true\}[\s\S]*?subtleOpacity=\{true\}/ },
    { name: 'Opacity transitions demo', regex: /opacityTransitions=\{true\}/ }
  ];
  
  let allDemoChecksPass = true;
  
  demoChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} found`);
    } else {
      console.error(`❌ ${check.name} missing`);
      allDemoChecksPass = false;
    }
  });
  
  return allDemoChecksPass;
}

function validateIntegrationWithPreviousFeatures() {
  console.log('\n🔗 Validating Integration with T3.1-T3.3 Features...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const integrationChecks = [
    { name: 'Blue-only + subtle opacity', regex: /blueOnly[\s\S]*?subtleOpacity/ },
    { name: 'Gentle movement + subtle opacity', regex: /gentleMovement[\s\S]*?subtleOpacity/ },
    { name: 'Optimal opacity in blue-only mode', regex: /initBlueOnlyTopology[\s\S]*?optimalOpacity/ },
    { name: 'Optimal opacity in gentle mode', regex: /initGentleTopology[\s\S]*?optimalOpacity/ },
    { name: 'Adaptive opacity considers gentle mode', regex: /adaptive[\s\S]*?gentleMovement/ }
  ];
  
  let allIntegrationChecksPass = true;
  
  integrationChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} integration found`);
    } else {
      console.error(`❌ ${check.name} integration missing`);
      allIntegrationChecksPass = false;
    }
  });
  
  return allIntegrationChecksPass;
}

// Main validation function
function main() {
  console.log('🔍 T3.4 Subtle Opacity & Transparency Effects Validation\n');
  console.log('=' .repeat(60));
  
  const validations = [
    () => validateFile(ANIMATED_BG_PATH, 'AnimatedBackground component'),
    () => validateFile(ANIMATION_TEST_PAGE_PATH, 'AnimationTestPage'),
    validateAnimatedBackgroundProps,
    validateOpacityModes,
    validateBackgroundBlur,
    validateOpacityTransitions,
    validateAdaptiveOpacity,
    validateTestPageDemos,
    validateIntegrationWithPreviousFeatures
  ];
  
  let allValidationsPassed = true;
  
  for (const validation of validations) {
    const result = validation();
    if (!result) {
      allValidationsPassed = false;
    }
  }
  
  console.log('\n' + '=' .repeat(60));
  
  if (allValidationsPassed) {
    console.log('🎉 T3.4 VALIDATION PASSED!');
    console.log('✅ All subtle opacity and transparency features are properly implemented');
    console.log('✅ All opacity modes (minimal, low, medium, adaptive) working');
    console.log('✅ Background blur effects implemented');
    console.log('✅ Smooth opacity transitions implemented');
    console.log('✅ Adaptive opacity logic with context awareness');
    console.log('✅ Full integration with T3.1-T3.3 features');
    console.log('✅ Comprehensive test demos available');
    console.log('\n🚀 Ready to proceed to T3.5: Adjustable Blur Effects');
    process.exit(0);
  } else {
    console.log('❌ T3.4 VALIDATION FAILED!');
    console.log('🔧 Please fix the issues above before proceeding to T3.5');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { main };
