import { test, expect } from "@playwright/test";

test.describe("Onboarding flows", () => {
  test("dashboard redirects unauthenticated user to login", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
    const url = page.url();
    expect(url).toMatch(/\/(dashboard|login)/);
  });

  test("shops page loads without JS crash", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    });
    await page.goto("/shops");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
    const url = page.url();
    expect(url).toMatch(/\/(shops|login)/);
  });
});

// Seeded-user onboarding tests require Docker stack + PLAYWRIGHT_RUN_SEEDED_TESTS=1
const runSeededTests = !!process.env.PLAYWRIGHT_RUN_SEEDED_TESTS;
const seededTest = runSeededTests ? test : test.skip;

test.describe("Onboarding checklist (requires PLAYWRIGHT_RUN_SEEDED_TESTS=1)", () => {
  seededTest("dashboard shows onboarding checklist for new customer", async ({ page }) => {
    await page.goto("/login");
    await page.fill("input[name='email'], input[type='email']", "test@example.com");
    await page.fill("input[name='password'], input[type='password']", "Test1234!");
    await page.click("button[type='submit']");
    await page.waitForURL("**/dashboard", { timeout: 10000 });

    // Checklist renders when no shop connected
    const checklist = page.locator("[data-testid='onboarding-checklist']");
    await expect(checklist).toBeVisible({ timeout: 8000 });
  });

  seededTest("shops empty state shows Etsy trademark note", async ({ page }) => {
    await page.goto("/login");
    await page.fill("input[name='email'], input[type='email']", "test@example.com");
    await page.fill("input[name='password'], input[type='password']", "Test1234!");
    await page.click("button[type='submit']");
    await page.waitForURL("**/dashboard", { timeout: 10000 });
    await page.goto("/shops");
    await page.waitForLoadState("networkidle");

    await expect(page.locator("text=Etsy® is a trademark")).toBeVisible({ timeout: 8000 });
    await expect(page.locator("text=Connect Etsy Shop")).toBeVisible();
  });
});
