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
 * Returns the size of a file in kilobytes.
 * If the file does not exist or an error occurs, returns 0.
 * @param {string} filePath - Path to the file.
 * @return {number} File size in kilobytes, or 0 if unavailable.
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
 * Scans the specified distribution directory and returns a map of JavaScript bundle chunk names to their sizes in kilobytes.
 *
 * Only `.js` files (excluding source maps) are considered. Files are categorized into named chunks based on filename patterns, and sizes are summed for each chunk.
 *
 * @param {string} distPath - The path to the distribution directory containing bundle files.
 * @returns {Map<string, number>} A map where keys are chunk names and values are their sizes in kilobytes.
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
 * Loads and parses the bundle size history from the configured history file.
 * @return {Array} An array of history entries, or an empty array if the file does not exist or cannot be read.
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
 * Saves the bundle size history to the configured history file after cleaning old entries.
 * Ensures the target directory exists before writing. Returns true on success, false on failure.
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
 * Filters and sorts bundle size history entries to retain only those within the configured retention period and limits the total number of entries.
 * @param {Array} history - The array of history entries to clean.
 * @return {Array} The cleaned and sorted array of history entries.
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
 * Retrieves the current Git commit hash (shortened to 8 characters) and branch name.
 * @return {Promise<{commit: string, branch: string}>} An object containing the commit hash and branch name, or 'unknown' values if retrieval fails.
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
 * Creates a new history entry object containing bundle size data, Git information, and build metadata.
 * 
 * @param {Map<string, number>} chunks - Map of chunk names to their sizes in kilobytes.
 * @return {Object} The history entry with timestamp, commit, branch, chunk sizes, total size, critical chunk size, and build info.
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
 * Compares the current bundle size entry to the previous history entry, identifying significant size changes per chunk and overall.
 *
 * Calculates percentage growth for each chunk and the total bundle size, generating alerts if growth exceeds configured thresholds. Only changes greater than 1% are tracked.
 *
 * @param {Object} currentEntry - The current bundle size entry.
 * @param {Array<Object>} history - Array of previous bundle size entries.
 * @return {Object} An object containing arrays of detected changes and generated alerts.
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
 * Creates a new alert object with a unique ID, timestamp, type, category, message, details, and unresolved status.
 * @param {string} type - The alert type, such as 'warning' or 'critical'.
 * @param {string} category - The category of the alert (e.g., 'chunk', 'total').
 * @param {string} message - A descriptive message for the alert.
 * @param {object} details - Additional details relevant to the alert.
 * @return {object} The constructed alert object.
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
 * Displays formatted bundle size changes in the console, highlighting increases and decreases with color-coded arrows.
 * If no significant changes are present, logs an informational message.
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
 * Displays bundle size alerts in the console, formatting critical alerts as errors and warnings as warnings.
 * @param {Array} alerts - The list of alert objects to display.
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
 * Analyzes recent bundle size history to identify growth trends and generate insights.
 *
 * Examines the last several history entries to calculate total size growth, detect significant increases or decreases, and identify consecutive growth periods.
 *
 * @param {Array} history - Array of history entries containing bundle size data.
 * @return {{ trends: Array, insights: Array }} An object with trend summaries and human-readable insights.
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
 * Displays bundle size trends and insights in a formatted console output.
 * 
 * @param {Array} trends - Array of trend summary objects, each containing period, startSize, endSize, and totalGrowth.
 * @param {Array} insights - Array of insight strings to be displayed.
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
 * Saves a comprehensive monitoring report to the configured report file, including the provided data and a timestamp.
 * If the target directory does not exist, it is created recursively.
 * Logs a success message on completion or a warning if saving fails.
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
 * Appends new alerts to the alerts file, retaining only the most recent 50 alerts.
 * Logs a success message on completion or a warning if saving fails.
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
 * Parses command-line arguments to determine which monitoring operations to perform.
 * @return {Object} An options object indicating which actions are enabled (record, analyze, trends, report, quiet).
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
 * Orchestrates the bundle size monitoring workflow based on CLI options.
 *
 * Executes steps to record current bundle sizes, analyze changes against history, generate alerts, display trends and insights, and save reports. Exits with a nonzero code if critical alerts are detected, or zero otherwise.
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