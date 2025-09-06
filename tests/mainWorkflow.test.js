/**
 * Tests for the SuperPassword Main Pipeline GitHub Actions workflow.
 * Framework: Uses the project's existing test runner (Jest/Vitest-style globals: describe/it/expect).
 * These tests avoid external YAML deps by verifying critical semantics via robust text-based assertions.
 * They search .github/workflows for a file whose 'name:' is 'SuperPassword Main Pipeline'.
 */

const fs = require('fs');
const path = require('path');

function readWorkflowFile() {
  const wfDir = path.join(process.cwd(), '.github', 'workflows');
  expect(fs.existsSync(wfDir)).toBe(true);
  const candidates = fs.readdirSync(wfDir).filter(f => /\.(ya?ml)$/.test(f));
  expect(candidates.length).toBeGreaterThan(0);
  const matches = candidates
    .map(f => path.join(wfDir, f))
    .filter(fp => {
      try {
        const s = fs.readFileSync(fp, 'utf8');
        return /^\s*name:\s*SuperPassword Main Pipeline\b/m.test(s);
      } catch { return false; }
    });
  expect(matches.length).toBeGreaterThan(0);
  // choose first match deterministically
  return matches.sort()[0];
}

function getWorkflowText() {
  const fp = readWorkflowFile();
  const txt = fs.readFileSync(fp, 'utf8');
  expect(txt && txt.length > 0).toBe(true);
  return { fp, txt };
}

describe('SuperPassword Main Pipeline workflow', () => {
  it('defines the correct workflow name and top-level triggers', () => {
    const { txt } = getWorkflowText();
    expect(/^\s*name:\s*SuperPassword Main Pipeline\b/m.test(txt)).toBe(true);

    // on: workflow_dispatch
    expect(/^\s*on:\s*\n(?:.|\n)*?\bworkflow_dispatch:\s*\{\s*\}/m.test(txt)).toBe(true);

    // on: push to develop and main with paths-ignore
    expect(/^\s*push:\s*\n(?:.|\n)*?^\s*branches:\s*\n\s*-\s*develop\s*\n\s*-\s*main/m.test(txt)).toBe(true);
    expect(/^\s*push:\s*\n(?:.|\n)*?^\s*paths-ignore:\s*\n\s*-\s*"\*\*\.md"\s*\n\s*-\s*"docs\/\*\*"/m.test(txt)).toBe(true);

    // on: pull_request to develop and main with paths-ignore
    expect(/^\s*pull_request:\s*\n(?:.|\n)*?^\s*branches:\s*\n\s*-\s*develop\s*\n\s*-\s*main/m.test(txt)).toBe(true);
    expect(/^\s*pull_request:\s*\n(?:.|\n)*?^\s*paths-ignore:\s*\n\s*-\s*"\*\*\.md"\s*\n\s*-\s*"docs\/\*\*"/m.test(txt)).toBe(true);

    // on: schedule every 30 minutes
    expect(/^\s*schedule:\s*\n\s*-\s*cron:\s*"\*\/30 \* \* \* \*"/m.test(txt)).toBe(true);

    // on: issues and issue_comment types
    expect(/^\s*issues:\s*\n\s*types:\s*\[opened,\s*edited,\s*labeled,\s*unlabeled,\s*reopened,\s*assigned,\s*unassigned\]/m.test(txt)).toBe(true);
    expect(/^\s*issue_comment:\s*\n\s*types:\s*\[created\]/m.test(txt)).toBe(true);
  });

  it('sets conservative permissions including id-token: write', () => {
    const { txt } = getWorkflowText();
    const permsBlock = /(^\s*permissions:\s*\n(?:^\s{2,}.+\n)+)/m.exec(txt);
    expect(permsBlock).toBeTruthy();
    expect(permsBlock[1]).toMatch(/^\s*contents:\s*read\b/m);
    expect(permsBlock[1]).toMatch(/^\s*issues:\s*write\b/m);
    expect(permsBlock[1]).toMatch(/^\s*pull-requests:\s*write\b/m);
    expect(permsBlock[1]).toMatch(/^\s*security-events:\s*write\b/m);
    expect(permsBlock[1]).toMatch(/^\s*checks:\s*write\b/m);
    expect(permsBlock[1]).toMatch(/^\s*statuses:\s*write\b/m);
    expect(permsBlock[1]).toMatch(/^\s*id-token:\s*write\b/m);
  });

  it('configures CodeQL job gated on push or pull_request', () => {
    const { txt } = getWorkflowText();
    const job = /(^\s*codeql:\s*\n(?:^\s{2,}.+\n)+)/m.exec(txt);
    expect(job).toBeTruthy();
    const block = job[1];
    expect(block).toMatch(/^\s*name:\s*CodeQL\b/m);
    expect(block).toMatch(/^\s*runs-on:\s*ubuntu-latest\b/m);
    expect(block).toMatch(/^\s*if:\s*github\.event_name == 'push' \|\| github\.event_name == 'pull_request'/m);
    expect(block).toMatch(/^\s*uses:\s*actions\/checkout@v4/m);
    expect(block).toMatch(/^\s*uses:\s*github\/codeql-action\/init@v3/m);
    expect(block).toMatch(/^\s*with:\s*\n\s*languages:\s*javascript\b/m);
    expect(block).toMatch(/^\s*uses:\s*actions\/setup-node@v4/m);
    expect(block).toMatch(/^\s*node-version:\s*"20"/m);
    expect(block).toMatch(/npm ci --legacy-peer-deps/);
    expect(block).toMatch(/github\/codeql-action\/analyze@v3/);
  });

  it('configures Validate job dependent on codeql with caching, type-check, lint, tests, coverage upload, and SonarCloud', () => {
    const { txt } = getWorkflowText();
    const job = /(^\s*validate:\s*\n(?:^\s{2,}.+\n)+?)(?=^\s*\S)/m.exec(txt);
    expect(job).toBeTruthy();
    const block = job[1];
    expect(block).toMatch(/^\s*needs:\s*codeql\b/m);
    expect(block).toMatch(/^\s*runs-on:\s*ubuntu-latest\b/m);
    expect(block).toMatch(/^\s*Cache dependencies/m);
    expect(block).toMatch(/actions\/cache@v3/);
    expect(block).toMatch(/path:\s*\|\n\s*node_modules\n\s*~\/\.npm\n\s*~\/\.expo/m);
    expect(block).toMatch(/Install dependencies[\s\S]*npm ci --legacy-peer-deps/);
    expect(block).toMatch(/Align Expo dependencies[\s\S]*npx expo install --fix --non-interactive \|\| true/);
    expect(block).toMatch(/Type check[\s\S]*npx tsc --noEmit/);
    expect(block).toMatch(/Lint[\s\S]*npm run lint[\s\S]*npm run fmt/);
    expect(block).toMatch(/Test[\s\S]*npm test -- --coverage/);
    expect(block).toMatch(/Upload coverage[\s\S]*codecov\/codecov-action@v3/);
    expect(block).toMatch(/SonarCloud Analysis[\s\S]*SonarSource\/sonarcloud-github-action@master/);
  });

  it('sets up Security job with OWASP Dependency Check, SARIF upload, and Snyk', () => {
    const { txt } = getWorkflowText();
    const job = /(^\s*security:\s*\n(?:^\s{2,}.+\n)+?)(?=^\s*\S)/m.exec(txt);
    expect(job).toBeTruthy();
    const block = job[1];
    expect(block).toMatch(/^\s*needs:\s*validate\b/m);
    expect(block).toMatch(/Dependency-Check_Action@main/);
    expect(block).toMatch(/--failOnCVSS 7/);
    expect(block).toMatch(/--enableRetired/);
    expect(block).toMatch(/upload-sarif@v3/);
    expect(block).toMatch(/snyk\/actions\/node@v0\.4\.0/);
    expect(block).toMatch(/--severity-threshold=high/);
  });

  it('defines Project Sync with concurrency control and robust script guards', () => {
    const { txt } = getWorkflowText();
    const job = /(^\s*project-sync:\s*\n(?:^\s{2,}.+\n)+?)(?=^\s*\S)/m.exec(txt);
    expect(job).toBeTruthy();
    const block = job[1];
    expect(block).toMatch(/^\s*concurrency:\s*\n\s*group:\s*project-sync\s*\n\s*cancel-in-progress:\s*true/m);
    expect(block).toMatch(/PROJECTS_V2_OWNER:\s*IgorGanapolsky/);
    expect(block).toMatch(/PROJECTS_V2_NUMBER:\s*1/);
    expect(block).toMatch(/actions\/github-script@v7/);
    // Important guards
    expect(block).toMatch(/actor != 'github-actions\[bot\]'/);
    expect(block).toMatch(/issue\.number != 81/);
    expect(block).toMatch(/const STATUS_ISSUE = 81;/);
    expect(block).toMatch(/📊 SuperPassword Project Status/);
    // Presence of GraphQL query usage
    expect(block).toMatch(/github\.graphql\(`\s*query\(/);
  });

  it('configures Build job to run only on push to main/develop with proper Expo steps', () => {
    const { txt } = getWorkflowText();
    const job = /(^\s*build:\s*\n(?:^\s{2,}.+\n)+?)(?=^\s*\S)/m.exec(txt);
    expect(job).toBeTruthy();
    const block = job[1];
    expect(block).toMatch(/^\s*needs:\s*\[validate,\s*security\]/m);
    expect(block).toMatch(/^\s*if:\s*github\.event_name == 'push' && \(github\.ref == 'refs\/heads\/main' \|\| github\.ref == 'refs\/heads\/develop'\)/m);
    expect(block).toMatch(/expo\/expo-github-action@v8/);
    expect(block).toMatch(/eas build --platform all --profile development --non-interactive/);
    expect(block).toMatch(/eas build --platform all --profile production --non-interactive/);
    expect(block).toMatch(/eas submit --platform all --latest/);
  });

  it('implements Notify job that comments on PRs for both failure and success cases', () => {
    const { txt } = getWorkflowText();
    const job = /(^\s*notify:\s*\n(?:^\s{2,}.+\n)+?)(?=^\s*\S|\Z)/m.exec(txt);
    expect(job).toBeTruthy();
    const block = job[1];
    expect(block).toMatch(/^\s*needs:\s*\[validate,\s*security,\s*build\]/m);
    expect(block).toMatch(/^\s*if:\s*always\(\) && \(github\.event_name == 'push' \|\| github\.event_name == 'pull_request'\)/m);
    // Failure path
    expect(block).toMatch(/Notify on failure/);
    expect(block).toMatch(/if:\s*failure\(\)/);
    expect(block).toMatch(/⚠️ CI Pipeline failed/);
    expect(block).toMatch(/createComment/);
    // Success path
    expect(block).toMatch(/Notify on success/);
    expect(block).toMatch(/if:\s*success\(\)/);
    expect(block).toMatch(/✅ CI Pipeline passed successfully!/);
  });
});