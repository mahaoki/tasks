import { test, expect } from '@playwright/test';

test('user can login and be redirected to dashboard', async ({ page }) => {
  await page.route('**/auth/login', async (route) => {
    await route.fulfill({
      json: { accessToken: 'a', refreshToken: 'b' },
    });
  });

  await page.goto('/login');
  await page.fill('input[placeholder="Email"]', 'user@example.com');
  await page.fill('input[placeholder="Password"]', 'pass');
  await page.click('text=Login');
  await expect(page).toHaveURL(/dashboard/);
});
