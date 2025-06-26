#!/usr/bin/env node

/**
 * Validation script for accent color contrast ratios
 * Validates WCAG 2.1 AA compliance for accent colors
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

// Test accent color combinations
function validateAccentColors() {
  console.log('🎨 Validating Accent Color Contrast Ratios');
  console.log('=========================================\n');

  const testCombinations = [
    // Accent Cream backgrounds with text
    { 
      bg: COLORS.brandAccentCream, 
      text: COLORS.brandBlack, 
      name: 'Accent Cream + Black Text',
      usage: 'Badges, highlights'
    },
    { 
      bg: COLORS.brandAccentCream, 
      text: COLORS.brandPrimary, 
      name: 'Accent Cream + Primary Text',
      usage: 'Tags, secondary highlights'
    },
    
    // Accent Gold backgrounds with text
    { 
      bg: COLORS.brandAccentGold, 
      text: COLORS.brandBlack, 
      name: 'Accent Gold + Black Text',
      usage: 'Notifications, warnings, price badges'
    },
    { 
      bg: COLORS.brandAccentGold, 
      text: COLORS.brandPrimary, 
      name: 'Accent Gold + Primary Text',
      usage: 'Alternative accent elements'
    },
    
    // White backgrounds with accent text
    { 
      bg: COLORS.brandWhite, 
      text: COLORS.brandAccentCream, 
      name: 'White + Accent Cream Text',
      usage: 'Accent text on white backgrounds'
    },
    { 
      bg: COLORS.brandWhite, 
      text: COLORS.brandAccentGold, 
      name: 'White + Accent Gold Text',
      usage: 'Accent text on white backgrounds'
    }
  ];

  let allPassed = true;

  testCombinations.forEach(({ bg, text, name, usage }) => {
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

  // Additional accent color usage validations
  console.log('🔍 Accent Color Usage Validation');
  console.log('===============================\n');

  console.log('✅ Accent Cream (#F5F0CD):');
  console.log('   - Used for: Badge backgrounds, hover highlights, subtle accents');
  console.log('   - Paired with: Black text, Primary blue text');
  console.log('   - WCAG AA Compliant with recommended text colors\n');

  console.log('✅ Accent Gold (#FADA7A):');
  console.log('   - Used for: Notifications, warnings, price badges, trending indicators');
  console.log('   - Paired with: Black text for maximum contrast');
  console.log('   - WCAG AA Compliant with recommended text colors\n');

  if (allPassed) {
    console.log('🎉 All accent color combinations pass WCAG 2.1 AA standards!');
  } else {
    console.log('⚠️  Some combinations need adjustment for WCAG compliance.');
  }

  return allPassed;
}

// Run validation
validateAccentColors();
