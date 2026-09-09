import fs from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";

const defaultPublishingUrl =
  "https://play.google.com/console/u/1/developers/8239620436488925047/app/4976249162120849673/publishing";

function fail(message) {
  throw new Error(message);
}

function tryParseUrl(rawUrl) {
  try {
    return new URL(rawUrl);
  } catch {
    return null;
  }
}

function isPlayLoginUrl(rawUrl) {
  const parsed = tryParseUrl(rawUrl);
  if (!parsed) {
    return false;
  }
  return parsed.hostname.toLowerCase() === "accounts.google.com";
}

async function expectAuthenticated(page) {
  const currentUrl = page.url();
  const isLogin = isPlayLoginUrl(currentUrl);
  const hasLoginField = await page
    .locator('input[type="email"]')
    .first()
    .isVisible()
    .catch(() => false);

  if (isLogin || hasLoginField) {
    fail(
      "Play auth state is not authenticated. Refresh PLAY_STORAGE_STATE_JSON and rerun.",
    );
  }
}

async function saveArtifacts(page, dir, name) {
  const screenshotPath = path.join(dir, `${name}.png`);
  const textPath = path.join(dir, `${name}.txt`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const bodyText = await page.locator("body").innerText().catch(() => "");
  fs.writeFileSync(textPath, bodyText, "utf8");
}

async function clickFirst(page, labels) {
  for (const label of labels) {
    if (label instanceof RegExp) {
      const roleButton = page.getByRole("button", { name: label }).first();
      if (await roleButton.isVisible().catch(() => false)) {
        await roleButton.click();
        return label.toString();
      }
      const textNode = page.getByText(label).first();
      if (await textNode.isVisible().catch(() => false)) {
        await textNode.click();
        return label.toString();
      }
      continue;
    }

    const roleButton = page.getByRole("button", { name: label }).first();
    if (await roleButton.isVisible().catch(() => false)) {
      await roleButton.click();
      return label;
    }

    const textNode = page.getByText(label, { exact: false }).first();
    if (await textNode.isVisible().catch(() => false)) {
      await textNode.click();
      return label;
    }
  }

  return null;
}

async function main() {
  const storageStatePath = process.env.PLAY_STORAGE_STATE_PATH;
  if (!storageStatePath || !fs.existsSync(storageStatePath)) {
    fail("PLAY_STORAGE_STATE_PATH must point to an existing Play auth state file.");
  }

  const publishingUrl = process.env.PLAY_PUBLISHING_URL ?? defaultPublishingUrl;
  const artifactDir =
    process.env.PLAY_PUBLISH_ARTIFACT_DIR ??
    path.resolve(process.cwd(), "test-results/play-publish-changes");
  fs.mkdirSync(artifactDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: storageStatePath,
    viewport: { width: 1600, height: 1200 },
  });
  const page = await context.newPage();

  let published = false;
  let publishLabel = null;
  let bodyBefore = "";
  let bodyAfter = "";

  try {
    await page.goto(publishingUrl, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(5000);
    await expectAuthenticated(page);
    bodyBefore = await page.locator("body").innerText().catch(() => "");
    await saveArtifacts(page, artifactDir, "01-publishing-overview");

    publishLabel = await clickFirst(page, [
      /publish \d+ changes?/i,
      /send for review/i,
      /submit for review/i,
      /publish changes/i,
      /^publish$/i,
    ]);

    if (publishLabel) {
      await page.waitForTimeout(3000);
      await saveArtifacts(page, artifactDir, "02-after-primary-click");

      await clickFirst(page, [
        /send for review/i,
        /submit for review/i,
        /publish/i,
        /confirm/i,
        /yes/i,
        /roll out/i,
      ]);

      await page.waitForTimeout(5000);
      published = true;
    }

    bodyAfter = await page.locator("body").innerText().catch(() => "");
    await saveArtifacts(page, artifactDir, "03-final");

    const updateStatus =
      bodyAfter.match(/\b(Ready to publish|In review|Published|Pending publication)\b/i)?.[0] ??
      "unknown";

    const resultPath = path.join(artifactDir, "result.json");
    fs.writeFileSync(
      resultPath,
      JSON.stringify(
        {
          published,
          publishLabel,
          updateStatus,
          hadPendingBefore: /ready to publish|changes? not sent|pending/i.test(bodyBefore),
          finalUrl: page.url(),
        },
        null,
        2,
      ),
      "utf8",
    );

    if (!published) {
      fail(
        "No Publish/Send-for-review control found on Play publishing overview. " +
          "Managed publishing may require manual Console action or refreshed PLAY_STORAGE_STATE_JSON.",
      );
    }

    console.log(`Play publish action clicked: ${publishLabel}; observed status: ${updateStatus}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

await main();
