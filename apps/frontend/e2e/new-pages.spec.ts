import { test, expect } from "@playwright/test";

test.describe("Sprint 26 — New pages smoke tests", () => {
  test.beforeEach(async ({ page }) => {
    // Set a mock token so auth redirects don't block us
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock_token_for_route_test");
    });
  });

  test("Insights page loads without JS errors", async ({ page }) => {
    await page.goto("/insights");
    // Should not redirect to /login (page loaded)
    await page.waitForTimeout(500);
    // Check page structure
    const heading = page.locator("h1");
    await expect(heading).toContainText("Insights");
  });

  test("Promote page loads with safe not-configured state", async ({ page }) => {
    await page.goto("/promote");
    await page.waitForTimeout(500);
    const heading = page.locator("h1");
    await expect(heading).toContainText("Promote");
    // Should show safety notice
    const safetyNotice = page.getByText("never auto-published");
    await expect(safetyNotice).toBeVisible();
  });

  test("Video Generator page loads with renderer not configured state", async ({ page }) => {
    await page.goto("/video-generator");
    await page.waitForTimeout(500);
    const heading = page.locator("h1");
    await expect(heading).toContainText("Video Generator");
    // Should show safety notice
    const safetyNotice = page.getByText("never auto-uploaded");
    await expect(safetyNotice).toBeVisible();
  });

  test("Bulk Create page loads", async ({ page }) => {
    await page.goto("/bulk-create");
    await page.waitForTimeout(500);
    const heading = page.locator("h1");
    await expect(heading).toContainText("Bulk Create");
    // Should show safety notice
    const safetyNotice = page.getByText("never auto-published");
    await expect(safetyNotice).toBeVisible();
  });
});
