#!/usr/bin/env node

/**
 * T4.1 Validation Script: Strategic Sections for Animated Backgrounds
 * 
 * This script validates that strategic sections for animated backgrounds have been
 * properly identified and documented according to PRD requirements.
 * 
 * Validation Criteria:
 * 1. Strategic sections analysis document created
 * 2. Hero sections identified and prioritized
 * 3. CTA sections identified and categorized
 * 4. Transition zones mapped out
 * 5. Implementation priority matrix defined
 * 6. Technical configuration guidelines established
 * 7. Performance and accessibility considerations documented
 */

const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function logSuccess(message) {
  console.log(`${colors.green}✓${colors.reset} ${message}`);
}

function logError(message) {
  console.log(`${colors.red}✗${colors.reset} ${message}`);
}

function logWarning(message) {
  console.log(`${colors.yellow}⚠${colors.reset} ${message}`);
}

function logInfo(message) {
  console.log(`${colors.blue}ℹ${colors.reset} ${message}`);
}

function logHeader(message) {
  console.log(`\n${colors.bold}${colors.cyan}${message}${colors.reset}`);
}

let validationResults = {
  passed: 0,
  failed: 0,
  warnings: 0,
  details: []
};

function validateCheck(condition, successMessage, errorMessage, isWarning = false) {
  if (condition) {
    logSuccess(successMessage);
    validationResults.passed++;
    validationResults.details.push({ type: 'pass', message: successMessage });
  } else {
    if (isWarning) {
      logWarning(errorMessage);
      validationResults.warnings++;
      validationResults.details.push({ type: 'warning', message: errorMessage });
    } else {
      logError(errorMessage);
      validationResults.failed++;
      validationResults.details.push({ type: 'error', message: errorMessage });
    }
  }
}

// File paths
const analysisDocPath = path.join(__dirname, '../tasks/t4.1-strategic-sections-analysis.md');
const indexPagePath = path.join(__dirname, '../src/pages/Index.tsx');
const aboutPagePath = path.join(__dirname, '../src/pages/About.tsx');
const aboutCroatiaPath = path.join(__dirname, '../src/components/AboutCroatia.tsx');
const featuredEventsPath = path.join(__dirname, '../src/components/FeaturedEvents.tsx');

logHeader('T4.1 Strategic Sections for Animated Backgrounds Validation');
logInfo('Validating strategic section identification and documentation...\n');

// Check if analysis document exists
if (!fs.existsSync(analysisDocPath)) {
  logError('Strategic sections analysis document not found');
  process.exit(1);
}

// Read analysis document
const analysisContent = fs.readFileSync(analysisDocPath, 'utf8');

logHeader('1. Strategic Sections Analysis Document');

// Check for main document structure
validateCheck(
  analysisContent.includes('# T4.1: Strategic Sections Analysis for Animated Backgrounds'),
  'Analysis document header properly formatted',
  'Analysis document missing proper header'
);

validateCheck(
  analysisContent.includes('## Strategic Section Analysis'),
  'Strategic section analysis section present',
  'Strategic section analysis section missing'
);

validateCheck(
  analysisContent.includes('## Implementation Priority Matrix'),
  'Implementation priority matrix section present',
  'Implementation priority matrix section missing'
);

validateCheck(
  analysisContent.includes('## Technical Configuration Guidelines'),
  'Technical configuration guidelines section present',
  'Technical configuration guidelines section missing'
);

logHeader('2. Hero Sections Identification');

// Check for hero section analysis
validateCheck(
  analysisContent.includes('### 1. Hero Sections') &&
  analysisContent.includes('**Primary Heroes (High Priority)**') &&
  analysisContent.includes('**Secondary Heroes (Medium Priority)**'),
  'Hero sections properly categorized by priority',
  'Hero sections missing or improperly categorized'
);

// Check for specific hero sections
const heroSections = [
  'Home Page Hero',
  'About Page Hero',
  'OrganizerDashboard Header'
];

heroSections.forEach(section => {
  validateCheck(
    analysisContent.includes(section),
    `${section} identified in analysis`,
    `${section} missing from analysis`
  );
});

// Check for configuration recommendations
validateCheck(
  analysisContent.includes('intensity={0.6}') &&
  analysisContent.includes('blueOnly={true}') &&
  analysisContent.includes('gentleMovement={true}'),
  'Hero sections include proper configuration recommendations',
  'Hero sections missing configuration recommendations'
);

logHeader('3. Call-to-Action (CTA) Sections');

// Check for CTA analysis
validateCheck(
  analysisContent.includes('### 2. Call-to-Action (CTA) Sections') &&
  analysisContent.includes('**Primary CTAs (High Priority)**') &&
  analysisContent.includes('**Secondary CTAs (Medium Priority)**'),
  'CTA sections properly categorized by priority',
  'CTA sections missing or improperly categorized'
);

// Check for specific CTA sections
const ctaSections = [
  'AboutCroatia Section',
  'FeaturedEvents Section',
  'Contact Section'
];

ctaSections.forEach(section => {
  validateCheck(
    analysisContent.includes(section),
    `${section} identified as CTA`,
    `${section} missing from CTA analysis`
  );
});

// Check for CTA-specific configurations
validateCheck(
  analysisContent.includes('adjustableBlur={true}') &&
  analysisContent.includes('blurType="content"'),
  'CTA sections include content-aware blur configurations',
  'CTA sections missing content-aware blur configurations'
);

logHeader('4. Transition Zones Mapping');

// Check for transition zones analysis
validateCheck(
  analysisContent.includes('### 3. Transition Zones') &&
  analysisContent.includes('**Primary Transitions (High Priority)**') &&
  analysisContent.includes('**Secondary Transitions (Medium Priority)**'),
  'Transition zones properly categorized',
  'Transition zones missing or improperly categorized'
);

// Check for specific transition areas
const transitionAreas = [
  'Page Section Breaks',
  'Form Transitions',
  'Navigation Hover States'
];

transitionAreas.forEach(area => {
  validateCheck(
    analysisContent.includes(area),
    `${area} identified as transition zone`,
    `${area} missing from transition analysis`
  );
});

// Check for transition-specific configurations
validateCheck(
  analysisContent.includes('opacityMode="adaptive"') &&
  analysisContent.includes('opacityTransitions={true}'),
  'Transition zones include adaptive opacity configurations',
  'Transition zones missing adaptive opacity configurations'
);

logHeader('5. Interactive Sections Analysis');

// Check for interactive sections
validateCheck(
  analysisContent.includes('### 4. Interactive Sections') &&
  analysisContent.includes('**Content Overlays (High Priority)**'),
  'Interactive sections properly identified',
  'Interactive sections missing from analysis'
);

// Check for overlay configurations
validateCheck(
  analysisContent.includes('contentBlur={6}') &&
  analysisContent.includes('backgroundBlur={8}'),
  'Interactive sections include proper overlay blur configurations',
  'Interactive sections missing overlay blur configurations'
);

logHeader('6. Priority Matrix Validation');

// Check for implementation phases
const phases = [
  'Phase 1: Core Impact Areas',
  'Phase 2: Enhanced Experience',
  'Phase 3: Professional Polish'
];

phases.forEach(phase => {
  validateCheck(
    analysisContent.includes(phase),
    `${phase} defined in priority matrix`,
    `${phase} missing from priority matrix`
  );
});

// Check for specific priority assignments
validateCheck(
  analysisContent.includes('1. **Home Page Hero Section** - Maximum visual impact') &&
  analysisContent.includes('2. **AboutCroatia CTA Section** - Key conversion area') &&
  analysisContent.includes('3. **Event Detail Hero** - Critical user engagement'),
  'Phase 1 priorities properly defined',
  'Phase 1 priorities missing or incomplete'
);

logHeader('7. Technical Configuration Guidelines');

// Check for performance considerations
validateCheck(
  analysisContent.includes('### Performance Considerations') &&
  analysisContent.includes('mobileIntensity={0.3}') &&
  analysisContent.includes('tabletIntensity={0.4-0.5}'),
  'Performance considerations properly documented',
  'Performance considerations missing or incomplete'
);

// Check for accessibility standards
validateCheck(
  analysisContent.includes('### Accessibility Standards') &&
  analysisContent.includes('respectReducedMotion={true}') &&
  analysisContent.includes('intensity ≤ 0.2 to avoid distraction'),
  'Accessibility standards properly documented',
  'Accessibility standards missing or incomplete'
);

// Check for visual hierarchy guidelines
validateCheck(
  analysisContent.includes('### Visual Hierarchy') &&
  analysisContent.includes('**Primary sections**: intensity={0.5-0.6}') &&
  analysisContent.includes('**Secondary sections**: intensity={0.3-0.4}') &&
  analysisContent.includes('**Background sections**: intensity={0.1-0.2}'),
  'Visual hierarchy guidelines properly defined',
  'Visual hierarchy guidelines missing or incomplete'
);

// Check for brand consistency
validateCheck(
  analysisContent.includes('### Brand Consistency') &&
  analysisContent.includes('**All sections**: blueOnly={true}') &&
  analysisContent.includes('blueIntensity="light"') &&
  analysisContent.includes('blueIntensity="medium"'),
  'Brand consistency guidelines properly defined',
  'Brand consistency guidelines missing or incomplete'
);

logHeader('8. Success Metrics Definition');

// Check for success metrics
validateCheck(
  analysisContent.includes('## Success Metrics') &&
  analysisContent.includes('### User Experience Metrics') &&
  analysisContent.includes('### Technical Metrics'),
  'Success metrics properly defined',
  'Success metrics missing or incomplete'
);

// Check for specific metrics
const metrics = [
  'Visual Appeal',
  'Performance',
  'Accessibility',
  'Frame Rate',
  'Bundle Size',
  'Memory Usage'
];

metrics.forEach(metric => {
  validateCheck(
    analysisContent.includes(metric),
    `${metric} metric defined`,
    `${metric} metric missing`
  );
});

// Check for performance targets
validateCheck(
  analysisContent.includes('60fps on desktop, 30fps mobile') &&
  analysisContent.includes('100KB per page') &&
  analysisContent.includes('WCAG 2.1 AA standards'),
  'Performance targets properly specified',
  'Performance targets missing or incomplete'
);

logHeader('9. Implementation Planning');

// Check for next steps
validateCheck(
  analysisContent.includes('## Next Steps') &&
  analysisContent.includes('1. **Validate Selections**') &&
  analysisContent.includes('2. **Create Implementation Plan**') &&
  analysisContent.includes('3. **Develop Components**'),
  'Implementation next steps properly defined',
  'Implementation next steps missing or incomplete'
);

// Check for integration notes
validateCheck(
  analysisContent.includes('**Implementation Note**') &&
  analysisContent.includes('T4.2-T4.5 implementation'),
  'Implementation integration notes present',
  'Implementation integration notes missing'
);

logHeader('10. File References Validation');

// Check if referenced files exist
const referencedFiles = [
  indexPagePath,
  aboutPagePath,
  aboutCroatiaPath,
  featuredEventsPath
];

referencedFiles.forEach(filePath => {
  const fileName = path.basename(filePath);
  validateCheck(
    fs.existsSync(filePath),
    `Referenced file ${fileName} exists`,
    `Referenced file ${fileName} not found`
  );
});

// Check for specific line references in files
if (fs.existsSync(indexPagePath)) {
  const indexContent = fs.readFileSync(indexPagePath, 'utf8');
  const lines = indexContent.split('\n');
  
  // Enhanced validation with robust array bounds checking
  const hasValidLineCount = lines.length >= 77;
  const hasValidLine26 = lines.length > 25 && lines[25] && typeof lines[25] === 'string';
  
  // Safe line content checking with multiple fallback patterns
  const containsHeroSection = hasValidLine26 && (
    lines[25].includes('section') ||
    lines[25].includes('<section') ||
    lines[25].includes('className="mb-12"') ||
    // Check surrounding lines for section content if line 26 doesn't match
    (lines.length > 27 && lines.slice(24, 28).some(line => 
      line && typeof line === 'string' && (
        line.includes('<section') || 
        line.includes('section className') ||
        line.includes('mb-12')
      )
    ))
  );
  
  // Additional content validation for hero section patterns
  const heroSectionPatterns = [
    'AnimatedBackground',
    'hero',
    'main.*container',
    'text-4xl.*md:text-5xl',
    'EnhancedSearch',
    'PageTransition',
    'Header'
  ];
  
  // Safe pattern matching with error handling
  const hasHeroSectionContent = heroSectionPatterns.some(pattern => {
    try {
      return indexContent.match(new RegExp(pattern, 'i'));
    } catch (error) {
      console.warn(`Pattern matching error for "${pattern}":`, error.message);
      return false;
    }
  });
  
  // Additional check for specific AnimatedBackground integration
  const hasAnimatedBackgroundIntegration = indexContent.includes('import AnimatedBackground') &&
    indexContent.includes('<AnimatedBackground') &&
    indexContent.includes('blueOnly={true}');
  
  const validationPassed = hasValidLineCount && containsHeroSection && 
    (hasHeroSectionContent || hasAnimatedBackgroundIntegration);
  
  validateCheck(
    validationPassed,
    'Index.tsx hero section properly referenced with expected content patterns',
    `Index.tsx hero section validation failed:\n` +
    `  - Line count >= 77: ${hasValidLineCount}\n` +
    `  - Valid line 26 exists: ${hasValidLine26}\n` +
    `  - Contains section markers: ${containsHeroSection}\n` +
    `  - Has hero content patterns: ${hasHeroSectionContent}\n` +
    `  - Has AnimatedBackground integration: ${hasAnimatedBackgroundIntegration}`
  );
}

if (fs.existsSync(aboutCroatiaPath)) {
  const aboutCroatiaContent = fs.readFileSync(aboutCroatiaPath, 'utf8');
  
  validateCheck(
    aboutCroatiaContent.includes('bg-gradient-to-r from-navy-blue to-medium-blue'),
    'AboutCroatia section properly identified with gradient background',
    'AboutCroatia section identification may be incorrect'
  );
}

// Summary
logHeader('Validation Summary');

const totalChecks = validationResults.passed + validationResults.failed;
const successRate = totalChecks > 0 ? ((validationResults.passed / totalChecks) * 100).toFixed(1) : 0;

console.log(`\n${colors.bold}Results:${colors.reset}`);
console.log(`${colors.green}✓ Passed: ${validationResults.passed}${colors.reset}`);
console.log(`${colors.red}✗ Failed: ${validationResults.failed}${colors.reset}`);
console.log(`${colors.yellow}⚠ Warnings: ${validationResults.warnings}${colors.reset}`);
console.log(`${colors.blue}Success Rate: ${successRate}%${colors.reset}`);

if (validationResults.failed === 0) {
  console.log(`\n${colors.bold}${colors.green}🎉 T4.1 Strategic Sections identification completed successfully!${colors.reset}`);
  console.log(`${colors.green}✓ All strategic sections properly identified and documented${colors.reset}`);
  console.log(`${colors.green}✓ Implementation priority matrix established${colors.reset}`);
  console.log(`${colors.green}✓ Technical configuration guidelines defined${colors.reset}`);
  console.log(`${colors.green}✓ Success metrics and next steps documented${colors.reset}`);
  
  if (validationResults.warnings > 0) {
    console.log(`\n${colors.yellow}Note: ${validationResults.warnings} warning(s) found. Review recommended but not blocking.${colors.reset}`);
  }
} else {
  console.log(`\n${colors.bold}${colors.red}❌ T4.1 Strategic Sections identification validation failed${colors.reset}`);
  console.log(`${colors.red}Please fix the ${validationResults.failed} error(s) before proceeding.${colors.reset}`);
  process.exit(1);
}
