import { expect, test } from '@playwright/test'

import { referenceUsers, signIn } from './auth'

test('unauthenticated users are redirected to sign-in and return to the protected destination', async ({ page }) => {
  await page.goto('/customers?search=Acme')
  await expect(page).toHaveURL(/\/sign-in\?redirect=/)

  await page.getByLabel('Email').fill(referenceUsers.admin)
  await page.getByLabel('Password').fill(process.env.E2E_AUTH_PASSWORD ?? process.env.SEED_AUTH_PASSWORD ?? '')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page).toHaveURL(/\/customers\?search=Acme/)
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()
})

test('viewer can read customers but cannot mutate them in UI or direct API', async ({ page }) => {
  await signIn(page, referenceUsers.viewer, '/customers')
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'New customer' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Acme Brasil' }).click()
  await expect(page.getByRole('button', { name: 'Edit' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Delete' })).toHaveCount(0)

  const forbidden = await page.request.post('/api/customers', {
    data: {
      name: 'Viewer Forbidden',
      email: `viewer.forbidden.${Date.now()}@example.com`,
      company: 'CPXLabs',
      status: 'lead',
    },
  })
  expect(forbidden.status()).toBe(403)
  await expect(forbidden.json()).resolves.toMatchObject({ error: { code: 'FORBIDDEN' } })
})

test('manager can create and update customers but cannot delete them', async ({ page }) => {
  await signIn(page, referenceUsers.manager, '/customers')
  await expect(page.getByRole('button', { name: 'New customer' })).toBeVisible()

  await page.getByRole('button', { name: 'Acme Brasil' }).click()
  await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Delete' })).toHaveCount(0)

  const customer = await page.request.post('/api/customers', {
    data: {
      name: 'Manager E2E',
      email: `manager.e2e.${Date.now()}@example.com`,
      company: 'CPXLabs',
      status: 'lead',
    },
  })
  expect(customer.status()).toBe(201)
  const created = await customer.json() as { id: string }

  const forbiddenDelete = await page.request.delete(`/api/customers/${created.id}`)
  expect(forbiddenDelete.status()).toBe(403)
})
