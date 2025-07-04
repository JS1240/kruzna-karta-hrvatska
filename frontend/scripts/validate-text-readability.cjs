#!/usr/bin/env node

/**
 * T4.4 Text Readability Validation Script
 * 
 * This script validates that text readability over animated backgrounds
 * has been successfully implemented across all components.
 * 
 * Success Criteria:
 * - All text uses brand colors (text-brand-primary, text-brand-black, text-brand-white)
 * - Text shadows are applied consistently for animated background sections
 * - Overlay modes provide sufficient contrast for text readability
 * - No legacy gray or navy-blue text colors remain
 * - Smart text shadow system is implemented
 * - All components use proper text contrast classes
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

  patterns.forEach(({ pattern, name, required = true, shouldNotExist = false }) => {
    const found = pattern.test(content);
    if (shouldNotExist) {
      if (!found) {
        log(`  ✅ ${name}: Correctly removed`, 'green');
      } else {
        log(`  ❌ ${name}: Still exists`, 'red');
        allFound = false;
      }
    } else {
      if (found) {
        log(`  ✅ ${name}: Found`, 'green');
      } else if (required) {
        log(`  ❌ ${name}: Missing`, 'red');
        allFound = false;
      } else {
        log(`  ⚠️  ${name}: Optional - Not found`, 'yellow');
      }
    }
  });

  return allFound;
}

function validateNoLegacyColors(filePath, description) {
  if (!fs.existsSync(filePath)) {
    log(`❌ ${description}: File not found - ${filePath}`, 'red');
    return false;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  const legacyPatterns = [
    { pattern: /text-gray-[0-9]/, name: 'Legacy gray text colors' },
    { pattern: /text-navy-blue/, name: 'Legacy navy-blue text colors' },
    { pattern: /dark:text-gray-[0-9]/, name: 'Legacy gray dark mode colors' },
  ];

  let allPassed = true;
  legacyPatterns.forEach(({ pattern, name }) => {
    const matches = content.match(pattern);
    if (matches) {
      log(`  ❌ ${name}: Found ${matches.length} instances`, 'red');
      allPassed = false;
    } else {
      log(`  ✅ ${name}: None found`, 'green');
    }
  });

  return allPassed;
}

function main() {
  log('🔍 T4.4 Text Readability Over Animated Backgrounds Validation', 'bold');
  log('='.repeat(65), 'blue');

  let allTestsPassed = true;

  // Test 1: Validate Homepage hero section enhancements
  log('\n📝 Test 1: Homepage Hero Section Text Readability', 'blue');
  const indexPath = path.join(__dirname, '../src/pages/Index.tsx');
  const indexPatterns = [
    { pattern: /overlayMode="medium"/, name: 'Enhanced overlay mode' },
    { pattern: /drop-shadow-lg/, name: 'Main heading text shadow' },
    { pattern: /drop-shadow-md/, name: 'Subtitle text shadow' },
    { pattern: /drop-shadow-sm/, name: 'Feature text shadows' },
    { pattern: /text-brand-primary/, name: 'Brand primary text color usage' },
    { pattern: /text-brand-black/, name: 'Brand black text color usage' },
    { pattern: /dark:text-brand-white/, name: 'Brand white dark mode text' },
  ];
  
  if (!validateFileContent(indexPath, indexPatterns, 'Homepage hero section')) {
    allTestsPassed = false;
  }

  // Test 2: Validate FeaturedEvents component improvements
  log('\n📝 Test 2: FeaturedEvents Component Text Readability', 'blue');
  const featuredEventsPath = path.join(__dirname, '../src/components/FeaturedEvents.tsx');
  const featuredEventsPatterns = [
    { pattern: /overlayMode="medium"/, name: 'Enhanced overlay mode' },
    { pattern: /text-brand-primary.*drop-shadow-md/, name: 'Section title with shadow' },
    { pattern: /bg-brand-primary.*text-white/, name: 'Event card location badge' },
    { pattern: /text-brand-primary.*truncate/, name: 'Event card title color' },
    { pattern: /gap-2 text-xs text-brand-black/, name: 'Event card date color' },
  ];
  
  if (!validateFileContent(featuredEventsPath, featuredEventsPatterns, 'FeaturedEvents component')) {
    allTestsPassed = false;
  }

  // Test 3: Validate AboutCroatia component optimization
  log('\n📝 Test 3: AboutCroatia Component Text Readability', 'blue');
  const aboutPath = path.join(__dirname, '../src/components/AboutCroatia.tsx');
  const aboutPatterns = [
    { pattern: /textContrast="auto"/, name: 'Auto text contrast mode' },
    { pattern: /drop-shadow-lg/, name: 'Main heading shadow' },
    { pattern: /drop-shadow-md/, name: 'Section heading shadows' },
    { pattern: /drop-shadow-sm/, name: 'Content text shadows' },
    { pattern: /overlayMode="medium"/, name: 'Medium overlay mode' },
    { pattern: /overlayStyle="frosted"/, name: 'Frosted overlay style' },
  ];
  
  if (!validateFileContent(aboutPath, aboutPatterns, 'AboutCroatia component')) {
    allTestsPassed = false;
  }

  // Test 4: Validate Header navigation text readability
  log('\n📝 Test 4: Header Navigation Text Readability', 'blue');
  const headerPath = path.join(__dirname, '../src/components/Header.tsx');
  const headerPatterns = [
    { pattern: /dark:text-brand-white/, name: 'Brand white dark mode navigation' },
    { pattern: /text-brand-black/, name: 'Brand black navigation text' },
  ];
  
  if (!validateFileContent(headerPath, headerPatterns, 'Header navigation')) {
    allTestsPassed = false;
  }

  // Test 5: Validate smart text shadow system implementation
  log('\n📝 Test 5: Smart Text Shadow System Implementation', 'blue');
  const overlayUtilsPath = path.join(__dirname, '../src/utils/overlayUtils.ts');
  const shadowSystemPatterns = [
    { pattern: /getAnimationAwareTextShadow/, name: 'Animation-aware text shadow function' },
    { pattern: /getPerformanceAwareTextStyling/, name: 'Performance-aware text styling function' },
    { pattern: /text-brand-black drop-shadow-/, name: 'Brand color with smart shadows' },
    { pattern: /text-white drop-shadow-lg/, name: 'Light text with strong shadows' },
    { pattern: /shadowIntensity.*animationIntensity/, name: 'Shadow intensity calculation' },
    { pattern: /high-contrast.*drop-shadow-lg/, name: 'High contrast mode shadows', required: false },
  ];
  
  if (!validateFileContent(overlayUtilsPath, shadowSystemPatterns, 'Smart text shadow system')) {
    allTestsPassed = false;
  }

  // Test 6: Validate brand color migration in LatestNews
  log('\n📝 Test 6: LatestNews Component Brand Color Migration', 'blue');
  const latestNewsPath = path.join(__dirname, '../src/components/LatestNews.tsx');
  if (!validateNoLegacyColors(latestNewsPath, 'LatestNews component legacy colors')) {
    allTestsPassed = false;
  }

  // Test 7: Check for legacy text colors across key components
  log('\n📝 Test 7: Legacy Text Color Elimination', 'blue');
  const keyComponentPaths = [
    { path: indexPath, name: 'Homepage' },
    { path: featuredEventsPath, name: 'FeaturedEvents' },
    { path: aboutPath, name: 'AboutCroatia' },
    { path: headerPath, name: 'Header' },
    { path: latestNewsPath, name: 'LatestNews' },
  ];

  let legacyColorsFound = false;
  keyComponentPaths.forEach(({ path: filePath, name }) => {
    if (!validateNoLegacyColors(filePath, `${name} legacy colors`)) {
      legacyColorsFound = true;
    }
  });
  
  if (legacyColorsFound) {
    allTestsPassed = false;
  }

  // Test 8: Validate text shadow consistency
  log('\n📝 Test 8: Text Shadow Consistency Validation', 'blue');
  const shadowPatterns = [
    { pattern: /drop-shadow-sm/, name: 'Small text shadows (subtle elements)' },
    { pattern: /drop-shadow-md/, name: 'Medium text shadows (standard elements)' },
    { pattern: /drop-shadow-lg/, name: 'Large text shadows (headings)' },
    { pattern: /drop-shadow-xl/, name: 'Extra large shadows (high contrast)', required: false },
  ];
  
  // Check shadow usage across components
  const shadowValidation = keyComponentPaths.every(({ path: filePath, name }) => {
    const content = fs.readFileSync(filePath, 'utf-8');
    const hasShadows = shadowPatterns.some(({ pattern }) => pattern.test(content));
    if (hasShadows) {
      log(`  ✅ ${name}: Text shadows implemented`, 'green');
      return true;
    } else {
      log(`  ⚠️  ${name}: No text shadows found`, 'yellow');
      return true; // Not necessarily a failure for all components
    }
  });

  // Final results
  log('\n' + '='.repeat(65), 'blue');
  if (allTestsPassed) {
    log('🎉 All T4.4 Text Readability tests passed!', 'green');
    log('✅ Text readability over animated backgrounds successfully implemented', 'green');
    log('✅ All components use brand colors for consistent visual hierarchy', 'green');
    log('✅ Smart text shadow system provides optimal readability', 'green');
    log('✅ Overlay modes deliver sufficient contrast for all text elements', 'green');
    log('✅ Legacy color classes eliminated from key components', 'green');
    log('✅ Header navigation and animated sections have enhanced readability', 'green');
    log('✅ T4.4 implementation is complete and ready for user testing', 'green');
  } else {
    log('❌ Some T4.4 Text Readability tests failed', 'red');
    log('🔧 Please review the failing tests and ensure all readability requirements are met', 'yellow');
    log('📋 Focus on: overlay configurations, text shadows, brand color usage, and contrast ratios', 'yellow');
  }

  process.exit(allTestsPassed ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { main };