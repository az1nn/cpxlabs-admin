import { expect, test } from '@playwright/test'

import { referenceUsers, signIn } from './auth'

test('a revoked session loses protected access on the next authoritative request', async ({ page }) => {
  await signIn(page, referenceUsers.viewer, '/customers')
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()

  const revoke = await page.request.post('/api/auth/sign-out')
  expect(revoke.ok()).toBe(true)

  await page.reload()
  await expect(page).toHaveURL(/\/sign-in\?redirect=/)
})
