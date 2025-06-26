#!/usr/bin/env node

/**
 * T4.2 Validation Script: Clear White Backgrounds
 * 
 * Validates the implementation of clear white backgrounds for non-animated sections
 * as specified in the animated background redesign PRD.
 */

const fs = require('fs');
const path = require('path');

class T42Validator {
  constructor() {
    this.frontendDir = path.join(__dirname, '..');
    this.errors = [];
    this.warnings = [];
    this.passed = [];
  }

  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️';
    console.log(`[${timestamp}] ${prefix} ${message}`);
  }

  error(message, file = null) {
    const fullMessage = file ? `${file}: ${message}` : message;
    this.errors.push(fullMessage);
    this.log(fullMessage, 'error');
  }

  warning(message, file = null) {
    const fullMessage = file ? `${file}: ${message}` : message;
    this.warnings.push(fullMessage);
    this.log(fullMessage, 'warning');
  }

  success(message) {
    this.passed.push(message);
    this.log(message, 'success');
  }

  readFile(filePath) {
    try {
      const fullPath = path.join(this.frontendDir, filePath);
      return fs.readFileSync(fullPath, 'utf8');
    } catch (error) {
      this.error(`Failed to read file: ${error.message}`, filePath);
      return null;
    }
  }

  fileExists(filePath) {
    try {
      const fullPath = path.join(this.frontendDir, filePath);
      return fs.existsSync(fullPath);
    } catch (error) {
      return false;
    }
  }

  // Validate CSS custom properties and Tailwind configuration
  validateBackgroundSystem() {
    this.log('Validating background system configuration...');

    // Check CSS custom properties
    const cssContent = this.readFile('src/index.css');
    if (cssContent) {
      const requiredProperties = [
        '--brand-white',
        '--brand-black',
        '--card',
        '--popover'
      ];

      let allPropertiesFound = true;
      requiredProperties.forEach(prop => {
        if (cssContent.includes(prop)) {
          this.success(`CSS custom property found: ${prop}`);
        } else {
          this.error(`Missing CSS custom property: ${prop}`, 'src/index.css');
          allPropertiesFound = false;
        }
      });

      if (allPropertiesFound) {
        this.success('All required CSS custom properties found');
      }
    }

    // Check Tailwind configuration
    const tailwindContent = this.readFile('tailwind.config.ts');
    if (tailwindContent) {
      const requiredColors = [
        'brand-white',
        'brand-black',
        'card',
        'popover'
      ];

      let allColorsFound = true;
      requiredColors.forEach(color => {
        if (tailwindContent.includes(color)) {
          this.success(`Tailwind color configuration found: ${color}`);
        } else {
          this.warning(`Tailwind color configuration missing: ${color}`, 'tailwind.config.ts');
          allColorsFound = false;
        }
      });

      if (allColorsFound) {
        this.success('All required Tailwind color configurations found');
      }
    }
  }

  // Validate page-level implementations
  validatePageImplementations() {
    this.log('Validating page-level white background implementations...');

    const pages = [
      'src/pages/About.tsx',
      'src/pages/Profile.tsx', 
      'src/pages/Admin.tsx',
      'src/pages/NotFound.tsx',
      'src/pages/Favorites.tsx',
      'src/pages/Popular.tsx',
      'src/pages/EventDetail.tsx'
    ];

    pages.forEach(pagePath => {
      const content = this.readFile(pagePath);
      if (content) {
        this.validatePageContent(content, pagePath);
      }
    });
  }

  validatePageContent(content, filePath) {
    // Check for proper white background usage in content areas
    const whiteBackgroundPatterns = [
      /bg-white/g,
      /bg-brand-white/g,
      /bg-card/g,
      /dark:bg-card/g,
      /dark:bg-popover/g
    ];

    let hasWhiteBackgrounds = false;
    whiteBackgroundPatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        hasWhiteBackgrounds = true;
        this.success(`Found ${matches.length} white background usage(s) in ${filePath}`);
      }
    });

    // Check for content sections that should have white backgrounds
    const contentSectionPatterns = [
      /<div[^>]+className[^>]*bg-white/g,
      /<section[^>]+className[^>]*bg-white/g,
      /<article[^>]+className[^>]*bg-white/g,
      /<form[^>]+className[^>]*bg-white/g
    ];

    let hasContentSections = false;
    contentSectionPatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        hasContentSections = true;
        this.success(`Found ${matches.length} white content section(s) in ${filePath}`);
      }
    });

    // Check for dark mode compatibility
    if (content.includes('dark:bg-card') || content.includes('dark:bg-popover')) {
      this.success(`Dark mode background support found in ${filePath}`);
    } else if (hasWhiteBackgrounds) {
      this.warning(`White backgrounds found but missing dark mode equivalents in ${filePath}`);
    }

    // Check for proper border and shadow usage
    if (content.includes('border') && content.includes('shadow')) {
      this.success(`Proper border and shadow usage found in ${filePath}`);
    } else if (hasWhiteBackgrounds) {
      this.warning(`White backgrounds found but missing borders/shadows for definition in ${filePath}`);
    }

    if (!hasWhiteBackgrounds && !hasContentSections) {
      this.warning(`No white background implementations found in ${filePath} - may need content area updates`);
    }
  }

  // Validate component implementations
  validateComponentImplementations() {
    this.log('Validating component-level white background implementations...');

    const components = [
      'src/components/EventCard.tsx',
      'src/components/NotificationCenter.tsx',
      'src/components/AttendeeManagement.tsx', 
      'src/components/EventCheckIn.tsx',
      'src/components/EnhancedSearch.tsx',
      'src/components/ErrorBoundary.tsx',
      'src/components/PWAInstallPrompt.tsx'
    ];

    components.forEach(componentPath => {
      const content = this.readFile(componentPath);
      if (content) {
        this.validateComponentContent(content, componentPath);
      }
    });
  }

  validateComponentContent(content, filePath) {
    // Check for card/container white backgrounds
    const cardBackgroundPatterns = [
      /className[^>]*bg-white/g,
      /className[^>]*bg-brand-white/g,
      /className[^>]*bg-card/g
    ];

    let hasCardBackgrounds = false;
    cardBackgroundPatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        hasCardBackgrounds = true;
        this.success(`Found ${matches.length} card background(s) in ${filePath}`);
      }
    });

    // Check for form/interactive element backgrounds
    const interactivePatterns = [
      /input[^>]*className[^>]*bg-white/g,
      /button[^>]*className[^>]*bg-white/g,
      /form[^>]*className[^>]*bg-white/g
    ];

    let hasInteractiveBackgrounds = false;
    interactivePatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        hasInteractiveBackgrounds = true;
        this.success(`Found ${matches.length} interactive element background(s) in ${filePath}`);
      }
    });

    // Check for backdrop/overlay backgrounds
    if (content.includes('backdrop-blur') || content.includes('bg-white/')) {
      this.success(`Proper overlay/backdrop backgrounds found in ${filePath}`);
    }

    if (!hasCardBackgrounds && !hasInteractiveBackgrounds) {
      this.warning(`Component may need white background implementation: ${filePath}`);
    }
  }

  // Validate accessibility and contrast
  validateAccessibility() {
    this.log('Validating accessibility and contrast requirements...');

    // Check for proper contrast classes
    const cssContent = this.readFile('src/index.css');
    if (cssContent) {
      // Verify brand colors meet contrast requirements
      if (cssContent.includes('--brand-black: 0 0% 0%') && cssContent.includes('--brand-white: 0 0% 100%')) {
        this.success('Maximum contrast colors (black/white) properly defined');
      } else {
        this.error('Brand black/white colors not properly defined for maximum contrast');
      }

      // Check for dark mode definitions
      if (cssContent.includes('.dark') && cssContent.includes('--card')) {
        this.success('Dark mode background colors properly defined');
      } else {
        this.warning('Dark mode background definitions may be incomplete');
      }
    }

    // Check for focus and hover states
    const componentFiles = [
      'src/components/ui/button.tsx',
      'src/components/ui/badge.tsx',
      'src/components/EventCard.tsx'
    ];

    componentFiles.forEach(filePath => {
      const content = this.readFile(filePath);
      if (content) {
        if (content.includes('focus:') || content.includes('hover:')) {
          this.success(`Interactive states properly defined in ${filePath}`);
        } else {
          this.warning(`Missing focus/hover states in ${filePath}`);
        }
      }
    });
  }

  // Validate responsive behavior
  validateResponsiveBehavior() {
    this.log('Validating responsive white background behavior...');

    const pages = [
      'src/pages/Index.tsx',
      'src/pages/About.tsx',
      'src/pages/EventDetail.tsx'
    ];

    pages.forEach(pagePath => {
      const content = this.readFile(pagePath);
      if (content) {
        // Check for responsive classes
        if (content.includes('md:') || content.includes('lg:') || content.includes('sm:')) {
          this.success(`Responsive design classes found in ${pagePath}`);
        }

        // Check for consistent background application
        if (content.includes('bg-white') || content.includes('bg-brand-white')) {
          this.success(`White background implementation found in ${pagePath}`);
        }
      }
    });
  }

  // Generate summary report
  generateReport() {
    this.log('\\n' + '='.repeat(60));
    this.log('T4.2 VALIDATION SUMMARY REPORT');
    this.log('='.repeat(60));

    this.log(`\\nTotal Checks: ${this.passed.length + this.warnings.length + this.errors.length}`);
    this.log(`✅ Passed: ${this.passed.length}`);
    this.log(`⚠️  Warnings: ${this.warnings.length}`);  
    this.log(`❌ Errors: ${this.errors.length}`);

    if (this.errors.length > 0) {
      this.log('\\n❌ ERRORS:');
      this.errors.forEach(error => this.log(`   • ${error}`));
    }

    if (this.warnings.length > 0) {
      this.log('\\n⚠️  WARNINGS:');
      this.warnings.forEach(warning => this.log(`   • ${warning}`));
    }

    // Calculate completion percentage
    const totalChecks = this.passed.length + this.warnings.length + this.errors.length;
    const successfulChecks = this.passed.length + this.warnings.length; // Warnings are not failures
    const completionPercentage = totalChecks > 0 ? Math.round((successfulChecks / totalChecks) * 100) : 0;

    this.log(`\\n📊 Completion: ${completionPercentage}%`);

    if (this.errors.length === 0) {
      this.log('\\n🎉 T4.2 VALIDATION PASSED!');
      this.log('Clear white backgrounds implementation is ready for next phase.');
    } else {
      this.log('\\n🔧 T4.2 VALIDATION REQUIRES FIXES');
      this.log('Please address the errors above before proceeding to T4.3.');
    }

    this.log('\\n' + '='.repeat(60));

    return this.errors.length === 0;
  }

  // Main validation method
  validate() {
    this.log('Starting T4.2: Clear White Backgrounds validation...');
    this.log('Validating implementation against PRD requirements\\n');

    this.validateBackgroundSystem();
    this.validatePageImplementations();
    this.validateComponentImplementations();
    this.validateAccessibility();
    this.validateResponsiveBehavior();

    return this.generateReport();
  }
}

// Run validation
if (require.main === module) {
  const validator = new T42Validator();
  try {
    const success = validator.validate();
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error('Validation failed:', error);
    process.exit(1);
  }
}

module.exports = T42Validator;
