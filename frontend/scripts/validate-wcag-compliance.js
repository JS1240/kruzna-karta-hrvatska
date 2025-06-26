#!/usr/bin/env node

/**
 * Comprehensive WCAG 2.1 AA compliance validation for all color combinations
 * Tests all brand colors across different contexts, modes, and usage scenarios
 */

// Brand color values from the design system
const BRAND_COLORS = {
  // Primary brand colors
  primary: '#3674B5',
  secondary: '#578FCA',
  
  // Accent colors
  accentCream: '#F5F0CD',
  accentGold: '#FADA7A',
  
  // Contrast colors
  black: '#000000',
  white: '#FFFFFF',
  
  // Additional contextual colors
  backgroundLight: '#FFFFFF',
  backgroundDark: '#1a1a1a',
  cardBackground: '#FFFFFF',
  overlayLight: '#FFFFFF99', // 60% opacity
  overlayDark: '#00000099'   // 60% opacity
};

// Convert hex to RGB
function hexToRGB(hex) {
  const cleanHex = hex.replace('#', '');
  return {
    r: parseInt(cleanHex.substr(0, 2), 16),
    g: parseInt(cleanHex.substr(2, 2), 16),
    b: parseInt(cleanHex.substr(4, 2), 16)
  };
}

// Calculate luminance (WCAG formula)
function getLuminance(hex) {
  const rgb = hexToRGB(hex);
  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// Calculate contrast ratio (WCAG formula)
function getContrastRatio(color1, color2) {
  const lum1 = getLuminance(color1);
  const lum2 = getLuminance(color2);
  const ratio = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
  return Math.round(ratio * 100) / 100;
}

// WCAG compliance levels
function getWCAGLevel(ratio, isLargeText = false) {
  const aaThreshold = isLargeText ? 3.0 : 4.5;
  const aaaThreshold = isLargeText ? 4.5 : 7.0;
  
  if (ratio >= aaaThreshold) return { level: 'AAA', icon: '🟢' };
  if (ratio >= aaThreshold) return { level: 'AA', icon: '🟡' };
  return { level: 'FAIL', icon: '🔴' };
}

// Test categories for comprehensive validation
const TEST_CATEGORIES = {
  // Primary text combinations (most critical)
  PRIMARY_TEXT: {
    name: 'Primary Text Combinations',
    critical: true,
    tests: [
      { bg: BRAND_COLORS.white, text: BRAND_COLORS.black, usage: 'Body text, headings, labels' },
      { bg: BRAND_COLORS.cardBackground, text: BRAND_COLORS.black, usage: 'Card content text' },
      { bg: BRAND_COLORS.accentCream, text: BRAND_COLORS.black, usage: 'Text on cream highlights' },
      { bg: BRAND_COLORS.accentGold, text: BRAND_COLORS.black, usage: 'Text on gold notifications' }
    ]
  },
  
  // Button text combinations
  BUTTON_TEXT: {
    name: 'Button Text Combinations',
    critical: true,
    tests: [
      { bg: BRAND_COLORS.primary, text: BRAND_COLORS.white, usage: 'Primary button text' },
      { bg: BRAND_COLORS.secondary, text: BRAND_COLORS.black, usage: 'Secondary button text (updated)' },
      { bg: BRAND_COLORS.accentCream, text: BRAND_COLORS.black, usage: 'Accent button text' },
      { bg: BRAND_COLORS.white, text: BRAND_COLORS.primary, usage: 'Outline button text' }
    ]
  },
  
  // Interactive elements
  INTERACTIVE_ELEMENTS: {
    name: 'Interactive Elements',
    critical: true,
    tests: [
      { bg: BRAND_COLORS.white, text: BRAND_COLORS.primary, usage: 'Links, clickable text' },
      { bg: BRAND_COLORS.cardBackground, text: BRAND_COLORS.primary, usage: 'Card links' },
      { bg: BRAND_COLORS.primary, text: BRAND_COLORS.white, usage: 'Active navigation items' },
      { bg: BRAND_COLORS.accentCream, text: BRAND_COLORS.black, usage: 'Links on cream background (FIXED: now uses black text)' }
    ]
  },
  
  // Large text combinations (headings, hero text)
  LARGE_TEXT: {
    name: 'Large Text (18pt+ or 14pt+ bold)',
    critical: false,
    isLargeText: true,
    tests: [
      { bg: BRAND_COLORS.white, text: BRAND_COLORS.primary, usage: 'Primary headings' },
      { bg: BRAND_COLORS.white, text: BRAND_COLORS.secondary, usage: 'Secondary headings' },
      { bg: BRAND_COLORS.primary, text: BRAND_COLORS.white, usage: 'Hero text on primary background' },
      { bg: BRAND_COLORS.accentCream, text: BRAND_COLORS.primary, usage: 'Headings on cream background' }
    ]
  },
  
  // Status and feedback colors
  STATUS_FEEDBACK: {
    name: 'Status & Feedback Elements',
    critical: false,
    tests: [
      { bg: BRAND_COLORS.accentGold, text: BRAND_COLORS.black, usage: 'Warning badges' },
      { bg: BRAND_COLORS.accentCream, text: BRAND_COLORS.black, usage: 'Info badges' },
      { bg: BRAND_COLORS.primary, text: BRAND_COLORS.white, usage: 'Primary badges' },
      { bg: BRAND_COLORS.white, text: BRAND_COLORS.black, usage: 'Default badges' }
    ]
  },
  
  // Dark mode combinations (if applicable)
  DARK_MODE: {
    name: 'Dark Mode Considerations',
    critical: false,
    tests: [
      { bg: BRAND_COLORS.backgroundDark, text: BRAND_COLORS.white, usage: 'Dark mode body text' },
      { bg: BRAND_COLORS.backgroundDark, text: BRAND_COLORS.accentGold, usage: 'Dark mode accent text' },
      { bg: BRAND_COLORS.primary, text: BRAND_COLORS.white, usage: 'Buttons in dark mode' },
      { bg: BRAND_COLORS.secondary, text: BRAND_COLORS.black, usage: 'Secondary buttons in dark mode' }
    ]
  }
};

// Run comprehensive validation
function validateWCAGCompliance() {
  console.log('🎨 Comprehensive WCAG 2.1 AA Compliance Validation');
  console.log('=================================================\n');

  let totalTests = 0;
  let passedTests = 0;
  let criticalTests = 0;
  let criticalPassed = 0;
  let failedTests = [];

  // Test each category
  Object.entries(TEST_CATEGORIES).forEach(([categoryKey, category]) => {
    console.log(`📋 ${category.name}`);
    console.log('='.repeat(category.name.length + 4));
    
    category.tests.forEach(({ bg, text, usage }) => {
      const ratio = getContrastRatio(bg, text);
      const { level, icon } = getWCAGLevel(ratio, category.isLargeText);
      
      totalTests++;
      if (category.critical) criticalTests++;
      
      const isPassed = level !== 'FAIL';
      if (isPassed) {
        passedTests++;
        if (category.critical) criticalPassed++;
      } else {
        failedTests.push({
          category: category.name,
          bg, text, usage, ratio, level
        });
      }
      
      const criticalLabel = category.critical ? ' (CRITICAL)' : '';
      const largeTextLabel = category.isLargeText ? ' (Large Text)' : '';
      
      console.log(`${icon} ${level} ${usage}${criticalLabel}${largeTextLabel}`);
      console.log(`    Ratio: ${ratio}:1`);
      console.log(`    Background: ${bg}, Text: ${text}\n`);
    });
    
    console.log('');
  });

  // Summary report
  console.log('📊 Validation Summary');
  console.log('===================\n');
  
  console.log(`📈 Overall Results:`);
  console.log(`   Total tests: ${totalTests}`);
  console.log(`   Passed: ${passedTests}/${totalTests} (${Math.round((passedTests/totalTests) * 100)}%)`);
  console.log(`   Failed: ${failedTests.length}\n`);
  
  console.log(`🎯 Critical Results:`);
  console.log(`   Critical tests: ${criticalTests}`);
  console.log(`   Critical passed: ${criticalPassed}/${criticalTests} (${Math.round((criticalPassed/criticalTests) * 100)}%)\n`);

  // Failed tests details
  if (failedTests.length > 0) {
    console.log('⚠️  Failed Tests Details');
    console.log('======================\n');
    
    failedTests.forEach((test, index) => {
      console.log(`${index + 1}. ${test.category}: ${test.usage}`);
      console.log(`   Background: ${test.bg}, Text: ${test.text}`);
      console.log(`   Ratio: ${test.ratio}:1 (${test.level})\n`);
    });
  }

  // Recommendations
  console.log('💡 Recommendations');
  console.log('=================\n');
  
  if (criticalPassed === criticalTests) {
    console.log('✅ All critical color combinations pass WCAG 2.1 AA standards');
    console.log('✅ Primary accessibility requirements met');
  } else {
    console.log('❌ Some critical combinations need adjustment');
  }
  
  if (passedTests === totalTests) {
    console.log('🎉 Perfect score! All color combinations are WCAG compliant');
    console.log('✅ T2.6 - WCAG validation COMPLETE');
  } else {
    console.log('⚠️  Some non-critical combinations could be improved');
    if (criticalPassed === criticalTests) {
      console.log('✅ T2.6 - WCAG validation COMPLETE (critical requirements met)');
    } else {
      console.log('❌ T2.6 - WCAG validation NEEDS WORK');
    }
  }

  // Implementation guidelines
  console.log('\n🔧 Implementation Status & Guidelines');
  console.log('===================================\n');
  
  console.log('✅ Current Brand Color System:');
  console.log('   - Primary text: #000000 on light backgrounds');
  console.log('   - Links/Interactive: #3674B5 on light backgrounds');
  console.log('   - Button text: #FFFFFF on #3674B5, #000000 on #578FCA');
  console.log('   - Accent text: #000000 on #F5F0CD and #FADA7A');
  console.log('');
  
  console.log('📋 Usage Guidelines:');
  console.log('   - Always use brand-black (#000000) for primary text');
  console.log('   - Use brand-primary (#3674B5) for links and interactive elements');
  console.log('   - Use brand-white (#FFFFFF) only on dark backgrounds');
  console.log('   - Test any custom color combinations with these tools');

  return criticalPassed === criticalTests;
}

// Run validation
const success = validateWCAGCompliance();
console.log(`\n🏁 Final Result: ${success ? 'PASS' : 'FAIL'}`);
process.exit(success ? 0 : 1);
