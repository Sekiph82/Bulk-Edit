import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3100";
const SEEDED = process.env.PLAYWRIGHT_RUN_SEEDED_TESTS === "1";

test("listing health page redirects unauthenticated users to login", async ({ page }) => {
  await page.goto(`${BASE}/listing-health`);
  await expect(page).toHaveURL(/\/login/);
});

test.describe("listing health (seeded)", () => {
  test.skip(!SEEDED, "requires PLAYWRIGHT_RUN_SEEDED_TESTS=1");

  test("listing health page loads summary cards for authenticated user", async ({ page }) => {
    // Login with seeded test user
    await page.goto(`${BASE}/login`);
    await page.fill('input[type="email"]', "test@example.com");
    await page.fill('input[type="password"]', "Test1234!");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);

    await page.goto(`${BASE}/listing-health`);
    await expect(page.getByRole("heading", { name: /listing health/i })).toBeVisible();
    // Summary cards
    await expect(page.getByText(/avg score/i)).toBeVisible();
    await expect(page.getByText(/total/i)).toBeVisible();
  });
});
