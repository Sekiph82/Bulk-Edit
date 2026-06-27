import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3100";
const SEEDED = process.env.PLAYWRIGHT_RUN_SEEDED_TESTS === "1";

test("profit page redirects unauthenticated users to login", async ({ page }) => {
  await page.goto(`${BASE}/profit`);
  await expect(page).toHaveURL(/\/login/);
});

test.describe("profit calculator (seeded)", () => {
  test.skip(!SEEDED, "requires PLAYWRIGHT_RUN_SEEDED_TESTS=1");

  test("profit page loads summary cards and warning banner for authenticated user", async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.fill('input[type="email"]', "test@example.com");
    await page.fill('input[type="password"]', "Test1234!");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);

    await page.goto(`${BASE}/profit`);
    await expect(page.getByRole("heading", { name: /profit/i })).toBeVisible();
    // Warning banner
    await expect(page.getByText(/fee rates are configurable/i)).toBeVisible();
    // Summary cards
    await expect(page.getByText(/avg margin/i)).toBeVisible();
  });
});
