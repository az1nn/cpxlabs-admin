import { expect, test } from '@playwright/test'

import { referenceUsers } from './auth'

function referencePassword() {
  const password = process.env.E2E_AUTH_PASSWORD ?? process.env.SEED_AUTH_PASSWORD
  if (!password) {
    throw new Error('E2E_AUTH_PASSWORD or SEED_AUTH_PASSWORD is required')
  }
  return password
}

test('protected navigation redirects to sign-in, restores the session, and clears authority on logout', async ({ page }) => {
  await page.goto('/customers')
  await expect(page).toHaveURL(/\/sign-in\?redirect=/)

  await page.getByLabel('Email').fill(referenceUsers.admin)
  await page.getByLabel('Password').fill(referencePassword())
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page).toHaveURL(/\/customers(?:\?|$)/)
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()

  await page.reload()
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()

  const browserStorage = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
  }))
  expect(browserStorage).toEqual({ local: [], session: [] })

  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page).toHaveURL(/\/sign-in(?:\?|$)/)

  await page.goto('/customers')
  await expect(page).toHaveURL(/\/sign-in\?redirect=/)
})
