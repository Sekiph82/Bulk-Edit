import { test, expect } from "@playwright/test";

test.describe("Theme system", () => {
  test("page loads and anti-flash script sets data-theme", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("body")).toBeVisible();
    // Anti-flash script sets data-theme before React hydrates
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme")
    );
    expect(["light", "dark"]).toContain(theme);
  });

  test("home page renders h1 in light mode", async ({ page }) => {
    // Set localStorage before navigation using addInitScript
    await page.addInitScript(() => {
      localStorage.setItem("bulk-edit-theme", "light");
    });
    await page.goto("/");
    await expect(page.locator("h1").first()).toBeVisible();
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme")
    );
    expect(theme).toBe("light");
  });

  test("home page renders h1 in dark mode", async ({ page }) => {
    // Set localStorage before navigation using addInitScript
    await page.addInitScript(() => {
      localStorage.setItem("bulk-edit-theme", "dark");
    });
    await page.goto("/");
    await expect(page.locator("h1").first()).toBeVisible();
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme")
    );
    expect(theme).toBe("dark");
  });
});
