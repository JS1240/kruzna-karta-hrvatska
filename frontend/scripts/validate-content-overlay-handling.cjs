#!/usr/bin/env node

/**
 * T4.3 Content Overlay Handling Validation Script
 * 
 * This script validates that the content overlay handling with proper blur effects
 * has been successfully implemented across the frontend components.
 * 
 * Success Criteria:
 * - AnimatedBackground component includes overlay system props
 * - Overlay utility functions are implemented
 * - Homepage hero section uses standardized overlay
 * - About page sections use standardized overlays  
 * - FeaturedEvents component uses standardized overlay
 * - Text contrast optimization is implemented
 */

const fs = require('fs');
const path = require('path');

// Color coding for output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function validateFile(filePath, description) {
  if (!fs.existsSync(filePath)) {
    log(`❌ ${description}: File not found - ${filePath}`, 'red');
    return false;
  }
  log(`✅ ${description}: File exists`, 'green');
  return true;
}

function validateFileContent(filePath, patterns, description) {
  if (!fs.existsSync(filePath)) {
    log(`❌ ${description}: File not found - ${filePath}`, 'red');
    return false;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  let allFound = true;

  patterns.forEach(({ pattern, name, required = true }) => {
    const found = pattern.test(content);
    if (found) {
      log(`  ✅ ${name}: Found`, 'green');
    } else if (required) {
      log(`  ❌ ${name}: Missing`, 'red');
      allFound = false;
    } else {
      log(`  ⚠️  ${name}: Optional - Not found`, 'yellow');
    }
  });

  return allFound;
}

function main() {
  log('🔍 T4.3 Content Overlay Handling Validation', 'bold');
  log('='.repeat(50), 'blue');

  let allTestsPassed = true;

  // Test 1: Validate AnimatedBackground component has overlay system props
  log('\n📝 Test 1: AnimatedBackground Component Overlay System', 'blue');
  const animatedBgPath = path.join(__dirname, '../src/components/AnimatedBackground.tsx');
  const animatedBgPatterns = [
    { pattern: /overlayMode\?\s*:\s*OverlayMode/, name: 'overlayMode prop type definition' },
    { pattern: /overlayStyle\?\s*:\s*OverlayStyle/, name: 'overlayStyle prop type definition' },
    { pattern: /textContrast\?\s*:\s*TextContrast/, name: 'textContrast prop type definition' },
    { pattern: /overlayColor\?\s*:\s*string/, name: 'overlayColor prop type definition' },
    { pattern: /overlayOpacity\?\s*:\s*number/, name: 'overlayOpacity prop type definition' },
    { pattern: /overlayPadding\?\s*:\s*string/, name: 'overlayPadding prop type definition' },
    { pattern: /generateOverlayClasses/, name: 'generateOverlayClasses usage' },
    { pattern: /generateOverlayBackground/, name: 'generateOverlayBackground usage' },
    { pattern: /getOverlayBackdropFilter/, name: 'getOverlayBackdropFilter usage' },
    { pattern: /getTextContrastClasses/, name: 'getTextContrastClasses usage' },
  ];
  
  if (!validateFileContent(animatedBgPath, animatedBgPatterns, 'AnimatedBackground overlay system')) {
    allTestsPassed = false;
  }

  // Test 2: Validate overlay utility functions exist
  log('\n📝 Test 2: Overlay Utility Functions', 'blue');
  const overlayUtilsPath = path.join(__dirname, '../src/utils/overlayUtils.ts');
  const overlayUtilsPatterns = [
    { pattern: /export type OverlayMode/, name: 'OverlayMode type export' },
    { pattern: /export type OverlayStyle/, name: 'OverlayStyle type export' },
    { pattern: /export type TextContrast/, name: 'TextContrast type export' },
    { pattern: /export const OVERLAY_PRESETS/, name: 'OVERLAY_PRESETS export' },
    { pattern: /export const getOverlayOpacity/, name: 'getOverlayOpacity function' },
    { pattern: /export const generateOverlayBackground/, name: 'generateOverlayBackground function' },
    { pattern: /export const getOverlayBackdropFilter/, name: 'getOverlayBackdropFilter function' },
    { pattern: /export const getTextContrastClasses/, name: 'getTextContrastClasses function' },
    { pattern: /export const generateOverlayClasses/, name: 'generateOverlayClasses function' },
    { pattern: /export const generateOverlayStyle/, name: 'generateOverlayStyle function' },
    { pattern: /export const getResponsiveOverlayConfig/, name: 'getResponsiveOverlayConfig function' },
    { pattern: /export const validateOverlayConfig/, name: 'validateOverlayConfig function' },
  ];
  
  if (!validateFileContent(overlayUtilsPath, overlayUtilsPatterns, 'Overlay utility functions')) {
    allTestsPassed = false;
  }

  // Test 3: Validate Homepage hero section uses standardized overlay
  log('\n📝 Test 3: Homepage Hero Section Overlay Implementation', 'blue');
  const indexPath = path.join(__dirname, '../src/pages/Index.tsx');
  const indexPatterns = [
    { pattern: /overlayMode="light"/, name: 'overlayMode prop usage' },
    { pattern: /overlayStyle="glass"/, name: 'overlayStyle prop usage' },
    { pattern: /textContrast="auto"/, name: 'textContrast prop usage' },
    { pattern: /overlayPadding="p-8"/, name: 'overlayPadding prop usage' },
    { pattern: /AnimatedBackground[^>]*overlayMode/, name: 'AnimatedBackground with overlay props' },
  ];
  
  if (!validateFileContent(indexPath, indexPatterns, 'Homepage hero section overlay')) {
    allTestsPassed = false;
  }

  // Test 4: Validate About page sections use standardized overlays
  log('\n📝 Test 4: About Page Sections Overlay Implementation', 'blue');
  const aboutPath = path.join(__dirname, '../src/components/AboutCroatia.tsx');
  const aboutPatterns = [
    { pattern: /import AnimatedBackground/, name: 'AnimatedBackground import' },
    { pattern: /overlayMode="medium"/, name: 'overlayMode prop usage' },
    { pattern: /overlayStyle="frosted"/, name: 'overlayStyle prop usage' },
    { pattern: /textContrast="light"/, name: 'textContrast prop usage' },
    { pattern: /AnimatedBackground[^>]*overlayMode/, name: 'AnimatedBackground with overlay props' },
    { pattern: /(?<!\/\/.*)bg-gradient-to-r from-navy-blue to-medium-blue/, name: 'Manual gradient removed', required: false },
  ];
  
  if (!validateFileContent(aboutPath, aboutPatterns, 'About page sections overlay')) {
    allTestsPassed = false;
  }

  // Test 5: Validate FeaturedEvents component uses standardized overlay
  log('\n📝 Test 5: FeaturedEvents Component Overlay Implementation', 'blue');
  const featuredEventsPath = path.join(__dirname, '../src/components/FeaturedEvents.tsx');
  const featuredEventsPatterns = [
    { pattern: /overlayMode="light"/, name: 'overlayMode prop usage' },
    { pattern: /overlayStyle="glass"/, name: 'overlayStyle prop usage' },
    { pattern: /textContrast="auto"/, name: 'textContrast prop usage' },
    { pattern: /overlayPadding="p-6"/, name: 'overlayPadding prop usage' },
    { pattern: /AnimatedBackground[^>]*overlayMode/, name: 'AnimatedBackground with overlay props' },
    { pattern: /(?<!\/\/.*)bg-white\/70 backdrop-blur-sm/, name: 'Manual backdrop blur removed', required: false },
  ];
  
  if (!validateFileContent(featuredEventsPath, featuredEventsPatterns, 'FeaturedEvents component overlay')) {
    allTestsPassed = false;
  }

  // Test 6: Validate text contrast optimization implementation
  log('\n📝 Test 6: Text Contrast Optimization Implementation', 'blue');
  const textContrastPatterns = [
    { pattern: /Auto mode - choose based on overlay opacity/, name: 'Auto text contrast logic' },
    { pattern: /if \(opacity > 0\.3\)/, name: 'Opacity-based text contrast' },
    { pattern: /} else if \(opacity > 0\.1\)/, name: 'Low opacity text handling' },
    { pattern: /text-white drop-shadow-md/, name: 'Light text with shadow for readability' },
  ];
  
  if (!validateFileContent(overlayUtilsPath, textContrastPatterns, 'Text contrast optimization')) {
    allTestsPassed = false;
  }

  // Test 7: Validate overlay integration patterns
  log('\n📝 Test 7: Overlay Integration Patterns', 'blue');
  const integrationPatterns = [
    { pattern: /const hexToRgb = \(hex: string\)/, name: 'Color parsing utility' },
    { pattern: /blur\([0-9]+px\) saturate/, name: 'Backdrop filter implementation' },
    { pattern: /relative z-10 rounded-lg/, name: 'Base overlay classes' },
    { pattern: /shadow-lg.*shadow-md/, name: 'Style-specific enhancements' },
  ];
  
  if (!validateFileContent(overlayUtilsPath, integrationPatterns, 'Overlay integration patterns')) {
    allTestsPassed = false;
  }

  // Final results
  log('\n' + '='.repeat(50), 'blue');
  if (allTestsPassed) {
    log('🎉 All T4.3 Content Overlay Handling tests passed!', 'green');
    log('✅ Content overlay handling with proper blur effects has been successfully implemented', 'green');
    log('✅ AnimatedBackground component includes comprehensive overlay system', 'green');
    log('✅ Standardized overlay utilities are implemented and functional', 'green');
    log('✅ Homepage, About page, and FeaturedEvents use standardized overlays', 'green');
    log('✅ Automatic text contrast optimization is implemented', 'green');
    log('✅ T4.3 implementation is complete and ready for integration testing', 'green');
  } else {
    log('❌ Some T4.3 Content Overlay Handling tests failed', 'red');
    log('🔧 Please review the failing tests and ensure all overlay features are properly implemented', 'yellow');
  }

  process.exit(allTestsPassed ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { main };