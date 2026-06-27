import { test, expect } from "@playwright/test";

test.describe("FAQ page", () => {
  test("FAQ page loads without crash", async ({ page }) => {
    await page.goto("/faq");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
  });

  test("FAQ page does not show mid-page Etsy disclaimer block", async ({ page }) => {
    await page.goto("/faq");
    await page.waitForLoadState("networkidle");
    // The disclaimer should only appear in the shared footer, not as a standalone indigo block
    const disclaimerBlocks = page.locator(".bg-indigo-50.border-t.border-indigo-100");
    await expect(disclaimerBlocks).toHaveCount(0);
  });
});
