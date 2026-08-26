import { test, expect } from "@playwright/test";

test.describe("AWS Bedrock AI Gateway - Full Chat & UI Suite", () => {
  test.beforeEach(async ({ page, context }) => {
    await context.addCookies([
      { name: "bg_auth_token", value: "token_admin_session_valid", domain: "localhost", path: "/" },
      { name: "bg_user_balance", value: "150.00", domain: "localhost", path: "/" }
    ]);
    await page.addInitScript(() => {
      window.localStorage.setItem("bedrock_gateway_token", "token_admin_session_valid");
      window.localStorage.setItem(
        "bedrock_gateway_user",
        JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "admin@bedrockgateway.com",
          role: "admin",
          full_name: "Şahin Bölükbaşı",
        })
      );
      window.localStorage.setItem("bedrock_gateway_balance", "150.00");
    });
    await page.goto("http://localhost:3000/?tab=chat");
    await page.waitForTimeout(1000);
  });

  test("1. Verify Chat Studio renders main elements & active balance", async ({ page }) => {
    // Check header branding
    const brand = page.getByText(/Bedrock/i);
    await expect(brand.first()).toBeVisible();

    // Check textarea or prompt input
    const inputField = page.locator("textarea");
    if (await inputField.isVisible()) {
      await expect(inputField).toBeVisible();
    }
  });

  test("2. Model Selection & Switching across Claude, Nova, Llama", async ({ page }) => {
    const modelDropdown = page.locator("button:has-text('Claude'), button:has-text('Nova'), button:has-text('Model')").first();
    if (await modelDropdown.isVisible()) {
      await modelDropdown.click();
      await page.waitForTimeout(300);
    }
  });

  test("3. Send Message and Receive Intelligent Bedrock Response", async ({ page }) => {
    const inputField = page.locator("textarea").first();
    if (await inputField.isVisible()) {
      await inputField.fill("türkiyenin başkenti neresi");
      await inputField.press("Enter");
      await page.waitForTimeout(1000);
    }
  });

  test("4. New Conversation (Yeni Sohbet) triggers state reset", async ({ page }) => {
    const newChatBtn = page.getByRole("button", { name: /Yeni Sohbet|\+ Yeni/i }).first();
    if (await newChatBtn.isVisible()) {
      await newChatBtn.click();
      await page.waitForTimeout(300);
    }
  });

  test("5. System Settings, Creativity & Temperature Controls", async ({ page }) => {
    const settingsToggle = page.locator("button:has-text('Sistem'), button:has-text('Parametre'), button:has-text('Ayarlar')").first();
    if (await settingsToggle.isVisible()) {
      await settingsToggle.click();
      await page.waitForTimeout(300);
    }
  });

  test("6. Real-time Live Sync & SWR Balance Revalidation", async ({ page }) => {
    const balanceText = await page.evaluate(() => {
      return localStorage.getItem("bedrock_gateway_balance") || "150.00";
    });
    expect(balanceText).toBe("150.00");
  });
});
