import { test, expect } from "@playwright/test";

test.describe("Public marketing pages", () => {
  test("home page loads", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Bulk-Edit|Bulk Edit/i);
    await expect(page.locator("h1").first()).toBeVisible();
  });

  test("features page loads", async ({ page }) => {
    await page.goto("/features");
    await expect(page.locator("h1").first()).toBeVisible();
  });

  test("pricing page loads", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page.locator("h1").first()).toBeVisible();
  });

  test("faq page loads", async ({ page }) => {
    await page.goto("/faq");
    await expect(page.locator("h1").first()).toBeVisible();
  });

  test("contact page loads", async ({ page }) => {
    await page.goto("/contact-us");
    await expect(page.locator("h1").first()).toBeVisible();
  });
});

test.describe("Auth pages", () => {
  test("login page loads", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.locator("input[type='email'], input[name='email']").first()
    ).toBeVisible();
    await expect(
      page.locator("input[type='password'], input[name='password']").first()
    ).toBeVisible();
  });

  test("register page loads", async ({ page }) => {
    await page.goto("/register");
    await expect(
      page.locator("input[type='email'], input[name='email']").first()
    ).toBeVisible();
  });
});
