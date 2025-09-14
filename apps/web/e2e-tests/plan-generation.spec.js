
const { test, expect } = require('@playwright/test');

test.describe('AI Plan Generation and Editing', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should generate a plan from AI chat and edit it', async ({ page }) => {
    // 1. Start a chat and ask for a plan
    await page.goto('/chat');
    await page.fill('[role="textbox"]', 'Create a plan for a small house');
    await page.press('[role="textbox"]', 'Enter');

    // 2. Wait for the AI to suggest a plan
    await page.waitForSelector('text=The AI has suggested a plan');

    // 3. Click the button to accept the plan
    await page.click('button:has-text("Create Plan")');

    // 4. Verify the Plan Editor opens
    await page.waitForSelector('text=Plan Editor');
    await expect(page.locator('h2:has-text("Plan Editor")')).toBeVisible();

    // 5. Edit an item
    const firstRow = page.locator('table tr').nth(1);
    await firstRow.locator('td').nth(3).click(); // Click quantity cell
    await firstRow.locator('input[type="number"]').fill('5');
    await page.keyboard.press('Enter');

    await firstRow.locator('td').nth(5).click(); // Click unit price cell
    await firstRow.locator('input[type="number"]').fill('150');
    await page.keyboard.press('Enter');

    // 6. Verify the subtotal is updated
    const subtotalCell = firstRow.locator('td').nth(6);
    await expect(subtotalCell).toHaveText('750');

    // 7. Verify the total is updated (this requires knowing the initial total)
    // This is a simplified example. A real test would need to calculate the expected total.
    const totalElement = page.locator('text=Total:');
    await expect(totalElement).toBeVisible();

    // 8. Delete an item
    const deleteButton = firstRow.locator('button:has-text("Delete")');
    await deleteButton.click();

    // 9. Verify the row is removed
    await expect(firstRow).not.toBeVisible();
  });
});
