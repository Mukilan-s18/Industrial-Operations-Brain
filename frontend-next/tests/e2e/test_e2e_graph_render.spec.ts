import { test, expect } from '@playwright/test';

test('E2E Knowledge Graph renders without crashing', async ({ page }) => {
  // Mock /api/nodes and /api/edges
  await page.route('**/api/nodes', async route => route.fulfill({
    json: [{ id: "P-101", label: "EQUIPMENT" }]
  }));
  await page.route('**/api/edges', async route => route.fulfill({
    json: []
  }));

  await page.goto('/');

  // Navigate to Knowledge Graph tab
  await page.getByText('Knowledge Graph', { exact: true }).click();

  // Check if the canvas element mounts. The force graph library injects a canvas into its container.
  // We'll wait for the "Loading graph topology..." to disappear
  await expect(page.getByText('Loading graph topology...')).toBeHidden({ timeout: 10000 });

  // Then check that a canvas element is rendered in the right panel
  const canvas = page.locator('canvas');
  await expect(canvas).toBeAttached();
});
