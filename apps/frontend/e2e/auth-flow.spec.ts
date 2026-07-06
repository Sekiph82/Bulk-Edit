import { test, expect } from "@playwright/test";

test.describe("Auth flow", () => {
  test("unauthenticated /dashboard page loads (client-side app shell)", async ({ page }) => {
    // Clear any stored tokens before navigation
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    // App shell renders — API calls will return 401 without token.
    // The page either redirects to /login or shows an empty/loading state.
    // Key: page must load without JavaScript crash.
    await expect(page.locator("body")).toBeVisible();
    // URL should be /dashboard or /login (if redirect implemented)
    const url = page.url();
    expect(url).toMatch(/\/(dashboard|login)/);
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
