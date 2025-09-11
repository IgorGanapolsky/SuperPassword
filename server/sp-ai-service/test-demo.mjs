#!/usr/bin/env node

/**
 * SuperPassword AI Intelligence Demo
 * This script demonstrates the powerful AI features of our Eko-powered service
 */

import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

const API_BASE = 'http://localhost:3001';
const API_VERSION = 'v1';

// Mock authentication token (works in development mode)
const AUTH_TOKEN = 'mock-dev-token';

const headers = {
  'Authorization': `Bearer ${AUTH_TOKEN}`,
  'Content-Type': 'application/json'
};

// Sample password data for testing (realistic but safe examples)
const samplePasswords = [
  {
    id: '1',
    site: 'gmail.com',
    username: 'user@example.com',
    password: 'MyPassword123!',
    lastUpdated: '2024-01-15T10:00:00Z',
    category: 'email'
  },
  {
    id: '2',
    site: 'bankofamerica.com',
    username: 'johndoe',
    password: 'password123',  // Intentionally weak
    lastUpdated: '2023-06-01T10:00:00Z',
    category: 'financial'
  },
  {
    id: '3',
    site: 'facebook.com',
    username: 'john.doe@email.com',
    password: 'MyPassword123!', // Duplicate of #1
    lastUpdated: '2024-02-10T10:00:00Z',
    category: 'social'
  },
  {
    id: '4',
    site: 'amazon.com',
    username: 'johndoe123',
    password: 'Str0ngP@ssw0rd!2024',
    lastUpdated: '2024-11-01T10:00:00Z',
    category: 'shopping'
  },
  {
    id: '5',
    site: 'linkedin.com',
    username: 'john.doe',
    password: 'linkedin2020',  // Weak and stale
    lastUpdated: '2020-03-15T10:00:00Z',
    category: 'professional'
  }
];

const colors = {
  reset: '\\x1b[0m',
  bright: '\\x1b[1m',
  red: '\\x1b[31m',
  green: '\\x1b[32m',
  yellow: '\\x1b[33m',
  blue: '\\x1b[34m',
  magenta: '\\x1b[35m',
  cyan: '\\x1b[36m'
};

function log(color, message) {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function header(title) {
  console.log('\\n' + '='.repeat(60));
  log('bright', `🧠 ${title}`);
  console.log('='.repeat(60));
}

function subheader(title) {
  console.log('\\n' + '-'.repeat(40));
  log('cyan', `📊 ${title}`);
  console.log('-'.repeat(40));
}

async function checkHealth() {
  try {
    const response = await axios.get(`${API_BASE}/health/detailed`);
    const health = response.data;
    
    header('🏥 AI SERVICE HEALTH CHECK');
    
    log('green', `✅ Service Status: ${health.status.toUpperCase()}`);
    log('blue', `⏰ Uptime: ${Math.round(health.uptime)} seconds`);
    log('blue', `🔗 Node Version: ${health.system.nodeVersion}`);
    log('blue', `💾 Memory Usage: ${health.system.memoryUsage.heapUsed}MB / ${health.system.memoryUsage.heapTotal}MB`);
    
    console.log('\\n🔧 Dependencies:');
    console.log(`  • Eko Service: ${health.dependencies.ekoService}`);
    console.log(`  • Firebase Service: ${health.dependencies.firebaseService}`);
    
    console.log('\\n🤖 AI Providers:');
    Object.entries(health.dependencies.llmProviders).forEach(([provider, status]) => {
      const emoji = status === 'configured' ? '✅' : '❌';
      console.log(`  ${emoji} ${provider.charAt(0).toUpperCase() + provider.slice(1)}: ${status}`);
    });
    
    return health.status === 'healthy';
  } catch (error) {
    log('red', `❌ Health check failed: ${error.message}`);
    return false;
  }
}

async function demoVaultAudit() {
  try {
    header('🔍 VAULT SECURITY AUDIT DEMO');
    
    const auditRequest = {
      requestId: uuidv4(),
      passwords: samplePasswords,
      analysisDepth: 'comprehensive',
      includeBreachCheck: true,
      includeTrendAnalysis: false
    };
    
    log('blue', `🔐 Analyzing ${auditRequest.passwords.length} passwords...`);
    console.log('\\nPassword entries:');
    auditRequest.passwords.forEach((pwd, i) => {
      console.log(`  ${i + 1}. ${pwd.site} (${pwd.username}) - Updated: ${pwd.lastUpdated?.substring(0, 10) || 'Unknown'}`);
    });
    
    const response = await axios.post(`${API_BASE}/api/${API_VERSION}/intelligence/audit`, auditRequest, { headers });
    const result = response.data;
    
    if (result.success) {
      const audit = result.data;
      
      subheader('🎯 SECURITY ANALYSIS RESULTS');
      
      // Overall Score
      const scoreColor = audit.securityScore >= 80 ? 'green' : audit.securityScore >= 60 ? 'yellow' : 'red';
      log(scoreColor, `🏆 Security Score: ${audit.securityScore}/100`);
      log(scoreColor, `⚠️  Risk Level: ${audit.riskLevel}`);
      
      // Summary
      console.log('\\n📋 Executive Summary:');
      console.log(`${audit.summary}`);
      
      // Key Metrics
      if (audit.keyMetrics) {
        console.log('\\n📊 Key Metrics:');
        console.log(`  • Total Passwords: ${audit.keyMetrics.totalPasswords}`);
        console.log(`  • Weak Passwords: ${audit.keyMetrics.weakPasswordCount}`);
        console.log(`  • Breached Passwords: ${audit.keyMetrics.breachedPasswordCount}`);
        console.log(`  • Duplicate Passwords: ${audit.keyMetrics.duplicatePasswordCount}`);
        console.log(`  • Stale Passwords: ${audit.keyMetrics.stalePasswordCount}`);
        console.log(`  • Average Age: ${audit.keyMetrics.averagePasswordAge} days`);
        console.log(`  • Strong Passwords: ${audit.keyMetrics.strongPasswordsPercentage}%`);
      }
      
      // Recommendations
      if (audit.recommendations && audit.recommendations.length > 0) {
        console.log('\\n💡 AI Recommendations:');
        audit.recommendations.forEach((rec, i) => {
          console.log(`  ${i + 1}. ${rec}`);
        });
      }
      
      // Priority Actions
      if (audit.priorityActions && audit.priorityActions.length > 0) {
        console.log('\\n🚨 Priority Actions:');
        audit.priorityActions.forEach((action, i) => {
          console.log(`  ${i + 1}. ${action}`);
        });
      }
      
      // Performance
      console.log('\\n⚡ Performance:');
      console.log(`  • Processing Time: ${result.meta?.processingTime}ms`);
      console.log(`  • Next Review: ${new Date(audit.nextReviewDate).toLocaleDateString()}`);
      
      return audit;
    } else {
      log('red', `❌ Audit failed: ${result.error?.message}`);
      return null;
    }
    
  } catch (error) {
    log('red', `❌ Vault audit demo failed: ${error.response?.data?.error?.message || error.message}`);
    return null;
  }
}

async function demoPhishingCheck() {
  try {
    header('🎣 PHISHING DETECTION DEMO');
    
    // Test various URLs (safe examples)
    const testUrls = [
      { url: 'https://google.com', expected: 'LOW' },
      { url: 'https://github.com', expected: 'LOW' },
      { url: 'https://g00gle.com', expected: 'HIGH' }, // Suspicious lookalike
      { url: 'https://paypal-security-update.suspicious-site.com', expected: 'CRITICAL' }, // Obvious phishing pattern
      { url: 'https://amaz0n-login.fake-domain.org', expected: 'HIGH' } // Another suspicious example
    ];
    
    for (const test of testUrls) {
      console.log(`\\n🔍 Checking: ${test.url}`);
      
      const checkRequest = {
        requestId: uuidv4(),
        url: test.url,
        context: 'User clicked on email link'
      };
      
      try {
        const response = await axios.post(`${API_BASE}/api/${API_VERSION}/intelligence/phishing-check`, checkRequest, { headers });
        const result = response.data;
        
        if (result.success) {
          const check = result.data;
          
          const riskColor = check.riskLevel === 'LOW' ? 'green' : 
                           check.riskLevel === 'MEDIUM' ? 'yellow' : 'red';
          
          log(riskColor, `  Risk Level: ${check.riskLevel}`);
          console.log(`  Phishing: ${check.isPhishing ? 'YES ⚠️' : 'No ✅'}`);
          console.log(`  Confidence: ${check.confidence}%`);
          console.log(`  Recommendation: ${check.recommendation}`);
          
          if (check.indicators && check.indicators.length > 0) {
            console.log('  Risk Indicators:');
            check.indicators.forEach(indicator => {
              console.log(`    • ${indicator.description}`);
            });
          }
        }
      } catch (error) {
        log('red', `  ❌ Check failed: ${error.response?.data?.error?.message || error.message}`);
      }
      
      // Small delay between checks
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
  } catch (error) {
    log('red', `❌ Phishing demo failed: ${error.message}`);
  }
}

async function demoRotationPlan() {
  try {
    header('🔄 PASSWORD ROTATION PLANNING DEMO');
    
    const rotationRequest = {
      requestId: uuidv4(),
      passwords: samplePasswords,
      prioritySites: ['bankofamerica.com', 'gmail.com'],
      rotationFrequency: 'monthly',
      userPreferences: {
        maxPasswordsPerWeek: 2,
        preferredDays: ['monday', 'wednesday'],
        avoidBusyPeriods: true,
        reminderPreference: 'push'
      }
    };
    
    log('blue', `📅 Generating rotation plan for ${rotationRequest.passwords.length} passwords...`);
    console.log(`🎯 Priority sites: ${rotationRequest.prioritySites.join(', ')}`);
    console.log(`⏰ Frequency: ${rotationRequest.rotationFrequency}`);
    
    const response = await axios.post(`${API_BASE}/api/${API_VERSION}/intelligence/rotation-plan`, rotationRequest, { headers });
    const result = response.data;
    
    if (result.success) {
      const plan = result.data;
      
      subheader('📋 ROTATION PLAN RESULTS');
      
      console.log(`📊 Total Passwords: ${plan.totalPasswords}`);
      console.log(`⏱️  Estimated Time: ${plan.estimatedTimeRequired} hours`);
      console.log(`🎯 Critical Priority: ${plan.criticalPriority?.length || 0} passwords`);
      console.log(`📅 Completion Estimate: ${new Date(plan.completionEstimate).toLocaleDateString()}`);
      
      if (plan.rotationSchedule && plan.rotationSchedule.length > 0) {
        console.log('\\n📅 Rotation Schedule (First 5):');
        plan.rotationSchedule.slice(0, 5).forEach((item, i) => {
          const priorityColor = item.priority === 'IMMEDIATE' ? 'red' : 
                               item.priority === 'HIGH' ? 'yellow' : 'green';
          log(priorityColor, `  ${i + 1}. ${item.site} - ${item.priority} (${item.estimatedMinutes} min)`);
          console.log(`     Scheduled: ${new Date(item.scheduledDate).toLocaleDateString()}`);
        });
      }
      
      if (plan.monthlyBreakdown && plan.monthlyBreakdown.length > 0) {
        console.log('\\n📊 Monthly Breakdown:');
        plan.monthlyBreakdown.forEach(month => {
          console.log(`  ${month.month}: ${month.passwordCount} passwords (${month.estimatedHours}h)`);
        });
      }
      
      console.log('\\n📝 Summary:');
      console.log(plan.summary);
      
      return plan;
    } else {
      log('red', `❌ Rotation plan failed: ${result.error?.message}`);
      return null;
    }
    
  } catch (error) {
    if (error.response?.status === 403) {
      log('yellow', '⚠️  Rotation planning requires Pro tier (this is expected in demo)');
      console.log('   In production, this would show upgrade options');
    } else {
      log('red', `❌ Rotation plan demo failed: ${error.response?.data?.error?.message || error.message}`);
    }
    return null;
  }
}

async function demoAuditHistory() {
  try {
    header('📈 AUDIT HISTORY & TRENDS DEMO');
    
    log('blue', '📊 Fetching audit history...');
    
    const response = await axios.get(`${API_BASE}/api/${API_VERSION}/intelligence/audit-history?limit=5`, { headers });
    const result = response.data;
    
    if (result.success && result.data.length > 0) {
      console.log('\\n📋 Recent Audits:');
      result.data.forEach((audit, i) => {
        const scoreColor = audit.securityScore >= 80 ? 'green' : audit.securityScore >= 60 ? 'yellow' : 'red';
        console.log(`  ${i + 1}. ${new Date(audit.timestamp).toLocaleDateString()}`);
        log(scoreColor, `     Score: ${audit.securityScore}/100`);
        console.log(`     Passwords: ${audit.totalPasswords}`);
        console.log(`     Weak: ${audit.weakPasswordCount}, Breached: ${audit.breachedPasswordCount}`);
      });
      
      // Show trend
      const scores = result.data.map(a => a.securityScore).reverse();
      if (scores.length >= 2) {
        const trend = scores[scores.length - 1] - scores[0];
        const trendColor = trend > 0 ? 'green' : trend < 0 ? 'red' : 'yellow';
        log(trendColor, `\\n📈 Trend: ${trend > 0 ? '+' : ''}${trend} points over time`);
      }
    } else {
      log('yellow', '📊 No audit history found (using mock data for demo)');
    }
    
  } catch (error) {
    log('red', `❌ Audit history demo failed: ${error.message}`);
  }
}

async function runFullDemo() {
  console.log('🚀 Starting SuperPassword AI Intelligence Demo...\\n');
  
  // Check if service is healthy
  const isHealthy = await checkHealth();
  if (!isHealthy) {
    log('red', '❌ Service not healthy. Please check your setup and try again.');
    process.exit(1);
  }
  
  // Run all demos
  await demoVaultAudit();
  await demoPhishingCheck();
  await demoRotationPlan();
  await demoAuditHistory();
  
  // Summary
  header('🎉 DEMO COMPLETE');
  log('green', '✅ SuperPassword AI Intelligence System is fully operational!');
  console.log('\\n🔗 Next Steps:');
  console.log('  1. Visit http://localhost:3001/docs for full API documentation');
  console.log('  2. Configure your API keys in .env for production features');
  console.log('  3. Integrate with React Native mobile app');
  console.log('  4. Set up tier-based monetization');
  console.log('\\n🚀 Your password manager now has AI superpowers!');
}

// Handle command line arguments
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log('SuperPassword AI Intelligence Demo');
  console.log('');
  console.log('Usage: node test-demo.js [options]');
  console.log('');
  console.log('Options:');
  console.log('  --health         Run health check only');
  console.log('  --audit          Run vault audit demo only');
  console.log('  --phishing       Run phishing check demo only');
  console.log('  --rotation       Run rotation planning demo only');
  console.log('  --history        Run audit history demo only');
  console.log('  --help, -h       Show this help message');
  console.log('');
  process.exit(0);
}

// Run specific demos based on arguments
if (args.includes('--health')) {
  checkHealth();
} else if (args.includes('--audit')) {
  checkHealth().then(() => demoVaultAudit());
} else if (args.includes('--phishing')) {
  checkHealth().then(() => demoPhishingCheck());
} else if (args.includes('--rotation')) {
  checkHealth().then(() => demoRotationPlan());
} else if (args.includes('--history')) {
  checkHealth().then(() => demoAuditHistory());
} else {
  // Run full demo
  runFullDemo();
}
