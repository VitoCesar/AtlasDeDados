const { test, expect } = require("@playwright/test");

test("dashboard mostra carregamento e conclui a renderização", async ({ page }) => {
  await page.goto("/");
  const dashboard = page.locator("#dashboard");
  await expect(dashboard).toHaveAttribute("aria-busy", "false", { timeout: 30000 });
  await expect(page.locator(".metrics")).toBeVisible();
  await expect(page.locator("#load-progress")).toHaveAttribute("aria-valuenow", "100");
});

test("movimento reduzido mantém o dashboard utilizável", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator("#dashboard")).toHaveAttribute("aria-busy", "false", { timeout: 30000 });
  await expect(page.locator("#source")).toBeEnabled();
});
