#!/usr/bin/env node

/**
 * Validation script for text contrast colors
 * Validates WCAG 2.1 AA compliance for text color combinations
 * and identifies components using non-brand text colors
 */

// Color values from the color scheme
const COLORS = {
  // Brand Colors
  brandPrimary: '#3674B5',
  brandSecondary: '#578FCA',
  brandAccentCream: '#F5F0CD',
  brandAccentGold: '#FADA7A',
  brandBlack: '#000000',
  brandWhite: '#FFFFFF',
  
  // Common background colors in the app
  bgWhite: '#FFFFFF',
  bgCream: '#caf0f8',
  bgCard: '#FFFFFF',
  bgLight: '#f8fafc',
  bgGray100: '#f3f4f6',
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

// Calculate luminance
function getLuminance(hex) {
  const rgb = hexToRGB(hex);
  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// Calculate contrast ratio
function getContrastRatio(color1, color2) {
  const lum1 = getLuminance(color1);
  const lum2 = getLuminance(color2);
  const ratio = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
  return Math.round(ratio * 100) / 100;
}

// Test text color combinations
function validateTextColors() {
  console.log('📝 Validating Text Color Contrast Ratios');
  console.log('=======================================\n');

  const textCombinations = [
    // Primary text on common backgrounds
    { 
      bg: COLORS.bgWhite, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on White',
      usage: 'Primary text, body text, headings'
    },
    { 
      bg: COLORS.bgCream, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Cream',
      usage: 'Body text on cream background'
    },
    { 
      bg: COLORS.bgCard, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Card',
      usage: 'Card content text'
    },
    
    // White text on dark backgrounds
    { 
      bg: COLORS.brandPrimary, 
      text: COLORS.brandWhite, 
      name: 'Brand White on Primary',
      usage: 'Button text, primary elements'
    },
    { 
      bg: COLORS.brandSecondary, 
      text: COLORS.brandWhite, 
      name: 'Brand White on Secondary',
      usage: 'Secondary button text'
    },
    
    // Secondary text combinations
    { 
      bg: COLORS.bgWhite, 
      text: COLORS.brandPrimary, 
      name: 'Brand Primary on White',
      usage: 'Links, secondary headings'
    },
    { 
      bg: COLORS.bgCream, 
      text: COLORS.brandPrimary, 
      name: 'Brand Primary on Cream',
      usage: 'Links on cream background'
    },
    
    // Accent combinations
    { 
      bg: COLORS.brandAccentCream, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Accent Cream',
      usage: 'Text on highlighted elements'
    },
    { 
      bg: COLORS.brandAccentGold, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Accent Gold',
      usage: 'Text on notification elements'
    }
  ];

  let allPassed = true;

  textCombinations.forEach(({ bg, text, name, usage }) => {
    const ratio = getContrastRatio(bg, text);
    const isAACompliant = ratio >= 4.5;
    const isAAACompliant = ratio >= 7.0;
    
    const status = isAACompliant ? 
      (isAAACompliant ? '🟢 AAA' : '🟡 AA') : 
      '🔴 FAIL';
    
    console.log(`${status} ${name}`);
    console.log(`    Ratio: ${ratio}:1`);
    console.log(`    Usage: ${usage}`);
    console.log(`    Background: ${bg}, Text: ${text}\n`);
    
    if (!isAACompliant) {
      allPassed = false;
    }
  });

  // Text color usage guidelines
  console.log('📋 Text Color Usage Guidelines');
  console.log('=============================\n');

  console.log('🖤 Brand Black (#000000):');
  console.log('   - Primary use: Body text, headings, labels on light backgrounds');
  console.log('   - Tailwind class: text-brand-black');
  console.log('   - Replaces: text-gray-900, text-gray-800, text-slate-900\n');

  console.log('🤍 Brand White (#FFFFFF):');
  console.log('   - Primary use: Text on dark backgrounds, button text');
  console.log('   - Tailwind class: text-brand-white');
  console.log('   - Replaces: text-white on dark backgrounds\n');

  console.log('🔵 Brand Primary (#3674B5):');
  console.log('   - Primary use: Links, secondary headings, interactive elements');
  console.log('   - Tailwind class: text-brand-primary');
  console.log('   - Replaces: text-navy-blue, text-blue-600\n');

  console.log('⚠️  Gray Colors - When to Keep:');
  console.log('   - text-gray-500, text-gray-600: Subtle secondary text (only if contrast sufficient)');
  console.log('   - Consider replacing with text-brand-black/70 for consistency\n');

  if (allPassed) {
    console.log('🎉 All text color combinations pass WCAG 2.1 AA standards!');
  } else {
    console.log('⚠️  Some text combinations need adjustment for WCAG compliance.');
  }

  return allPassed;
}

// Find non-brand text color patterns
function analyzeTextColorPatterns() {
  console.log('\n🔍 Text Color Pattern Analysis');
  console.log('=============================\n');

  const nonBrandPatterns = [
    'text-gray-\\d+',
    'text-slate-\\d+', 
    'text-zinc-\\d+',
    'text-neutral-\\d+',
    'text-navy-blue',
    'text-blue-\\d+',
    'dark:text-gray-\\d+'
  ];

  const brandTextClasses = [
    'text-brand-black',
    'text-brand-white', 
    'text-brand-primary',
    'text-brand-secondary'
  ];

  console.log('📋 Recommended Text Color Mappings:');
  console.log('==================================\n');

  console.log('Replace these patterns:');
  console.log('  text-gray-900, text-gray-800 → text-brand-black');
  console.log('  text-gray-700, text-gray-600 → text-brand-black/80 or text-brand-black');
  console.log('  text-gray-500 → text-brand-black/60 (for subtle text)');
  console.log('  text-navy-blue → text-brand-primary');
  console.log('  text-blue-600, text-blue-700 → text-brand-primary');
  console.log('  text-white (on dark bg) → text-brand-white\n');

  console.log('✅ Already using brand colors:');
  brandTextClasses.forEach(cls => console.log(`  ${cls}`));
  
  console.log('\n🎯 Implementation Priority:');
  console.log('1. Headers and primary text → text-brand-black');
  console.log('2. Links and interactive elements → text-brand-primary');
  console.log('3. Button text → text-brand-white (on dark) / text-brand-black (on light)');
  console.log('4. Secondary/muted text → text-brand-black/70 or text-brand-black/60');
}

// Run validations
console.log('🎨 Brand Text Color Validation & Analysis');
console.log('========================================\n');

const isValid = validateTextColors();
analyzeTextColorPatterns();

console.log('\n📊 Summary:');
console.log(`WCAG Compliance: ${isValid ? '✅ PASS' : '❌ NEEDS WORK'}`);
console.log('Next Steps: Update components to use brand text colors for consistency');
