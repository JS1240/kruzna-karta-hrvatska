#!/usr/bin/env node

/**
 * Bundle Size Monitoring and Maintenance Tools
 * 
 * Provides ongoing monitoring, historical tracking, and maintenance
 * tools for bundle size management and optimization.
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
  magenta: '\x1b[35m',
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m'
};

const log = {
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bold}${colors.cyan}${msg}${colors.reset}`),
  metric: (label, value, unit = '') => console.log(`${colors.magenta}${label}:${colors.reset} ${colors.bold}${value}${unit}${colors.reset}`),
};

/**
 * Bundle size monitoring configuration
 */
const MONITORING_CONFIG = {
  // File paths
  historyFile: path.join(__dirname, '../dist/bundle-size-history.json'),
  reportFile: path.join(__dirname, '../dist/bundle-monitor-report.json'),
  alertsFile: path.join(__dirname, '../dist/bundle-alerts.json'),
  
  // Monitoring thresholds
  warningThresholds: {
    chunkGrowth: 0.15,      // 15% growth triggers warning
    totalGrowth: 0.10,      // 10% total growth triggers warning
    criticalGrowth: 0.20,   // 20% growth triggers critical alert
  },
  
  // History retention
  historyRetentionDays: 30,
  maxHistoryEntries: 100,
  
  // Alert settings
  enableAlerts: true,
  alertChannels: ['console', 'file', 'json'],
};

/**
 * Bundle size history entry
 */
interface HistoryEntry {
  timestamp: string;
  commit?: string;
  branch?: string;
  chunks: { [key: string]: number };
  totalSize: number;
  criticalSize: number;
  buildInfo?: {
    mode: string;
    duration?: number;
    nodeVersion: string;
  };
}

/**
 * Alert entry
 */
interface Alert {
  id: string;
  timestamp: string;
  type: 'warning' | 'critical';
  category: 'size_growth' | 'limit_exceeded' | 'regression';
  message: string;
  details: any;
  resolved?: boolean;
  resolvedAt?: string;
}

/**
 * Get file size in KB
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
 * Get current bundle sizes
 */
function getCurrentBundleSizes(distPath) {
  const chunks = new Map();
  
  if (!fs.existsSync(distPath)) {
    return chunks;
  }
  
  const files = fs.readdirSync(distPath);
  
  files.forEach(file => {
    if (file.endsWith('.js') && !file.endsWith('.map')) {
      const filePath = path.join(distPath, file);
      const size = getFileSize(filePath);
      
      // Extract chunk name
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
      else chunkName = file.replace(/\.[^/.]+$/, "");
      
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
 * Load bundle size history
 */
function loadHistory() {
  try {
    if (!fs.existsSync(MONITORING_CONFIG.historyFile)) {
      return [];
    }
    
    const data = fs.readFileSync(MONITORING_CONFIG.historyFile, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.warn('Could not load bundle size history:', error.message);
    return [];
  }
}

/**
 * Save bundle size history
 */
function saveHistory(history) {
  try {
    // Ensure directory exists
    const dir = path.dirname(MONITORING_CONFIG.historyFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    // Clean old entries
    const cleanedHistory = cleanHistory(history);
    
    fs.writeFileSync(MONITORING_CONFIG.historyFile, JSON.stringify(cleanedHistory, null, 2));
    return true;
  } catch (error) {
    console.warn('Could not save bundle size history:', error.message);
    return false;
  }
}

/**
 * Clean old history entries
 */
function cleanHistory(history) {
  const now = new Date();
  const cutoffDate = new Date(now.getTime() - (MONITORING_CONFIG.historyRetentionDays * 24 * 60 * 60 * 1000));
  
  // Filter by date and limit entries
  return history
    .filter(entry => new Date(entry.timestamp) > cutoffDate)
    .slice(-MONITORING_CONFIG.maxHistoryEntries)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
}

/**
 * Get Git information
 */
async function getGitInfo() {
  try {
    const { execSync } = await import('child_process');
    
    const commit = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    
    return { commit: commit.substring(0, 8), branch };
  } catch (error) {
    return { commit: 'unknown', branch: 'unknown' };
  }
}

/**
 * Create history entry
 */
async function createHistoryEntry(chunks) {
  const gitInfo = await getGitInfo();
  const chunksObj = Object.fromEntries(chunks);
  
  const totalSize = Array.from(chunks.values()).reduce((sum, size) => sum + size, 0);
  const criticalChunks = ['vendor-react', 'vendor-routing', 'main'];
  const criticalSize = criticalChunks.reduce((sum, chunkName) => {
    return sum + (chunks.get(chunkName) || 0);
  }, 0);
  
  return {
    timestamp: new Date().toISOString(),
    commit: gitInfo.commit,
    branch: gitInfo.branch,
    chunks: chunksObj,
    totalSize,
    criticalSize,
    buildInfo: {
      mode: process.env.NODE_ENV || 'development',
      nodeVersion: process.version,
    }
  };
}

/**
 * Analyze size changes
 */
function analyzeSizeChanges(currentEntry, history) {
  if (history.length === 0) {
    return { changes: [], alerts: [] };
  }
  
  const previousEntry = history[history.length - 1];
  const changes = [];
  const alerts = [];
  
  // Analyze chunk changes
  for (const [chunkName, currentSize] of Object.entries(currentEntry.chunks)) {
    const previousSize = previousEntry.chunks[chunkName] || 0;
    
    if (previousSize > 0) {
      const growthPercentage = (currentSize - previousSize) / previousSize;
      
      if (Math.abs(growthPercentage) > 0.01) { // Only track changes > 1%
        changes.push({
          chunk: chunkName,
          previousSize,
          currentSize,
          change: currentSize - previousSize,
          growthPercentage: growthPercentage * 100,
        });
        
        // Check for alerts
        if (growthPercentage > MONITORING_CONFIG.warningThresholds.criticalGrowth) {
          alerts.push(createAlert('critical', 'size_growth', 
            `${chunkName} chunk grew by ${(growthPercentage * 100).toFixed(1)}%`,
            { chunk: chunkName, growth: growthPercentage, previousSize, currentSize }
          ));
        } else if (growthPercentage > MONITORING_CONFIG.warningThresholds.chunkGrowth) {
          alerts.push(createAlert('warning', 'size_growth',
            `${chunkName} chunk grew by ${(growthPercentage * 100).toFixed(1)}%`,
            { chunk: chunkName, growth: growthPercentage, previousSize, currentSize }
          ));
        }
      }
    }
  }
  
  // Analyze total size change
  const totalGrowth = (currentEntry.totalSize - previousEntry.totalSize) / previousEntry.totalSize;
  
  if (totalGrowth > MONITORING_CONFIG.warningThresholds.totalGrowth) {
    alerts.push(createAlert('warning', 'size_growth',
      `Total bundle size grew by ${(totalGrowth * 100).toFixed(1)}%`,
      { totalGrowth, previousTotal: previousEntry.totalSize, currentTotal: currentEntry.totalSize }
    ));
  }
  
  return { changes, alerts };
}

/**
 * Create alert
 */
function createAlert(type, category, message, details) {
  return {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString(),
    type,
    category,
    message,
    details,
    resolved: false,
  };
}

/**
 * Display size changes
 */
function displaySizeChanges(changes) {
  if (changes.length === 0) {
    log.info('No significant size changes detected');
    return;
  }
  
  log.header('📈 Bundle Size Changes');
  
  changes.forEach(change => {
    const changeStr = change.change > 0 ? `+${change.change}KB` : `${change.change}KB`;
    const percentStr = change.growthPercentage > 0 ? 
      `+${change.growthPercentage.toFixed(1)}%` : 
      `${change.growthPercentage.toFixed(1)}%`;
    
    if (change.change > 0) {
      console.log(`${colors.red}↗${colors.reset} ${change.chunk}: ${change.previousSize}KB → ${change.currentSize}KB (${changeStr}, ${percentStr})`);
    } else {
      console.log(`${colors.green}↘${colors.reset} ${change.chunk}: ${change.previousSize}KB → ${change.currentSize}KB (${changeStr}, ${percentStr})`);
    }
  });
}

/**
 * Display alerts
 */
function displayAlerts(alerts) {
  if (alerts.length === 0) {
    return;
  }
  
  log.header('🚨 Bundle Size Alerts');
  
  alerts.forEach(alert => {
    if (alert.type === 'critical') {
      log.error(`CRITICAL: ${alert.message}`);
    } else {
      log.warning(`WARNING: ${alert.message}`);
    }
  });
}

/**
 * Generate size trends
 */
function generateSizeTrends(history) {
  if (history.length < 2) {
    return { trends: [], insights: [] };
  }
  
  const trends = [];
  const insights = [];
  
  // Analyze last 7 entries (roughly a week if daily builds)
  const recentHistory = history.slice(-7);
  
  if (recentHistory.length >= 2) {
    const firstEntry = recentHistory[0];
    const lastEntry = recentHistory[recentHistory.length - 1];
    
    const totalGrowth = (lastEntry.totalSize - firstEntry.totalSize) / firstEntry.totalSize;
    
    trends.push({
      period: `Last ${recentHistory.length} builds`,
      totalGrowth: totalGrowth * 100,
      startSize: firstEntry.totalSize,
      endSize: lastEntry.totalSize,
    });
    
    // Generate insights
    if (totalGrowth > 0.05) {
      insights.push(`Bundle size has grown ${(totalGrowth * 100).toFixed(1)}% over recent builds`);
    }
    
    if (totalGrowth < -0.05) {
      insights.push(`Bundle size has decreased ${Math.abs(totalGrowth * 100).toFixed(1)}% over recent builds`);
    }
    
    // Check for consistent growth
    let consecutiveGrowth = 0;
    for (let i = 1; i < recentHistory.length; i++) {
      if (recentHistory[i].totalSize > recentHistory[i - 1].totalSize) {
        consecutiveGrowth++;
      } else {
        consecutiveGrowth = 0;
      }
    }
    
    if (consecutiveGrowth >= 3) {
      insights.push(`Bundle size has grown in ${consecutiveGrowth} consecutive builds`);
    }
  }
  
  return { trends, insights };
}

/**
 * Display trends and insights
 */
function displayTrendsAndInsights(trends, insights) {
  if (trends.length > 0) {
    log.header('📊 Size Trends');
    trends.forEach(trend => {
      log.metric(trend.period, `${trend.startSize}KB → ${trend.endSize}KB (${trend.totalGrowth > 0 ? '+' : ''}${trend.totalGrowth.toFixed(1)}%)`);
    });
  }
  
  if (insights.length > 0) {
    log.header('💡 Insights');
    insights.forEach(insight => log.info(insight));
  }
}

/**
 * Save monitoring report
 */
function saveMonitoringReport(data) {
  try {
    const report = {
      timestamp: new Date().toISOString(),
      ...data,
      generatedBy: 'bundle-monitor',
    };
    
    const dir = path.dirname(MONITORING_CONFIG.reportFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(MONITORING_CONFIG.reportFile, JSON.stringify(report, null, 2));
    log.success(`Monitoring report saved: ${MONITORING_CONFIG.reportFile}`);
  } catch (error) {
    log.warning('Could not save monitoring report');
  }
}

/**
 * Save alerts
 */
function saveAlerts(alerts) {
  if (alerts.length === 0) return;
  
  try {
    let existingAlerts = [];
    if (fs.existsSync(MONITORING_CONFIG.alertsFile)) {
      const data = fs.readFileSync(MONITORING_CONFIG.alertsFile, 'utf8');
      existingAlerts = JSON.parse(data);
    }
    
    // Add new alerts
    const allAlerts = [...existingAlerts, ...alerts];
    
    // Clean old alerts (keep last 50)
    const cleanedAlerts = allAlerts.slice(-50);
    
    fs.writeFileSync(MONITORING_CONFIG.alertsFile, JSON.stringify(cleanedAlerts, null, 2));
    log.success(`${alerts.length} alert(s) saved`);
  } catch (error) {
    log.warning('Could not save alerts');
  }
}

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  
  const options = {
    record: false,
    analyze: false,
    trends: false,
    report: false,
    quiet: false,
  };
  
  args.forEach(arg => {
    if (arg === '--record') options.record = true;
    if (arg === '--analyze') options.analyze = true;
    if (arg === '--trends') options.trends = true;
    if (arg === '--report') options.report = true;
    if (arg === '--quiet') options.quiet = true;
  });
  
  // Default: record and analyze
  if (!options.record && !options.analyze && !options.trends && !options.report) {
    options.record = true;
    options.analyze = true;
  }
  
  return options;
}

/**
 * Main monitoring function
 */
async function main() {
  const options = parseArgs();
  
  if (!options.quiet) {
    log.header('📦 Bundle Size Monitor');
  }
  
  const distPath = path.join(__dirname, '../dist');
  
  // Get current bundle sizes
  const currentChunks = getCurrentBundleSizes(distPath);
  
  if (currentChunks.size === 0) {
    log.error('No bundle files found. Run "npm run build" first.');
    process.exit(1);
  }
  
  // Load history
  const history = loadHistory();
  
  let currentEntry = null;
  let changes = [];
  let alerts = [];
  let trends = [];
  let insights = [];
  
  // Record current sizes
  if (options.record) {
    currentEntry = await createHistoryEntry(currentChunks);
    history.push(currentEntry);
    saveHistory(history);
    
    if (!options.quiet) {
      log.success('Bundle sizes recorded');
    }
  }
  
  // Analyze changes
  if (options.analyze && history.length > 0) {
    const entryToAnalyze = currentEntry || (await createHistoryEntry(currentChunks));
    const analysis = analyzeSizeChanges(entryToAnalyze, history.slice(0, -1));
    changes = analysis.changes;
    alerts = analysis.alerts;
    
    if (!options.quiet) {
      displaySizeChanges(changes);
      displayAlerts(alerts);
    }
    
    // Save alerts
    if (alerts.length > 0 && MONITORING_CONFIG.enableAlerts) {
      saveAlerts(alerts);
    }
  }
  
  // Generate trends
  if (options.trends && history.length > 1) {
    const trendAnalysis = generateSizeTrends(history);
    trends = trendAnalysis.trends;
    insights = trendAnalysis.insights;
    
    if (!options.quiet) {
      displayTrendsAndInsights(trends, insights);
    }
  }
  
  // Current sizes summary
  if (!options.quiet) {
    log.header('📋 Current Bundle Sizes');
    const totalSize = Array.from(currentChunks.values()).reduce((sum, size) => sum + size, 0);
    
    log.metric('Total Size', totalSize, 'KB');
    
    const sortedChunks = Array.from(currentChunks.entries())
      .sort((a, b) => b[1] - a[1]);
    
    sortedChunks.forEach(([name, size]) => {
      log.metric(`${name}`, size, 'KB');
    });
  }
  
  // Save comprehensive report
  if (options.report) {
    const reportData = {
      currentSizes: Object.fromEntries(currentChunks),
      totalSize: Array.from(currentChunks.values()).reduce((sum, size) => sum + size, 0),
      changes,
      alerts,
      trends,
      insights,
      historyCount: history.length,
      options,
    };
    
    saveMonitoringReport(reportData);
  }
  
  // Exit code based on alerts
  if (alerts.some(alert => alert.type === 'critical')) {
    process.exit(1);
  } else if (alerts.some(alert => alert.type === 'warning')) {
    process.exit(0); // Warning but not failure
  } else {
    process.exit(0);
  }
}

// Run monitoring
main().catch(error => {
  console.error('Bundle monitoring failed:', error);
  process.exit(1);
});