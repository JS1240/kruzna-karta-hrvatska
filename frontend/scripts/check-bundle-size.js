#!/usr/bin/env node

/**
 * Bundle Size Checker Script
 * 
 * Analyzes the built bundle and reports on size violations.
 * Ensures mobile optimization libraries stay under size limits.
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
 * Get command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const limitArg = args.find(arg => arg.startsWith('--limit='));
  const limit = limitArg ? parseInt(limitArg.split('=')[1]) : 1000; // Default 1MB
  
  return { limit };
}

/**
 * Get file size in KB
 */
function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath);
    return Math.round(stats.size / 1024); // Convert to KB
  } catch (error) {
    return 0;
  }
}

/**
 * Get all JS files in dist directory
 */
function getDistFiles(distPath) {
  const files = [];
  
  if (!fs.existsSync(distPath)) {
    log.error(`Dist directory not found: ${distPath}`);
    return files;
  }
  
  function walkDir(dir) {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        walkDir(fullPath);
      } else if (item.endsWith('.js') && !item.endsWith('.map')) {
        const relativePath = path.relative(distPath, fullPath);
        const size = getFileSize(fullPath);
        files.push({ path: relativePath, size, fullPath });
      }
    }
  }
  
  walkDir(distPath);
  return files.sort((a, b) => b.size - a.size); // Sort by size descending
}

/**
 * Analyze mobile optimization file sizes
 */
function analyzeMobileOptimizations() {
  const mobileFiles = [
    'src/utils/mobileDetection.ts',
    'src/utils/mobilePerformanceMonitor.ts',
    'src/utils/connectionAwareOptimizer.ts',
    'src/utils/mobileTouchOptimizer.ts'
  ];
  
  log.header('📱 Mobile Optimization File Analysis');
  
  let totalMobileSize = 0;
  const mobileFileSizes = [];
  
  for (const file of mobileFiles) {
    const filePath = path.join(__dirname, '..', file);
    const size = getFileSize(filePath);
    totalMobileSize += size;
    mobileFileSizes.push({ file, size });
    
    if (size > 25) { // Warning if any mobile file > 25KB
      log.warning(`${file}: ${size}KB (large mobile file)`);
    } else {
      log.info(`${file}: ${size}KB`);
    }
  }
  
  log.info(`Total mobile optimization code: ${totalMobileSize}KB`);
  
  if (totalMobileSize > 100) {
    log.warning('Mobile optimization files are quite large. Consider code splitting.');
  } else {
    log.success('Mobile optimization file sizes are reasonable.');
  }
  
  return { totalMobileSize, mobileFileSizes };
}

/**
 * Analyze bundle chunks
 */
function analyzeBundleChunks(files, limit) {
  log.header('📦 Bundle Chunk Analysis');
  
  let totalSize = 0;
  const violations = [];
  const chunks = [];
  
  // Categorize files
  for (const file of files) {
    totalSize += file.size;
    chunks.push(file);
    
    if (file.size > limit) {
      violations.push(file);
    }
  }
  
  // Report on chunks
  log.info(`Total bundle size: ${totalSize}KB`);
  log.info(`Number of chunks: ${chunks.length}`);
  
  if (chunks.length > 0) {
    log.info('\nLargest chunks:');
    chunks.slice(0, 5).forEach(chunk => {
      const status = chunk.size > limit ? colors.red : 
                    chunk.size > limit * 0.8 ? colors.yellow : colors.green;
      console.log(`  ${status}${chunk.path}: ${chunk.size}KB${colors.reset}`);
    });
  }
  
  return { totalSize, violations, chunks };
}

/**
 * Identify optimization opportunities
 */
function identifyOptimizations(files, limit) {
  log.header('🎯 Optimization Opportunities');
  
  const opportunities = [];
  
  // Check for large vendor chunks
  const vendorFiles = files.filter(f => f.path.includes('vendor') || f.path.includes('chunk'));
  const largeVendors = vendorFiles.filter(f => f.size > limit * 0.5);
  
  if (largeVendors.length > 0) {
    opportunities.push({
      type: 'Large vendor chunks detected',
      files: largeVendors,
      suggestion: 'Consider splitting large libraries or using dynamic imports'
    });
  }
  
  // Check for animation-related files
  const animationFiles = files.filter(f => 
    f.path.includes('three') || 
    f.path.includes('vanta') || 
    f.path.includes('p5') ||
    f.path.includes('animation')
  );
  
  if (animationFiles.length > 0) {
    const animationSize = animationFiles.reduce((sum, f) => sum + f.size, 0);
    if (animationSize > limit) {
      opportunities.push({
        type: 'Animation libraries are large',
        files: animationFiles,
        suggestion: 'Implement lazy loading for animation libraries'
      });
    }
  }
  
  // Check for map-related files
  const mapFiles = files.filter(f => f.path.includes('mapbox') || f.path.includes('map'));
  if (mapFiles.length > 0) {
    const mapSize = mapFiles.reduce((sum, f) => sum + f.size, 0);
    if (mapSize > limit * 0.5) {
      opportunities.push({
        type: 'Map libraries are large',
        files: mapFiles,
        suggestion: 'Load maps only when needed'
      });
    }
  }
  
  // Report opportunities
  if (opportunities.length === 0) {
    log.success('No obvious optimization opportunities found.');
  } else {
    opportunities.forEach((opp, index) => {
      log.warning(`${index + 1}. ${opp.type}`);
      log.info(`   Files: ${opp.files.map(f => f.path).join(', ')}`);
      log.info(`   Total size: ${opp.files.reduce((sum, f) => sum + f.size, 0)}KB`);
      log.info(`   Suggestion: ${opp.suggestion}`);
    });
  }
  
  return opportunities;
}

/**
 * Generate bundle report
 */
function generateReport(analysis) {
  const { limit } = parseArgs();
  const { totalSize, violations, chunks } = analysis.bundle;
  const { totalMobileSize } = analysis.mobile;
  
  log.header('📊 Bundle Size Report');
  
  const report = {
    timestamp: new Date().toISOString(),
    limit: `${limit}KB`,
    totalSize: `${totalSize}KB`,
    mobileOptimizationSize: `${totalMobileSize}KB`,
    chunksCount: chunks.length,
    violations: violations.length,
    status: violations.length === 0 ? 'PASS' : 'FAIL',
    recommendations: []
  };
  
  // Add recommendations
  if (totalSize > limit * 2) {
    report.recommendations.push('Bundle is significantly oversized. Implement aggressive code splitting.');
  }
  
  if (violations.length > 0) {
    report.recommendations.push(`${violations.length} chunks exceed ${limit}KB limit. Consider splitting or lazy loading.`);
  }
  
  if (totalMobileSize > 50) {
    report.recommendations.push('Mobile optimization files are large. Consider conditional loading.');
  }
  
  if (chunks.length < 3) {
    report.recommendations.push('Too few chunks. Implement more aggressive code splitting.');
  }
  
  // Save report
  const reportPath = path.join(__dirname, '../dist/bundle-report.json');
  try {
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    log.success(`Report saved to: ${reportPath}`);
  } catch (error) {
    log.warning('Could not save report file');
  }
  
  return report;
}

/**
 * Main function
 */
function main() {
  const { limit } = parseArgs();
  
  log.header(`🔍 Bundle Size Analysis (Limit: ${limit}KB)`);
  
  const distPath = path.join(__dirname, '../dist');
  
  // Analyze mobile optimizations
  const mobileAnalysis = analyzeMobileOptimizations();
  
  // Get bundle files
  const files = getDistFiles(distPath);
  
  if (files.length === 0) {
    log.error('No bundle files found. Run "npm run build" first.');
    process.exit(1);
  }
  
  // Analyze bundle
  const bundleAnalysis = analyzeBundleChunks(files, limit);
  
  // Identify optimizations
  const optimizations = identifyOptimizations(files, limit);
  
  // Generate report
  const report = generateReport({
    mobile: mobileAnalysis,
    bundle: bundleAnalysis,
    optimizations
  });
  
  // Final status
  log.header('🎯 Final Status');
  
  if (bundleAnalysis.violations.length === 0) {
    log.success(`✅ All chunks under ${limit}KB limit!`);
    if (bundleAnalysis.totalSize > limit * 3) {
      log.warning(`⚠️  Total bundle size (${bundleAnalysis.totalSize}KB) is quite large`);
    } else {
      log.success(`📦 Total bundle size: ${bundleAnalysis.totalSize}KB`);
    }
  } else {
    log.error(`❌ ${bundleAnalysis.violations.length} chunks exceed ${limit}KB limit:`);
    bundleAnalysis.violations.forEach(file => {
      log.error(`   ${file.path}: ${file.size}KB`);
    });
  }
  
  if (mobileAnalysis.totalMobileSize < 30) {
    log.success(`📱 Mobile optimization impact: ${mobileAnalysis.totalMobileSize}KB (excellent)`);
  } else if (mobileAnalysis.totalMobileSize < 50) {
    log.warning(`📱 Mobile optimization impact: ${mobileAnalysis.totalMobileSize}KB (acceptable)`);
  } else {
    log.error(`📱 Mobile optimization impact: ${mobileAnalysis.totalMobileSize}KB (too large)`);
  }
  
  // Exit with appropriate code
  const hasViolations = bundleAnalysis.violations.length > 0;
  const mobileTooLarge = mobileAnalysis.totalMobileSize > 50;
  
  if (hasViolations || mobileTooLarge) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}

// Run the analysis
main();