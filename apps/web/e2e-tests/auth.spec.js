
const { test, expect } = require('@playwright/test');

test.describe('Authentication', () => {
  test('should allow a user to log in with valid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('should show an error message with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Invalid email or password')).toBeVisible();
  });

  test('should allow a user to log out', async ({ page }) => {
    // First, log in
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    // Now, log out
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL('/login');
  });
});
