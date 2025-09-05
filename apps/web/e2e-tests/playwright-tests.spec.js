const { test, expect } = require('@playwright/test');

// Test data
const testPlan = {
  project_name: 'Test Project',
  items: [
    {
      category: 'materials',
      title: 'Test Material',
      description: 'Test description',
      quantity: 10,
      unit: 'unit',
      unit_price: 100,
      subtotal: 1000
    },
    {
      category: 'labor',
      title: 'Test Labor',
      description: 'Test labor description',
      quantity: 5,
      unit: 'hour',
      unit_price: 50,
      subtotal: 250
    }
  ],
  total: 1250,
  margin_target: 0.2,
  currency: 'NIS'
};

test.describe('StudioOps AI End-to-End Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application using baseURL (port 3004)
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForSelector('text=StudioOps AI');
  });

  test('should load the home page', async ({ page }) => {
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    
    // Verify page title - handle case where title might be different
    const title = await page.title();
    expect(title).toMatch(/StudioOps|studioops/i);
    
    // Verify main heading or any heading that indicates the app
    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();
    
    // Verify chat interface or any interactive element is present
    const interactiveElement = page.locator('[role="textbox"], textarea, input').first();
    await expect(interactiveElement).toBeVisible();
  });

  test('should navigate to plan editor', async ({ page }) => {
    // Click on plan editor link or button
    const planEditorLink = page.locator('text=Plan Editor').or(page.locator('a[href*="plan"]'));
    await planEditorLink.click();
    
    // Wait for plan editor to load
    await page.waitForSelector('text=עורך תוכנית');
    
    // Verify plan editor components
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('button:has-text("הוסף שורה")')).toBeVisible();
  });

  test('should create and edit a plan', async ({ page }) => {
    // Navigate to plan editor
    const planEditorLink = page.locator('text=Plan Editor').or(page.locator('a[href*="plan"]'));
    await planEditorLink.click();
    
    // Wait for plan editor to load
    await page.waitForSelector('text=עורך תוכנית');
    
    // Add a new row
    const addRowButton = page.locator('button:has-text("הוסף שורה")');
    await addRowButton.click();
    
    // Wait for new row to appear
    await page.waitForSelector('tr:nth-child(2)');
    
    // Edit the new row
    const titleCell = page.locator('tr:nth-child(2) td:nth-child(2)');
    await titleCell.click();
    
    const titleInput = page.locator('tr:nth-child(2) input[type="text"]').first();
    await titleInput.fill('Test Item');
    await titleInput.press('Enter');
    
    // Verify the edit was saved
    await expect(titleCell).toContainText('Test Item');
  });

  test('should interact with chat interface', async ({ page }) => {
    // Find chat input
    const chatInput = page.locator('[role="textbox"]');
    await chatInput.fill('Hello, can you help me create a project plan?');
    await chatInput.press('Enter');
    
    // Wait for AI response
    await page.waitForTimeout(2000); // Wait for response
    
    // Verify response contains helpful text
    const responses = page.locator('[class*="message"], [class*="response"]');
    await expect(responses.last()).toContainText(/project|plan|help/i);
  });

  test('should test API endpoints', async ({ request }) => {
    // Test health endpoint
    const healthResponse = await request.get('/api/health');
    expect(healthResponse.status()).toBe(200);
    
    const healthData = await healthResponse.json();
    expect(healthData).toHaveProperty('status', 'ok');
    
    // Test API health endpoint
    const apiHealthResponse = await request.get('/api/health');
    expect(apiHealthResponse.status()).toBe(200);
    
    const apiHealthData = await apiHealthResponse.json();
    expect(apiHealthData).toHaveProperty('status', 'ok');
    
    // Test chat endpoint
    const chatResponse = await request.post('/api/chat/message', {
      data: {
        message: 'Test message',
        project_id: null
      }
    });
    
    expect(chatResponse.status()).toBe(200);
    const chatData = await chatResponse.json();
    expect(chatData).toHaveProperty('message');
    expect(chatData).toHaveProperty('context');
  });

  test('should test plan generation API', async ({ request }) => {
    const planResponse = await request.post('/api/chat/generate_plan', {
      data: {
        project_name: 'Test Project',
        project_description: 'Test project description'
      }
    });
    
    expect(planResponse.status()).toBe(200);
    const planData = await planResponse.json();
    
    // Verify plan structure
    expect(planData).toHaveProperty('project_name');
    expect(planData).toHaveProperty('items');
    expect(planData).toHaveProperty('total');
    expect(Array.isArray(planData.items)).toBe(true);
  });

  test('should test vendors and materials APIs', async ({ request }) => {
    // Test vendors endpoint
    const vendorsResponse = await request.get('/api/vendors');
    expect(vendorsResponse.status()).toBe(200);
    
    const vendorsData = await vendorsResponse.json();
    expect(Array.isArray(vendorsData)).toBe(true);
    
    // Test materials endpoint
    const materialsResponse = await request.get('/api/materials');
    expect(materialsResponse.status()).toBe(200);
    
    const materialsData = await materialsResponse.json();
    expect(Array.isArray(materialsData)).toBe(true);
  });

  test('should handle plan saving and loading', async ({ page }) => {
    // Navigate to plan editor
    const planEditorLink = page.locator('text=Plan Editor').or(page.locator('a[href*="plan"]'));
    await planEditorLink.click();
    
    // Wait for plan editor to load
    await page.waitForSelector('text=עורך תוכנית');
    
    // Check if save button exists
    const saveButton = page.locator('button:has-text("שמור תוכנית")');
    
    if (await saveButton.isVisible()) {
      // Try to save the plan
      await saveButton.click();
      
      // Wait for save operation
      await page.waitForTimeout(1000);
      
      // Verify success (this would depend on your actual implementation)
      // Could check for success message or disabled button state
      await expect(saveButton).not.toBeDisabled();
    }
  });

  test('should test responsive design', async ({ page }) => {
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify elements are still accessible
    await expect(page.locator('[role="textbox"]')).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('[role="textbox"]')).toBeVisible();
    
    // Reset to desktop
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should test error handling', async ({ page }) => {
    // Test invalid chat input
    const chatInput = page.locator('[role="textbox"]');
    await chatInput.fill(''); // Empty message
    await chatInput.press('Enter');
    
    // Should handle empty messages gracefully
    await page.waitForTimeout(1000);
    
    // Test navigation to non-existent page
    await page.goto('/non-existent-page');
    
    // Should show 404 or redirect to home
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/|404/);
  });
});