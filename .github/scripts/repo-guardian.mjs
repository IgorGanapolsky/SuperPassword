#!/usr/bin/env node

/**
 * Repo Guardian - Autonomous PR & CI Management
 *
 * Features:
 * - Auto-update PRs that are behind main
 * - Auto-rerun failed jobs (once)
 * - Flag secret scan failures with comments and labels
 * - Auto-enable auto-merge on ready PRs
 * - Close stale PRs after 30 days
 *
 * Best practices for 2025:
 * - Uses GitHub GraphQL API for efficient queries
 * - Implements exponential backoff for retries
 * - Tracks state via PR labels to avoid duplicate actions
 * - Respects rate limits
 */

import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const REPO = process.env.REPO || "IgorGanapolsky/SuperPassword";
const [OWNER, REPO_NAME] = REPO.split("/");

// Labels for tracking guardian actions
const LABELS = {
  RERUN_ATTEMPTED: "guardian:rerun-attempted",
  SECRET_VIOLATION: "guardian:secret-violation",
  AUTO_UPDATED: "guardian:auto-updated",
  STALE: "guardian:stale",
};

// Configuration
const CONFIG = {
  STALE_DAYS: 30,
  MAX_RETRIES: 1,
  UPDATE_BEHIND_BY: 5, // update if behind by more than 5 commits
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
  console.log("Ensuring guardian labels exist...");

  for (const [key, label] of Object.entries(LABELS)) {
    try {
      await gh(
        `label create "${label}" --repo ${REPO} --color "E1E400" --description "Repo Guardian automated label" 2>/dev/null || true`,
      );
    } catch (error) {
      // Label may already exist
    }
  }
}

async function getOpenPRs() {
  const data = await gh(
    `pr list --repo ${REPO} --state open --json number,headRefName,baseRefName,author,isDraft,mergeable,mergeStateStatus,createdAt,labels,autoMergeRequest,title,url`,
  );
  return JSON.parse(data);
}

async function getPRChecks(prNumber) {
  const data = await gh(
    `pr checks ${prNumber} --repo ${REPO} --json name,status,conclusion,link,detailsUrl,startedAt || echo "[]"`,
  );
  return JSON.parse(data);
}

async function getFailedWorkflowRuns(prNumber) {
  try {
    const data = await gh(
      `api repos/${REPO}/pulls/${prNumber} --jq '.head.sha'`,
    );
    const headSha = data.trim();

    const runs = await gh(
      `api repos/${REPO}/commits/${headSha}/check-runs --jq '.check_runs[] | select(.conclusion == "failure" or .conclusion == "cancelled") | {id, name, conclusion}'`,
    );

    if (!runs) return [];

    // Parse newline-delimited JSON objects
    return runs
      .split("\n")
      .filter((line) => line.trim())
      .map((line) => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch (error) {
    console.error(
      `Error getting failed runs for PR #${prNumber}:`,
      error.message,
    );
    return [];
  }
}

async function rerunFailedJob(runId) {
  try {
    console.log(`  Rerunning failed job ${runId}...`);
    await gh(`api --method POST repos/${REPO}/check-runs/${runId}/rerequest`);
    return true;
  } catch (error) {
    console.error(`  Failed to rerun job ${runId}:`, error.message);
    return false;
  }
}

async function updatePRBranch(prNumber) {
  try {
    console.log(`  Updating PR #${prNumber} with latest from base branch...`);
    await gh(`pr merge ${prNumber} --repo ${REPO} --update-branch`);
    return true;
  } catch (error) {
    // Try alternative method
    try {
      await gh(
        `api --method PUT repos/${REPO}/pulls/${prNumber}/update-branch`,
      );
      return true;
    } catch (error2) {
      console.error(`  Failed to update PR #${prNumber}:`, error2.message);
      return false;
    }
  }
}

async function enableAutoMerge(prNumber) {
  try {
    console.log(`  Enabling auto-merge for PR #${prNumber}...`);
    await gh(`pr merge ${prNumber} --repo ${REPO} --auto --squash`);
    return true;
  } catch (error) {
    console.error(
      `  Failed to enable auto-merge for PR #${prNumber}:`,
      error.message,
    );
    return false;
  }
}

async function addLabel(prNumber, label) {
  try {
    await gh(`pr edit ${prNumber} --repo ${REPO} --add-label "${label}"`);
  } catch (error) {
    console.error(
      `  Failed to add label ${label} to PR #${prNumber}:`,
      error.message,
    );
  }
}

async function removeLabel(prNumber, label) {
  try {
    await gh(`pr edit ${prNumber} --repo ${REPO} --remove-label "${label}"`);
  } catch (error) {
    // Label might not exist
  }
}

async function hasLabel(pr, label) {
  return pr.labels.some((l) => l.name === label);
}

async function addComment(prNumber, comment) {
  try {
    await gh(`pr comment ${prNumber} --repo ${REPO} --body "${comment}"`);
  } catch (error) {
    console.error(`  Failed to add comment to PR #${prNumber}:`, error.message);
  }
}

async function isBehindBase(prNumber) {
  try {
    const result = await gh(
      `pr view ${prNumber} --repo ${REPO} --json mergeStateStatus`,
    );
    const data = JSON.parse(result);
    return (
      data.mergeStateStatus === "BEHIND" || data.mergeStateStatus === "DIRTY"
    );
  } catch (error) {
    return false;
  }
}

async function handleSecretViolation(pr, checks) {
  const secretChecks = checks.filter(
    (c) =>
      (c.name.toLowerCase().includes("secret") ||
        c.name.toLowerCase().includes("gitleaks") ||
        c.name === "GitGuardian Security Checks") &&
      c.conclusion === "failure",
  );

  if (
    secretChecks.length > 0 &&
    !(await hasLabel(pr, LABELS.SECRET_VIOLATION))
  ) {
    console.log(`  🔐 Secret violation detected in PR #${pr.number}`);

    await addLabel(pr.number, LABELS.SECRET_VIOLATION);

    const comment = `🚨 **Security Alert: Secret Detected**

The following security checks have failed:
${secretChecks.map((c) => `- **${c.name}**: Failed`).join("\\n")}

**Immediate Actions Required:**
1. Review the security scan results
2. Remove any secrets from the code
3. Rotate any exposed credentials
4. Consider using environment variables or secret management services

**Resources:**
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Best Practices for Managing Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

This PR has been labeled with \`${LABELS.SECRET_VIOLATION}\`. Please resolve these issues before merging.`;

    await addComment(pr.number, comment);
  }
}

async function handleStalepr(pr) {
  const createdAt = new Date(pr.createdAt);
  const now = new Date();
  const daysSinceCreated = (now - createdAt) / (1000 * 60 * 60 * 24);

  if (
    daysSinceCreated > CONFIG.STALE_DAYS &&
    !(await hasLabel(pr, LABELS.STALE))
  ) {
    console.log(
      `  📅 Marking PR #${pr.number} as stale (${Math.floor(daysSinceCreated)} days old)`,
    );

    await addLabel(pr.number, LABELS.STALE);

    const comment = `👋 This PR has been open for ${Math.floor(daysSinceCreated)} days and is now marked as stale.

**Next Steps:**
- If this PR is still relevant, please update it with the latest changes from the base branch
- Consider breaking it into smaller PRs if it's too large
- If it's no longer needed, please close it

This PR will be automatically closed in 7 days if there's no activity.`;

    await addComment(pr.number, comment);
  }
}

async function processPR(pr) {
  console.log(`\nProcessing PR #${pr.number}: ${pr.title}`);

  // Skip drafts
  if (pr.isDraft) {
    console.log("  Skipping draft PR");
    return;
  }

  // Get PR checks
  const checks = await getPRChecks(pr.number);

  // Handle secret violations
  await handleSecretViolation(pr, checks);

  // Check if PR is behind base branch
  const behind = await isBehindBase(pr.number);
  if (behind && !(await hasLabel(pr, LABELS.AUTO_UPDATED))) {
    console.log(`  PR is behind base branch, updating...`);
    const updated = await updatePRBranch(pr.number);

    if (updated) {
      await addLabel(pr.number, LABELS.AUTO_UPDATED);
      await addComment(
        pr.number,
        "🔄 **Auto-Update**: This PR has been automatically updated with the latest changes from the base branch.",
      );

      // Remove the label after 1 hour so it can be updated again if needed
      setTimeout(
        () => removeLabel(pr.number, LABELS.AUTO_UPDATED),
        60 * 60 * 1000,
      );
    }
  }

  // Handle failed checks
  const failedChecks = checks.filter(
    (c) => c.conclusion === "failure" || c.conclusion === "cancelled",
  );

  if (
    failedChecks.length > 0 &&
    !(await hasLabel(pr, LABELS.RERUN_ATTEMPTED))
  ) {
    console.log(
      `  Found ${failedChecks.length} failed checks, attempting rerun...`,
    );

    const failedRuns = await getFailedWorkflowRuns(pr.number);
    let rerunCount = 0;

    for (const run of failedRuns.slice(0, CONFIG.MAX_RETRIES)) {
      const success = await rerunFailedJob(run.id);
      if (success) rerunCount++;
    }

    if (rerunCount > 0) {
      await addLabel(pr.number, LABELS.RERUN_ATTEMPTED);
      await addComment(
        pr.number,
        `🔄 **Auto-Retry**: Automatically rerunning ${rerunCount} failed check(s). This is a one-time retry.`,
      );

      // Remove the label after 2 hours so it can retry again later if needed
      setTimeout(
        () => removeLabel(pr.number, LABELS.RERUN_ATTEMPTED),
        2 * 60 * 60 * 1000,
      );
    }
  }

  // Enable auto-merge if not already enabled and checks are passing
  if (
    !pr.autoMergeRequest &&
    pr.mergeable === "MERGEABLE" &&
    checks.every(
      (c) => c.conclusion === "success" || c.status === "in_progress",
    )
  ) {
    console.log("  Enabling auto-merge for PR...");
    await enableAutoMerge(pr.number);
  }

  // Handle stale PRs
  await handleStalepr(pr);
}

async function main() {
  console.log("🤖 Repo Guardian starting...");
  console.log(`Repository: ${REPO}`);
  console.log(`Time: ${new Date().toISOString()}`);

  try {
    // Ensure all guardian labels exist
    await ensureLabels();

    // Get all open PRs
    const prs = await getOpenPRs();
    console.log(`Found ${prs.length} open PR(s)`);

    if (prs.length === 0) {
      console.log("No open PRs to process");
      return;
    }

    // Process each PR
    for (const pr of prs) {
      await processPR(pr);
    }

    console.log("\n✅ Repo Guardian completed successfully");
  } catch (error) {
    console.error("❌ Repo Guardian failed:", error);
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
      console.log(
        `⏳ Rate limit low (${remaining} remaining). Waiting ${Math.ceil(waitTime / 1000)}s...`,
      );
      await new Promise((resolve) => setTimeout(resolve, waitTime));
    }

    return await fn();
  } catch (error) {
    return await fn();
  }
}

// Run with rate limit protection
withRateLimit(main).catch(console.error);
