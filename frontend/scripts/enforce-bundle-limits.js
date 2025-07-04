#!/usr/bin/env node

/**
 * Bundle Size Enforcement Script
 * 
 * Enforces bundle size limits and provides optimization recommendations.
 * Integrates with CI/CD to prevent bundle size regressions.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ANSI color codes
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

const log = {
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bold}${colors.cyan}${msg}${colors.reset}`),
};

/**
 * Bundle size limits configuration
 */
const BUNDLE_LIMITS = {
  // Main application bundle
  main: 500, // 500KB
  
  // Individual chunk limits
  chunks: {
    'vendor-react': 200,     // React ecosystem
    'animation-three': 600,  // Three.js
    'animation-vanta': 100,  // Vanta.js
    'animation-p5': 1200,    // p5.js (large but optional)
    'vendor-maps': 1200,     // Mapbox GL
    'vendor-charts': 300,    // Recharts
    'vendor-ui-radix': 200,  // Radix UI components
    'mobile-optimizations': 50, // Mobile optimization features
  },
  
  // Total bundle size limit
  total: 2500, // 2.5MB total
  
  // Critical path limit (essential chunks)
  critical: 800, // 800KB for critical path
};

/**
 * Critical chunks that must be loaded on initial page load
 */
const CRITICAL_CHUNKS = [
  'vendor-react',
  'vendor-routing',
  'main',
];

/**
 * Optional chunks that can be lazy loaded
 */
const OPTIONAL_CHUNKS = [
  'animation-three',
  'animation-vanta',
  'animation-p5',
  'vendor-maps',
  'vendor-charts',
  'mobile-optimizations',
];

/**
 * Parses command-line arguments and returns an options object indicating which enforcement modes are enabled.
 * @return {{strict: boolean, fix: boolean, report: boolean, ci: boolean}} An object with flags for strict mode, fix mode, report mode, and CI mode.
 */
function parseArgs() {
  const args = process.argv.slice(2);
  
  const options = {
    strict: false,
    fix: false,
    report: false,
    ci: false,
  };
  
  args.forEach(arg => {
    if (arg === '--strict') options.strict = true;
    if (arg === '--fix') options.fix = true;
    if (arg === '--report') options.report = true;
    if (arg === '--ci') options.ci = true;
  });
  
  return options;
}

/**
 * Returns the size of a file in kilobytes.
 * If the file does not exist or cannot be accessed, returns 0.
 * @param {string} filePath - The path to the file.
 * @return {number} The file size in kilobytes, or 0 if unavailable.
 */
function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath);
    return Math.round(stats.size / 1024);
  } catch (error) {
    return 0;
  }
}

/**
 * Scans the specified dist directory for JavaScript bundle files, categorizes them into chunk names, and aggregates their sizes.
 *
 * @param {string} distPath - Path to the distribution directory containing bundle files.
 * @return {Map<string, number>} A map of chunk names to their total sizes in kilobytes. Returns an empty map if the directory does not exist.
 */
function getDistChunks(distPath) {
  const chunks = new Map();
  
  if (!fs.existsSync(distPath)) {
    log.error(`Dist directory not found: ${distPath}`);
    return chunks;
  }
  
  const files = fs.readdirSync(distPath);
  
  files.forEach(file => {
    if (file.endsWith('.js') && !file.endsWith('.map')) {
      const filePath = path.join(distPath, file);
      const size = getFileSize(filePath);
      
      // Extract chunk name from filename
      let chunkName = 'main';
      if (file.includes('vendor-react')) chunkName = 'vendor-react';
      else if (file.includes('animation-three')) chunkName = 'animation-three';
      else if (file.includes('animation-vanta')) chunkName = 'animation-vanta';
      else if (file.includes('animation-p5')) chunkName = 'animation-p5';
      else if (file.includes('vendor-maps')) chunkName = 'vendor-maps';
      else if (file.includes('vendor-charts')) chunkName = 'vendor-charts';
      else if (file.includes('vendor-ui-radix')) chunkName = 'vendor-ui-radix';
      else if (file.includes('vendor-routing')) chunkName = 'vendor-routing';
      else if (file.includes('vendor-query')) chunkName = 'vendor-query';
      else if (file.includes('vendor-forms')) chunkName = 'vendor-forms';
      else if (file.includes('vendor-utils')) chunkName = 'vendor-utils';
      else if (file.includes('vendor-icons')) chunkName = 'vendor-icons';
      else if (file.includes('vendor-misc')) chunkName = 'vendor-misc';
      else if (file.includes('mobile-optimizations')) chunkName = 'mobile-optimizations';
      else if (file.includes('index') || file.includes('main')) chunkName = 'main';
      else chunkName = file.replace(/\.[^/.]+$/, ""); // Remove extension
      
      if (chunks.has(chunkName)) {
        chunks.set(chunkName, chunks.get(chunkName) + size);
      } else {
        chunks.set(chunkName, size);
      }
    }
  });
  
  return chunks;
}

/**
 * Analyzes JavaScript bundle chunk sizes against predefined limits, identifying violations and warnings, and generates optimization recommendations.
 *
 * @param {Map<string, number>} chunks - Map of chunk names to their sizes in KB.
 * @param {Object} options - Options object controlling analysis behavior.
 * @return {Object} Analysis results including violations, warnings, recommendations, total bundle size, and critical path size.
 */
function analyzeBundleViolations(chunks, options) {
  log.header('📊 Bundle Size Analysis');
  
  const violations = [];
  const warnings = [];
  const recommendations = [];
  
  // Check individual chunk limits
  for (const [chunkName, size] of chunks) {
    const limit = BUNDLE_LIMITS.chunks[chunkName] || BUNDLE_LIMITS.main;
    
    if (size > limit) {
      violations.push({
        type: 'chunk',
        name: chunkName,
        size,
        limit,
        overage: size - limit,
      });
    } else if (size > limit * 0.8) {
      warnings.push({
        type: 'chunk',
        name: chunkName,
        size,
        limit,
        percentage: (size / limit) * 100,
      });
    }
  }
  
  // Check total bundle size
  const totalSize = Array.from(chunks.values()).reduce((sum, size) => sum + size, 0);
  if (totalSize > BUNDLE_LIMITS.total) {
    violations.push({
      type: 'total',
      name: 'Total Bundle',
      size: totalSize,
      limit: BUNDLE_LIMITS.total,
      overage: totalSize - BUNDLE_LIMITS.total,
    });
  }
  
  // Check critical path size
  const criticalSize = CRITICAL_CHUNKS.reduce((sum, chunkName) => {
    return sum + (chunks.get(chunkName) || 0);
  }, 0);
  
  if (criticalSize > BUNDLE_LIMITS.critical) {
    violations.push({
      type: 'critical',
      name: 'Critical Path',
      size: criticalSize,
      limit: BUNDLE_LIMITS.critical,
      overage: criticalSize - BUNDLE_LIMITS.critical,
    });
  }
  
  // Generate recommendations
  if (violations.length > 0 || warnings.length > 0) {
    recommendations.push(...generateOptimizationRecommendations(chunks, violations, warnings));
  }
  
  return { violations, warnings, recommendations, totalSize, criticalSize };
}

/**
 * Generates prioritized optimization recommendations based on chunk sizes and detected bundle violations or warnings.
 *
 * Analyzes specific chunk categories (such as animation, maps, charts, mobile optimizations, UI libraries, and miscellaneous vendors) and suggests targeted actions like code splitting, lazy loading, or dependency audits when size thresholds are exceeded.
 *
 * @param {Map<string, number>} chunks - Map of chunk names to their sizes in KB.
 * @param {Array} violations - List of bundle size violations.
 * @param {Array} warnings - List of bundle size warnings.
 * @return {Array<Object>} Array of recommendation objects, each containing priority, type, message, and suggested action.
 */
function generateOptimizationRecommendations(chunks, violations, warnings) {
  const recommendations = [];
  
  // Check for large animation libraries
  const animationSize = ['animation-three', 'animation-vanta', 'animation-p5']
    .reduce((sum, chunk) => sum + (chunks.get(chunk) || 0), 0);
  
  if (animationSize > 800) {
    recommendations.push({
      priority: 'high',
      type: 'code-splitting',
      message: `Animation libraries are ${animationSize}KB. Implement lazy loading.`,
      action: 'Use dynamic imports for animation libraries',
    });
  }
  
  // Check for large map libraries
  const mapSize = chunks.get('vendor-maps') || 0;
  if (mapSize > 1000) {
    recommendations.push({
      priority: 'high',
      type: 'lazy-loading',
      message: `Map library is ${mapSize}KB. Load only when maps are needed.`,
      action: 'Lazy load Mapbox GL when map components are rendered',
    });
  }
  
  // Check for chart libraries
  const chartSize = chunks.get('vendor-charts') || 0;
  if (chartSize > 250) {
    recommendations.push({
      priority: 'medium',
      type: 'conditional-loading',
      message: `Chart library is ${chartSize}KB. Consider lighter alternatives.`,
      action: 'Use lightweight charting library or load conditionally',
    });
  }
  
  // Check mobile optimizations
  const mobileSize = chunks.get('mobile-optimizations') || 0;
  if (mobileSize > 30) {
    recommendations.push({
      priority: 'medium',
      type: 'mobile-optimization',
      message: `Mobile optimizations are ${mobileSize}KB. Ensure proper lazy loading.`,
      action: 'Load mobile optimizations only on mobile devices',
    });
  }
  
  // Check for UI library size
  const uiSize = chunks.get('vendor-ui-radix') || 0;
  if (uiSize > 150) {
    recommendations.push({
      priority: 'low',
      type: 'tree-shaking',
      message: `UI library is ${uiSize}KB. Improve tree shaking.`,
      action: 'Import only required UI components',
    });
  }
  
  // Check for miscellaneous vendor chunks
  const miscSize = chunks.get('vendor-misc') || 0;
  if (miscSize > 100) {
    recommendations.push({
      priority: 'medium',
      type: 'dependency-audit',
      message: `Miscellaneous vendors are ${miscSize}KB. Audit dependencies.`,
      action: 'Review and remove unused dependencies',
    });
  }
  
  return recommendations;
}

/**
 * Outputs bundle analysis results, including violations, warnings, summary statistics, and optimization recommendations.
 * @param {Object} analysis - The analysis results containing violations, warnings, recommendations, total size, and critical path size.
 * @param {Object} options - CLI options affecting output formatting or behavior.
 * @return {boolean} Returns true if no bundle size violations are present; otherwise, false.
 */
function reportResults(analysis, options) {
  const { violations, warnings, recommendations, totalSize, criticalSize } = analysis;
  
  // Report violations
  if (violations.length > 0) {
    log.header('❌ Bundle Size Violations');
    violations.forEach(violation => {
      log.error(`${violation.name}: ${violation.size}KB (limit: ${violation.limit}KB, over by ${violation.overage}KB)`);
    });
  } else {
    log.header('✅ No Bundle Size Violations');
  }
  
  // Report warnings
  if (warnings.length > 0) {
    log.header('⚠️  Bundle Size Warnings');
    warnings.forEach(warning => {
      log.warning(`${warning.name}: ${warning.size}KB (${warning.percentage.toFixed(1)}% of ${warning.limit}KB limit)`);
    });
  }
  
  // Report totals
  log.header('📋 Bundle Summary');
  log.info(`Total bundle size: ${totalSize}KB (limit: ${BUNDLE_LIMITS.total}KB)`);
  log.info(`Critical path size: ${criticalSize}KB (limit: ${BUNDLE_LIMITS.critical}KB)`);
  
  // Report recommendations
  if (recommendations.length > 0) {
    log.header('💡 Optimization Recommendations');
    recommendations.forEach((rec, index) => {
      const priority = rec.priority === 'high' ? colors.red : 
                     rec.priority === 'medium' ? colors.yellow : colors.blue;
      console.log(`${index + 1}. ${priority}${rec.priority.toUpperCase()}${colors.reset}: ${rec.message}`);
      console.log(`   Action: ${rec.action}`);
    });
  }
  
  return violations.length === 0;
}

/**
 * Generates a shell script with recommended optimization steps based on bundle analysis.
 * The script is saved as `optimize-bundle.sh` in the parent directory if the `--fix` option is enabled and recommendations exist.
 */
function generateOptimizationScript(recommendations, options) {
  if (!options.fix || recommendations.length === 0) return;
  
  log.header('🔧 Generating Optimization Script');
  
  const scriptContent = `#!/bin/bash
# Generated Bundle Optimization Script
# Run this script to apply recommended optimizations

echo "Applying bundle size optimizations..."

${recommendations.map(rec => {
  switch (rec.type) {
    case 'code-splitting':
      return `# ${rec.message}\necho "Implementing code splitting for animation libraries..."`;
    case 'lazy-loading':
      return `# ${rec.message}\necho "Implementing lazy loading for heavy libraries..."`;
    case 'conditional-loading':
      return `# ${rec.message}\necho "Adding conditional loading..."`;
    case 'tree-shaking':
      return `# ${rec.message}\necho "Improving tree shaking..."`;
    case 'dependency-audit':
      return `# ${rec.message}\necho "Running dependency audit..."\nnpm audit`;
    default:
      return `# ${rec.message}\necho "Manual optimization required: ${rec.action}"`;
  }
}).join('\n\n')}

echo "Optimization script completed. Please review and implement suggestions manually."
`;
  
  const scriptPath = path.join(__dirname, '../optimize-bundle.sh');
  fs.writeFileSync(scriptPath, scriptContent);
  fs.chmodSync(scriptPath, '755');
  
  log.success(`Optimization script generated: ${scriptPath}`);
}

/**
 * Saves a JSON report of the bundle size analysis to the dist directory.
 *
 * The report includes a timestamp, bundle size limits, analysis results, chunk sizes, CLI options, and pass/fail status.
 * Returns the report object regardless of whether saving succeeds.
 *
 * @return {Object} The generated report object.
 */
function saveBundleReport(analysis, chunks, options) {
  const report = {
    timestamp: new Date().toISOString(),
    bundleLimits: BUNDLE_LIMITS,
    analysis,
    chunks: Object.fromEntries(chunks),
    options,
    status: analysis.violations.length === 0 ? 'PASS' : 'FAIL',
  };
  
  const reportPath = path.join(__dirname, '../dist/bundle-enforcement-report.json');
  
  try {
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    log.success(`Bundle report saved: ${reportPath}`);
  } catch (error) {
    log.warning('Could not save bundle report');
  }
  
  return report;
}

/**
 * Outputs bundle size analysis results in GitHub Actions workflow command format when running in CI mode.
 * 
 * If violations exist, logs errors and sets workflow outputs to indicate failure and the number of violations.
 * If no violations are found, logs a notice and sets outputs to indicate success.
 */
function handleCIMode(analysis, options) {
  if (!options.ci) return;
  
  const { violations } = analysis;
  
  if (violations.length > 0) {
    console.log('\n::error title=Bundle Size Violation::Bundle size limits exceeded');
    violations.forEach(violation => {
      console.log(`::error::${violation.name} is ${violation.size}KB (limit: ${violation.limit}KB)`);
    });
    
    // Set GitHub Actions output
    console.log(`::set-output name=bundle_status::failed`);
    console.log(`::set-output name=violations_count::${violations.length}`);
  } else {
    console.log('::notice title=Bundle Size Check::All bundle size limits passed');
    console.log(`::set-output name=bundle_status::passed`);
    console.log(`::set-output name=violations_count::0`);
  }
}

/**
 * Executes the bundle size enforcement workflow, including analysis, reporting, optimization script generation, report saving, and CI integration.
 *
 * Parses CLI options, checks bundle chunk sizes against configured limits, reports violations and warnings, generates optimization recommendations and scripts if requested, saves a JSON report, and exits with an appropriate status code based on enforcement results and mode.
 */
function main() {
  const options = parseArgs();
  
  log.header('🚦 Bundle Size Enforcement');
  log.info(`Mode: ${options.strict ? 'Strict' : 'Standard'}`);
  log.info(`Limits: Main=${BUNDLE_LIMITS.main}KB, Total=${BUNDLE_LIMITS.total}KB, Critical=${BUNDLE_LIMITS.critical}KB`);
  
  const distPath = path.join(__dirname, '../dist');
  
  // Get bundle chunks
  const chunks = getDistChunks(distPath);
  
  if (chunks.size === 0) {
    log.error('No bundle files found. Run "npm run build" first.');
    process.exit(1);
  }
  
  // Analyze bundle
  const analysis = analyzeBundleViolations(chunks, options);
  
  // Report results
  const passed = reportResults(analysis, options);
  
  // Generate optimization script if requested
  generateOptimizationScript(analysis.recommendations, options);
  
  // Save report
  saveBundleReport(analysis, chunks, options);
  
  // Handle CI mode
  handleCIMode(analysis, options);
  
  // Exit with appropriate code
  if (options.strict && !passed) {
    log.error('Bundle size enforcement failed in strict mode');
    process.exit(1);
  } else if (!passed) {
    log.warning('Bundle size limits exceeded (non-strict mode)');
    process.exit(options.ci ? 1 : 0);
  } else {
    log.success('✅ All bundle size limits passed!');
    process.exit(0);
  }
}

// Run enforcement
main();