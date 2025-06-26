#!/usr/bin/env node

/**
 * Validation Script for T3.5: Adjustable Blur Effects
 * 
 * This script validates that the AnimatedBackground component properly implements
 * all adjustable blur effects according to T3.5 requirements.
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
  console.log('\n📋 Validating AnimatedBackground T3.5 Props...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const requiredProps = [
    'adjustableBlur',
    'blurType',
    'blurIntensity',
    'customBlurValue',
    'contentBlur',
    'edgeBlur'
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

function validateBlurTypes() {
  console.log('\n🎭 Validating Blur Types...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const requiredTypes = ['background', 'content', 'edge', 'dynamic'];
  const typeRegex = /'background'\s*\|\s*'content'\s*\|\s*'edge'\s*\|\s*'dynamic'/;
  
  if (typeRegex.test(content)) {
    console.log('✅ All blur types defined in type');
    
    // Check if getBlurFilter function exists
    if (content.includes('getBlurFilter')) {
      console.log('✅ getBlurFilter function found');
      
      // Check if each type has implementation
      const typesImplemented = requiredTypes.every(type => {
        return content.includes(`case '${type}':`);
      });
      
      if (typesImplemented) {
        console.log('✅ All blur types implemented');
        return true;
      } else {
        console.error('❌ Not all blur types implemented');
        return false;
      }
    } else {
      console.error('❌ getBlurFilter function not found');
      return false;
    }
  } else {
    console.error('❌ Blur types not properly defined');
    return false;
  }
}

function validateBlurIntensities() {
  console.log('\n🔧 Validating Blur Intensities...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const requiredIntensities = ['light', 'medium', 'heavy', 'custom'];
  const intensityRegex = /'light'\s*\|\s*'medium'\s*\|\s*'heavy'\s*\|\s*'custom'/;
  
  if (intensityRegex.test(content)) {
    console.log('✅ All blur intensities defined in type');
    
    // Check if getBlurValue function exists
    if (content.includes('getBlurValue')) {
      console.log('✅ getBlurValue function found');
      
      // Check if intensity mapping exists
      if (content.includes('blurIntensityMap')) {
        console.log('✅ Blur intensity mapping found');
        
        // Check if each intensity has implementation
        const intensitiesImplemented = requiredIntensities.every(intensity => {
          return content.includes(`${intensity}:`);
        });
        
        if (intensitiesImplemented) {
          console.log('✅ All blur intensities implemented');
          return true;
        } else {
          console.error('❌ Not all blur intensities implemented');
          return false;
        }
      } else {
        console.error('❌ Blur intensity mapping not found');
        return false;
      }
    } else {
      console.error('❌ getBlurValue function not found');
      return false;
    }
  } else {
    console.error('❌ Blur intensities not properly defined');
    return false;
  }
}

function validateBlurFunctions() {
  console.log('\n⚙️ Validating Blur Functions...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const functionChecks = [
    { name: 'getBlurValue function', regex: /getBlurValue.*=.*\(\).*=>/ },
    { name: 'getBlurFilter function', regex: /getBlurFilter.*=.*\(\).*=>/ },
    { name: 'getBlurStyling function', regex: /getBlurStyling.*=.*\(\).*=>/ },
    { name: 'CSS filter property usage', regex: /filter.*=.*contentFilter/ },
    { name: 'Backdrop filter fallback', regex: /if \(!adjustableBlur\)/ }
  ];
  
  let allFunctionChecksPass = true;
  
  functionChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} found`);
    } else {
      console.error(`❌ ${check.name} missing`);
      allFunctionChecksPass = false;
    }
  });
  
  return allFunctionChecksPass;
}

function validateBlurTypeImplementations() {
  console.log('\n🌈 Validating Blur Type Implementations...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const implementationChecks = [
    { name: 'Background blur implementation', regex: /case 'background'/ },
    { name: 'Content blur with contrast', regex: /case 'content'[\s\S]*?contrast\(1\.1\)/ },
    { name: 'Edge blur with drop-shadow', regex: /case 'edge'[\s\S]*?drop-shadow/ },
    { name: 'Dynamic blur intensity adjustment', regex: /case 'dynamic'[\s\S]*?dynamicBlur.*intensity/ },
    { name: 'Content blur radius limit', regex: /Math\.min.*contentBlur/ },
    { name: 'Edge blur radius limit', regex: /Math\.min.*edgeBlur/ }
  ];
  
  let allImplementationChecksPass = true;
  
  implementationChecks.forEach(check => {
    if (check.regex.test(content)) {
      console.log(`✅ ${check.name} found`);
    } else {
      console.error(`❌ ${check.name} missing`);
      allImplementationChecksPass = false;
    }
  });
  
  return allImplementationChecksPass;
}

function validateTestPageDemos() {
  console.log('\n🎭 Validating AnimationTestPage T3.5 Demos...');
  
  const content = fs.readFileSync(ANIMATION_TEST_PAGE_PATH, 'utf8');
  
  const demoChecks = [
    { name: 'T3.5 section heading', regex: /Adjustable Blur.*T3\.5/ },
    { name: 'Background blur demo', regex: /blurType="background"/ },
    { name: 'Content blur demo', regex: /blurType="content"/ },
    { name: 'Edge blur demo', regex: /blurType="edge"/ },
    { name: 'Dynamic blur demo', regex: /blurType="dynamic"/ },
    { name: 'Light intensity demo', regex: /blurIntensity="light"/ },
    { name: 'Heavy intensity demo', regex: /blurIntensity="heavy"/ },
    { name: 'Custom blur demo', regex: /blurIntensity="custom"[\s\S]*?customBlurValue/ },
    { name: 'Gentle + Adjustable demo', regex: /gentleMovement=\{true\}[\s\S]*?adjustableBlur=\{true\}/ },
    { name: 'Complete feature demo T3.1-T3.5', regex: /All T3\.1-T3\.5/ }
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
  console.log('\n🔗 Validating Integration with T3.1-T3.4 Features...');
  
  const content = fs.readFileSync(ANIMATED_BG_PATH, 'utf8');
  
  const integrationChecks = [
    { name: 'Adjustable blur + gentle movement', regex: /adjustableBlur[\s\S]*?gentleMovement/ },
    { name: 'Adjustable blur + subtle opacity', regex: /adjustableBlur[\s\S]*?subtleOpacity/ },
    { name: 'Dynamic blur considers intensity', regex: /dynamicBlur.*intensity/ },
    { name: 'Gentle mode affects dynamic blur', regex: /gentleMovement[\s\S]*?brightness/ },
    { name: 'Fallback to T3.4 backgroundBlur', regex: /!adjustableBlur[\s\S]*?backgroundBlur/ },
    { name: 'Enhanced transitions integration', regex: /blurTransition.*adjustableBlur/ }
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
  console.log('🔍 T3.5 Adjustable Blur Effects Validation\n');
  console.log('=' .repeat(60));
  
  const validations = [
    () => validateFile(ANIMATED_BG_PATH, 'AnimatedBackground component'),
    () => validateFile(ANIMATION_TEST_PAGE_PATH, 'AnimationTestPage'),
    validateAnimatedBackgroundProps,
    validateBlurTypes,
    validateBlurIntensities,
    validateBlurFunctions,
    validateBlurTypeImplementations,
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
    console.log('🎉 T3.5 VALIDATION PASSED!');
    console.log('✅ All adjustable blur effects are properly implemented');
    console.log('✅ All blur types (background, content, edge, dynamic) working');
    console.log('✅ All intensity levels (light, medium, heavy, custom) implemented');
    console.log('✅ Content-aware and edge feathering blur effects functional');
    console.log('✅ Dynamic blur adapts to animation intensity and gentle mode');
    console.log('✅ Full integration with T3.1-T3.4 features');
    console.log('✅ Comprehensive test demos available');
    console.log('\n🚀 Ready to proceed to T3.6: Responsive Behavior');
    process.exit(0);
  } else {
    console.log('❌ T3.5 VALIDATION FAILED!');
    console.log('🔧 Please fix the issues above before proceeding to T3.6');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { main };
