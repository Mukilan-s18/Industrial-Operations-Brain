import { test, expect } from '@playwright/test';

test('E2E RCA Flow creates a work order', async ({ page }) => {
  // Mock the /api/stream endpoint to return a simulated SSE response
  // We do this to decouple frontend E2E from the actual backend LLM which can be slow and flaky
  await page.route('**/api/stream', async route => {
    const response = `data: {"answer": "The vibration is caused by bearing wear."}\n\ndata: {"action_taken": "CREATE_SAP_WO", "action_result": "Created Work Order 9999"}\n\n`;
    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      body: response,
    });
  });

  // Mock /api/nodes and /api/edges so the graph doesn't crash
  await page.route('**/api/nodes', async route => route.fulfill({ json: [] }));
  await page.route('**/api/edges', async route => route.fulfill({ json: [] }));

  await page.goto('/');

  // Type the RCA query
  const input = page.getByPlaceholder('Ask as Ravi (Operator)...');
  await input.fill('Why is P-101 vibrating?');

  // Submit
  await page.locator('button[type="submit"]').click();

  // Wait for the simulated SSE response to render in the DOM
  await expect(page.getByText('The vibration is caused by bearing wear.')).toBeVisible();
  
  // Wait for the action block
  await expect(page.getByText('CREATE_SAP_WO')).toBeVisible();
  await expect(page.getByText('Created Work Order 9999')).toBeVisible();
});
