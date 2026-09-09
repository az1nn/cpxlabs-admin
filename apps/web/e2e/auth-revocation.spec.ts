import { expect, test } from '@playwright/test'

import { referenceUsers, signIn } from './auth'

test('a revoked session loses protected access on the next authoritative request', async ({ page }) => {
  await signIn(page, referenceUsers.viewer, '/customers')
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()

  const revokeStatus = await page.evaluate(async () => {
    const response = await fetch('/api/auth/sign-out', {
      method: 'POST',
      credentials: 'include',
      headers: { 'content-type': 'application/json' },
      body: '{}',
    })
    return response.status
  })
  expect(revokeStatus).toBe(200)

  await page.reload()
  await expect(page).toHaveURL(/\/sign-in\?redirect=/)
})
