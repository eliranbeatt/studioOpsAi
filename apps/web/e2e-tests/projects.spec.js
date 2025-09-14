
const { test, expect } = require('@playwright/test');

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
    await page.goto('/projects');
  });

  test('should display the projects page', async ({ page }) => {
    await expect(page.locator('h1:has-text("Projects")')).toBeVisible();
    await expect(page.locator('button:has-text("New Project")')).toBeVisible();
  });

  test('should allow a user to create a new project', async ({ page }) => {
    await page.click('button:has-text("New Project")');
    await page.waitForSelector('form');
    await page.fill('input[name="name"]', 'My New Project');
    await page.fill('textarea[name="description"]', 'This is a test project.');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=My New Project')).toBeVisible();
  });

  test('should navigate to the project details page', async ({ page }) => {
    // This test assumes a project already exists
    await page.click('text=My New Project');
    await expect(page.locator('h1:has-text("My New Project")')).toBeVisible();
    await expect(page.locator('text=This is a test project.')).toBeVisible();
  });
});
