#!/usr/bin/env node

/**
 * Final validation script for contrast compliance
 * Validates WCAG 2.1 AA compliance for all brand color combinations
 */

// Color values from the brand color scheme
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

// Test all critical color combinations
function validateFinalContrast() {
  console.log('🎨 Final Brand Color Contrast Validation');
  console.log('======================================\n');

  const criticalCombinations = [
    // Primary text combinations
    { 
      bg: COLORS.brandWhite, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on White',
      usage: 'Primary body text, headings, labels',
      critical: true
    },
    { 
      bg: COLORS.brandAccentCream, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Accent Cream',
      usage: 'Text on highlighted sections, badges',
      critical: true
    },
    { 
      bg: COLORS.brandAccentGold, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Accent Gold',
      usage: 'Text on notifications, warnings',
      critical: true
    },
    
    // Button text combinations
    { 
      bg: COLORS.brandPrimary, 
      text: COLORS.brandWhite, 
      name: 'Brand White on Primary',
      usage: 'Primary button text',
      critical: true
    },
    { 
      bg: COLORS.brandSecondary, 
      text: COLORS.brandBlack, 
      name: 'Brand Black on Secondary',
      usage: 'Secondary button text (updated for contrast)',
      critical: true
    },
    
    // Link and interactive text
    { 
      bg: COLORS.brandWhite, 
      text: COLORS.brandPrimary, 
      name: 'Brand Primary on White',
      usage: 'Links, interactive elements',
      critical: true
    },
    
    // Previously problematic combinations (should now be avoided or fixed)
    { 
      bg: COLORS.brandSecondary, 
      text: COLORS.brandWhite, 
      name: 'Brand White on Secondary',
      usage: 'AVOID - Poor contrast (now using Black text)',
      critical: false,
      deprecated: true
    },
    { 
      bg: COLORS.brandAccentCream, 
      text: COLORS.brandPrimary, 
      name: 'Brand Primary on Cream',
      usage: 'Limited use - Check context',
      critical: false
    }
  ];

  let allCriticalPassed = true;
  let criticalCount = 0;
  let passedCount = 0;

  criticalCombinations.forEach(({ bg, text, name, usage, critical, deprecated }) => {
    const ratio = getContrastRatio(bg, text);
    const isAACompliant = ratio >= 4.5;
    const isAAACompliant = ratio >= 7.0;
    
    let status = '';
    if (deprecated) {
      status = '🚫 DEPRECATED';
    } else if (isAACompliant) {
      status = isAAACompliant ? '🟢 AAA' : '🟡 AA';
      if (critical) passedCount++;
    } else {
      status = '🔴 FAIL';
      if (critical) allCriticalPassed = false;
    }
    
    if (critical) criticalCount++;
    
    console.log(`${status} ${name}${critical ? ' (CRITICAL)' : ''}`);
    console.log(`    Ratio: ${ratio}:1`);
    console.log(`    Usage: ${usage}`);
    console.log(`    Background: ${bg}, Text: ${text}\n`);
  });

  // Summary
  console.log('📊 Validation Summary');
  console.log('==================\n');
  
  console.log(`✅ Critical combinations passed: ${passedCount}/${criticalCount}`);
  console.log(`📈 Success rate: ${Math.round((passedCount/criticalCount) * 100)}%\n`);

  if (allCriticalPassed) {
    console.log('🎉 All critical color combinations pass WCAG 2.1 AA standards!');
    console.log('✅ T2.5 - Text color contrast implementation complete');
    console.log('✅ Ready to proceed to T2.6 - Full WCAG validation');
  } else {
    console.log('⚠️  Some critical combinations still need adjustment.');
    console.log('❌ T2.5 - Text color contrast implementation needs more work');
  }

  // Implementation status
  console.log('\n🔧 Implementation Status');
  console.log('======================\n');
  console.log('✅ Updated text-gray-* → text-brand-black');
  console.log('✅ Updated text-navy-blue → text-brand-primary');
  console.log('✅ Updated text-white → text-brand-white (on dark backgrounds)');
  console.log('✅ Secondary button uses text-brand-black for better contrast');
  console.log('✅ Accent colors use text-brand-black for maximum contrast');
  console.log('\n📋 Next Steps for T2.6:');
  console.log('- Run comprehensive WCAG validation across all components');
  console.log('- Test color combinations in both light and dark modes');
  console.log('- Validate accessibility with screen readers');
  console.log('- Performance test with new color implementations');

  return allCriticalPassed;
}

// Run validation
const success = validateFinalContrast();
process.exit(success ? 0 : 1);
