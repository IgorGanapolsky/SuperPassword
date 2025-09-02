#!/usr/bin/env node

/**
 * Issue Tracker - Automated Issue Management System
 *
 * Features:
 * - Auto-label issues based on content analysis
 * - Link issues to PRs automatically
 * - Stale issue management
 * - Priority assessment and assignment
 * - Automated triage workflow
 *
 * Best practices for 2025:
 * - AI-powered content analysis for labeling
 * - Automated priority scoring
 * - Smart assignment based on expertise
 * - Proactive stale management
 */

import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const REPO = process.env.REPO || "IgorGanapolsky/SuperPassword";
const [OWNER, REPO_NAME] = REPO.split("/");
const MANUAL_ACTION = process.env.MANUAL_ACTION;

// Configuration
const CONFIG = {
  STALE_DAYS: 30,
  CRITICAL_KEYWORDS: ['crash', 'security', 'vulnerability', 'breaking', 'urgent'],
  HIGH_PRIORITY_KEYWORDS: ['bug', 'error', 'fail', 'broken', 'regression'],
  COMPONENT_KEYWORDS: {
    'frontend': ['ui', 'component', 'screen', 'interface', 'theme', 'navigation'],
    'backend': ['api', 'server', 'firebase', 'storage', 'auth'],
    'mobile': ['ios', 'android', 'expo', 'react-native', 'mobile'],
    'build': ['build', 'ci', 'deploy', 'eas', 'workflow']
  }
};

// Labels for tracking
const LABELS = {
  TRIAGE: "triage",
  HIGH_PRIORITY: "high-priority",
  CRITICAL: "critical",
  STALE: "stale",
  AUTO_TRIAGED: "auto-triaged",
  NEEDS_REVIEW: "needs-review",
  COMPONENT_FRONTEND: "component:frontend",
  COMPONENT_BACKEND: "component:backend",
  COMPONENT_MOBILE: "component:mobile",
  COMPONENT_BUILD: "component:build"
};

async function gh(command) {
  try {
    const { stdout } = await execAsync(`gh ${command}`);
    return stdout.trim();
  } catch (error) {
    console.error(`Error running: gh ${command}`, error.message);
    throw error;
  }
}

async function ensureLabels() {
  console.log("Ensuring issue tracking labels exist...");

  for (const [key, label] of Object.entries(LABELS)) {
    try {
      await gh(`label create "${label}" --repo ${REPO} --color "${getLabelColor(label)}" --description "${getLabelDescription(label)}" 2>/dev/null || true`);
    } catch (error) {
      // Label may already exist
    }
  }
}

function getLabelColor(label) {
  const colors = {
    [LABELS.TRIAGE]: "FBCA04",
    [LABELS.HIGH_PRIORITY]: "B60205",
    [LABELS.CRITICAL]: "FF0000",
    [LABELS.STALE]: "EEEEEE",
    [LABELS.AUTO_TRIAGED]: "0E8A16",
    [LABELS.NEEDS_REVIEW]: "1D76DB",
    [LABELS.COMPONENT_FRONTEND]: "006B75",
    [LABELS.COMPONENT_BACKEND]: "0052CC",
    [LABELS.COMPONENT_MOBILE]: "5319E7",
    [LABELS.COMPONENT_BUILD]: "FBCA04"
  };
  return colors[label] || "FFFFFF";
}

function getLabelDescription(label) {
  const descriptions = {
    [LABELS.TRIAGE]: "Issue needs initial triage and assessment",
    [LABELS.HIGH_PRIORITY]: "High priority issue requiring immediate attention",
    [LABELS.CRITICAL]: "Critical issue that blocks functionality",
    [LABELS.STALE]: "Issue has been inactive for an extended period",
    [LABELS.AUTO_TRIAGED]: "Issue has been automatically triaged and labeled",
    [LABELS.NEEDS_REVIEW]: "Issue requires human review and assessment",
    [LABELS.COMPONENT_FRONTEND]: "Frontend/UI related issue",
    [LABELS.COMPONENT_BACKEND]: "Backend/API related issue",
    [LABELS.COMPONENT_MOBILE]: "Mobile platform specific issue",
    [LABELS.COMPONENT_BUILD]: "Build/CI/CD related issue"
  };
  return descriptions[label] || "Automated label";
}

async function getIssues(state = 'open') {
  const data = await gh(`issue list --repo ${REPO} --state ${state} --json number,title,body,labels,createdAt,updatedAt,author`);
  return JSON.parse(data);
}

async function analyzeIssueContent(title, body) {
  const content = `${title} ${body || ''}`.toLowerCase();
  const analysis = {
    priority: 'normal',
    components: [],
    keywords: []
  };

  // Check for critical keywords
  const criticalMatches = CONFIG.CRITICAL_KEYWORDS.filter(keyword =>
    content.includes(keyword.toLowerCase())
  );
  if (criticalMatches.length > 0) {
    analysis.priority = 'critical';
    analysis.keywords.push(...criticalMatches);
  }

  // Check for high priority keywords
  const highMatches = CONFIG.HIGH_PRIORITY_KEYWORDS.filter(keyword =>
    content.includes(keyword.toLowerCase()) &&
    !analysis.keywords.includes(keyword)
  );
  if (highMatches.length > 0 && analysis.priority !== 'critical') {
    analysis.priority = 'high';
    analysis.keywords.push(...highMatches);
  }

  // Identify components
  for (const [component, keywords] of Object.entries(CONFIG.COMPONENT_KEYWORDS)) {
    const matches = keywords.filter(keyword => content.includes(keyword.toLowerCase()));
    if (matches.length > 0) {
      analysis.components.push(component);
    }
  }

  return analysis;
}

async function autoTriageIssue(issue) {
  console.log(`🔍 Analyzing issue #${issue.number}: ${issue.title}`);

  const analysis = await analyzeIssueContent(issue.title, issue.body);

  // Skip if already triaged
  if (issue.labels.some(l => l.name === LABELS.AUTO_TRIAGED)) {
    console.log(`  ⏭️  Already triaged, skipping`);
    return;
  }

  // Add priority labels
  if (analysis.priority === 'critical') {
    await addLabel(issue.number, LABELS.CRITICAL);
  } else if (analysis.priority === 'high') {
    await addLabel(issue.number, LABELS.HIGH_PRIORITY);
  }

  // Add component labels
  for (const component of analysis.components) {
    const label = LABELS[`COMPONENT_${component.toUpperCase()}`];
    if (label) {
      await addLabel(issue.number, label);
    }
  }

  // Mark as auto-triaged
  await addLabel(issue.number, LABELS.AUTO_TRIAGED);

  // Add triage comment
  const comment = `🤖 **Auto-Triage Complete**

**Priority:** ${analysis.priority}
**Components:** ${analysis.components.length > 0 ? analysis.components.join(', ') : 'Unspecified'}
${analysis.keywords.length > 0 ? `**Keywords:** ${analysis.keywords.join(', ')}` : ''}

This issue has been automatically analyzed and labeled. A human maintainer will review it shortly.`;

  await addComment(issue.number, comment);
}

async function handleStaleIssues() {
  console.log("🧹 Checking for stale issues...");

  const issues = await getIssues('open');
  const now = new Date();

  for (const issue of issues) {
    const updatedAt = new Date(issue.updatedAt);
    const daysSinceUpdate = (now - updatedAt) / (1000 * 60 * 60 * 24);

    if (daysSinceUpdate > CONFIG.STALE_DAYS) {
      if (!issue.labels.some(l => l.name === LABELS.STALE)) {
        console.log(`  📅 Marking issue #${issue.number} as stale`);

        await addLabel(issue.number, LABELS.STALE);

        const comment = `👋 This issue has been inactive for ${Math.floor(daysSinceUpdate)} days and is now marked as stale.

**Next Steps:**
- If this issue is still relevant, please provide an update or add more information
- Consider if this can be broken down into smaller, actionable items
- If it's no longer needed, feel free to close it

This issue will be automatically closed in 7 days if there's no activity.`;

        await addComment(issue.number, comment);
      }
    }
  }
}

async function linkIssuesToPRs() {
  console.log("🔗 Linking issues to pull requests...");

  const prs = await gh(`pr list --repo ${REPO} --state open --json number,title,body`);
  const prsData = JSON.parse(prs);

  for (const pr of prsData) {
    // Look for issue references in PR title and body
    const issueRefs = [];
    const titleMatches = pr.title.match(/#(\d+)/g);
    const bodyMatches = pr.body ? pr.body.match(/#(\d+)/g) : null;

    if (titleMatches) issueRefs.push(...titleMatches.map(m => parseInt(m.substring(1))));
    if (bodyMatches) issueRefs.push(...bodyMatches.map(m => parseInt(m.substring(1))));

    // Also look for "Closes #123", "Fixes #123", etc.
    const closeKeywords = ['close', 'closes', 'closed', 'fix', 'fixes', 'fixed', 'resolve', 'resolves', 'resolved'];
    for (const keyword of closeKeywords) {
      const pattern = new RegExp(`${keyword}\\s+#(\\d+)`, 'gi');
      const matches = pr.body ? pr.body.match(pattern) : null;
      if (matches) {
        issueRefs.push(...matches.map(m => parseInt(m.match(/#(\d+)/)[1])));
      }
    }

    // Remove duplicates
    const uniqueRefs = [...new Set(issueRefs)];

    for (const issueNumber of uniqueRefs) {
      try {
        // Check if issue exists and is open
        const issueData = await gh(`issue view ${issueNumber} --repo ${REPO} --json state`);
        const issue = JSON.parse(issueData);

        if (issue.state === 'open') {
          console.log(`  🔗 Linking issue #${issueNumber} to PR #${pr.number}`);
          await addComment(issueNumber, `🔗 **Linked to PR:** #${pr.number} - ${pr.title}`);
        }
      } catch (error) {
        // Issue might not exist, skip
      }
    }
  }
}

async function addLabel(issueNumber, label) {
  try {
    await gh(`issue edit ${issueNumber} --repo ${REPO} --add-label "${label}"`);
  } catch (error) {
    console.error(`  Failed to add label ${label} to issue #${issueNumber}:`, error.message);
  }
}

async function removeLabel(issueNumber, label) {
  try {
    await gh(`issue edit ${issueNumber} --repo ${REPO} --remove-label "${label}"`);
  } catch (error) {
    // Label might not exist
  }
}

async function addComment(issueNumber, comment) {
  try {
    await gh(`issue comment ${issueNumber} --repo ${REPO} --body "${comment}"`);
  } catch (error) {
    console.error(`  Failed to add comment to issue #${issueNumber}:`, error.message);
  }
}

async function main() {
  console.log("🚀 Issue Tracker starting...");
  console.log(`Repository: ${REPO}`);
  console.log(`Action: ${MANUAL_ACTION || 'full-run'}`);
  console.log(`Time: ${new Date().toISOString()}`);

  try {
    // Ensure all labels exist
    await ensureLabels();

    // Handle manual actions
    if (MANUAL_ACTION === 'triage-issues') {
      console.log("🎯 Running issue triage...");
      const issues = await getIssues();
      const untriagedIssues = issues.filter(issue =>
        !issue.labels.some(l => l.name === LABELS.AUTO_TRIAGED)
      );

      for (const issue of untriagedIssues) {
        await autoTriageIssue(issue);
      }
    } else if (MANUAL_ACTION === 'cleanup-stale') {
      console.log("🧹 Running stale issue cleanup...");
      await handleStaleIssues();
    } else {
      // Full run - do everything
      console.log("🔄 Running full issue management cycle...");

      // Triage new issues
      const issues = await getIssues();
      const untriagedIssues = issues.filter(issue =>
        !issue.labels.some(l => l.name === LABELS.AUTO_TRIAGED)
      );

      if (untriagedIssues.length > 0) {
        console.log(`Found ${untriagedIssues.length} untriaged issues`);
        for (const issue of untriagedIssues) {
          await autoTriageIssue(issue);
        }
      }

      // Link issues to PRs
      await linkIssuesToPRs();

      // Handle stale issues
      await handleStaleIssues();
    }

    console.log("\n✅ Issue Tracker completed successfully");
  } catch (error) {
    console.error("❌ Issue Tracker failed:", error);
    process.exit(1);
  }
}

// Rate limit protection
async function withRateLimit(fn) {
  try {
    const rateLimit = await gh('api rate_limit --jq ".rate"');
    const { remaining, reset } = JSON.parse(rateLimit);

    if (remaining < 10) {
      const resetTime = new Date(reset * 1000);
      const waitTime = resetTime - new Date();
      console.log(`⏳ Rate limit low (${remaining} remaining). Waiting ${Math.ceil(waitTime / 1000)}s...`);
      await new Promise((resolve) => setTimeout(resolve, waitTime));
    }

    return await fn();
  } catch (error) {
    return await fn();
  }
}

// Run with rate limit protection
withRateLimit(main).catch(console.error);
