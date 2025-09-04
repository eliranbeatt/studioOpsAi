const { test, expect } = require('@playwright/test');

test.describe('StudioOps AI UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3004');
  });

  test('Home page loads correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/StudioOps AI/);
    await expect(page.locator('text=ניהול פרויקטים')).toBeVisible();
  });

  test('Projects page navigation works', async ({ page }) => {
    await page.click('text=פרויקטים');
    await expect(page.locator('text=ניהול פרויקטים')).toBeVisible();
  });

  test('Vendors page navigation works', async ({ page }) => {
    await page.click('text=ספקים');
    await expect(page.locator('text=ניהול ספקים')).toBeVisible();
  });

  test('Materials page navigation works', async ({ page }) => {
    await page.click('text=חומרים');
    await expect(page.locator('text=ניהול חומרים')).toBeVisible();
  });

  test('Add Project button opens modal', async ({ page }) => {
    await page.click('text=פרויקטים');
    await page.click('text=➕ פרויקט חדש');
    await expect(page.locator('text=צור פרויקט חדש')).toBeVisible();
  });

  test('Add Vendor button opens modal', async ({ page }) => {
    await page.click('text=ספקים');
    await page.click('text=➕ ספק חדש');
    await expect(page.locator('text=צור ספק חדש')).toBeVisible();
  });

  test('API health check', async ({ request }) => {
    const response = await request.get('http://localhost:8002/health');
    expect(response.status()).toBe(200);
  });

  test('Projects API endpoint works', async ({ request }) => {
    const response = await request.get('http://localhost:8002/projects');
    expect(response.status()).toBe(200);
  });

  test('Vendors API endpoint works', async ({ request }) => {
    const response = await request.get('http://localhost:8002/vendors');
    expect(response.status()).toBe(200);
  });

  test('Materials API endpoint works', async ({ request }) => {
    const response = await request.get('http://localhost:8002/materials');
    expect(response.status()).toBe(200);
  });
});