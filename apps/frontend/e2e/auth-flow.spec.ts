import { test, expect } from "@playwright/test";

test.describe("Auth flow", () => {
  test("unauthenticated /dashboard redirects to /login", async ({ page }) => {
    // Clear any stored tokens before navigation
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/dashboard");
    await page.waitForURL("**/login**", { timeout: 10000 });
    expect(page.url()).toContain("/login");
  });

  test("unauthenticated /shops?connected=true preserves destination through login", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/shops?connected=true");
    await page.waitForURL("**/login**", { timeout: 10000 });
    expect(decodeURIComponent(page.url())).toContain("next=/shops?connected=true");
  });

  test("/login is directly accessible and renders the sign-in form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
  });
});

// Private Beta route-policy tests: these require the server under test to be
// built/started with NEXT_PUBLIC_PRIVATE_BETA_MODE=true (the middleware
// inlines this at build time, so a plain dev server with the flag unset —
// the default locally — cannot exercise this gate). Mirrors the
// PLAYWRIGHT_RUN_SEEDED_TESTS convention below.
//
// Usage:
//   NEXT_PUBLIC_PRIVATE_BETA_MODE=true npm run build && npm start &
//   PLAYWRIGHT_RUN_PRIVATE_BETA_TESTS=1 PLAYWRIGHT_BASE_URL=http://localhost:3100 npm run e2e
const runPrivateBetaTests = !!process.env.PLAYWRIGHT_RUN_PRIVATE_BETA_TESTS;
const privateBetaTest = runPrivateBetaTests ? test : test.skip;

test.describe("Private Beta route policy (requires NEXT_PUBLIC_PRIVATE_BETA_MODE=true build)", () => {
  privateBetaTest("/private-beta is public", async ({ page }) => {
    const response = await page.goto("/private-beta");
    expect(response?.status()).toBeLessThan(400);
  });

  privateBetaTest("/login is not redirected to /private-beta", async ({ page }) => {
    await page.goto("/login");
    expect(page.url()).toContain("/login");
    await expect(page.locator("input[type='email']")).toBeVisible();
  });

  privateBetaTest("/register is redirected to /private-beta", async ({ page }) => {
    await page.goto("/register");
    await page.waitForURL("**/private-beta**", { timeout: 10000 });
  });

  privateBetaTest("/get-started is redirected to /private-beta", async ({ page }) => {
    await page.goto("/get-started");
    await page.waitForURL("**/private-beta**", { timeout: 10000 });
  });

  privateBetaTest("unauthenticated /dashboard still reaches /login, not /private-beta", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/dashboard");
    await page.waitForURL("**/login**", { timeout: 10000 });
  });

  privateBetaTest("public marketing route / stays public", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBeLessThan(400);
    expect(page.url()).not.toContain("/private-beta");
  });
});

// Seeded-user tests require:
//   1. Docker stack running: docker compose -p bulk-edit up -d
//   2. Seeded users available: test@example.com / Test1234! and test-su@example.com / Test1234!
//   3. Set PLAYWRIGHT_RUN_SEEDED_TESTS=1 env var to enable
//
// Usage: PLAYWRIGHT_RUN_SEEDED_TESTS=1 npm run e2e
const runSeededTests = !!process.env.PLAYWRIGHT_RUN_SEEDED_TESTS;
const seededTest = runSeededTests ? test : test.skip;

test.describe("Seeded user flows (requires PLAYWRIGHT_RUN_SEEDED_TESTS=1)", () => {
  seededTest(
    "normal user: admin nav hidden, /admin is a 404",
    async ({ page }) => {
      await page.goto("/login");
      await page.fill(
        "input[name='email'], input[type='email']",
        "test@example.com"
      );
      await page.fill(
        "input[name='password'], input[type='password']",
        "Test1234!"
      );
      await page.click("button[type='submit']");
      await page.waitForURL("**/dashboard", { timeout: 10000 });

      // Admin nav must NOT be visible for normal user
      const adminLink = page.locator("[data-testid='admin-nav-link']");
      await expect(adminLink).not.toBeVisible();

      // /admin is no longer the owner entrypoint — must 404 for non-superusers
      const response = await page.goto("/admin");
      expect(response?.status()).toBe(404);
    }
  );

  seededTest(
    "superuser: admin nav visible, /admin redirects to the owner console",
    async ({ page }) => {
      await page.goto("/login");
      await page.fill(
        "input[name='email'], input[type='email']",
        "test-su@example.com"
      );
      await page.fill(
        "input[name='password'], input[type='password']",
        "Test1234!"
      );
      await page.click("button[type='submit']");
      await page.waitForURL("**/dashboard", { timeout: 10000 });

      // Admin nav must be visible for superuser
      const adminLink = page.locator("[data-testid='admin-nav-link']");
      await expect(adminLink).toBeVisible({ timeout: 8000 });

      // /admin must redirect a confirmed superuser to the owner console
      await page.goto("/admin");
      await page.waitForURL("**/owner", { timeout: 8000 });
      await expect(
        page.locator("text=Owner Dashboard").first()
      ).toBeVisible({ timeout: 8000 });
    }
  );
});
