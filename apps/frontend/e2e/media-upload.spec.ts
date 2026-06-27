import { test, expect } from "@playwright/test";

test.describe("Media page upload UI", () => {
  test("media page loads without crash", async ({ page }) => {
    await page.goto("/media");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
  });

  test("redirects unauthenticated user to login or stays on media", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/media");
    await page.waitForLoadState("networkidle");
    const url = page.url();
    expect(url).toMatch(/\/(media|login)/);
  });
});
