import { expect, test } from '@playwright/test'

import { referenceUsers, signIn } from './auth'

function isCustomerApiResponse(response: import('@playwright/test').Response, method: string) {
  const url = new URL(response.url())
  return url.pathname.startsWith('/api/customers') && response.request().method() === method
}

test('admin customer CRUD journey traverses the authenticated real HTTP API', async ({ page }) => {
  await signIn(page, referenceUsers.admin, '/customers')

  const initialListResponse = page.waitForResponse((response) => isCustomerApiResponse(response, 'GET'))
  await page.goto('/customers')

  await expect((await initialListResponse).ok()).toBe(true)
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()

  await page.reload()
  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()

  await page.getByLabel('Search').fill('Acme')
  await expect(page).toHaveURL(/search=Acme/)
  await expect(page.getByRole('button', { name: 'Acme Brasil' })).toBeVisible()

  await page.getByLabel('Search').fill('')
  await page.getByRole('button', { name: 'New customer' }).click()

  await expect(page.getByRole('heading', { name: 'New customer' })).toBeVisible()
  await page.getByLabel('Name').fill('E2E Customer')
  await page.getByLabel('Company').fill('CPXLabs QA')
  await page.getByLabel('Email').fill('e2e.customer@example.com')
  await page.getByLabel('Status').selectOption('active')

  const createResponse = page.waitForResponse((response) => isCustomerApiResponse(response, 'POST'))
  await page.getByRole('button', { name: 'Create customer' }).click()
  await expect((await createResponse).ok()).toBe(true)

  await expect(page.getByRole('heading', { name: 'E2E Customer' })).toBeVisible()
  await expect(page.getByText('e2e.customer@example.com')).toBeVisible()

  await page.getByRole('button', { name: 'Edit' }).click()
  await expect(page.getByRole('heading', { name: 'Edit E2E Customer' })).toBeVisible()

  await page.getByLabel('Name').fill('E2E Customer Updated')
  const updateResponse = page.waitForResponse((response) => isCustomerApiResponse(response, 'PATCH'))
  await page.getByRole('button', { name: 'Save changes' }).click()
  await expect((await updateResponse).ok()).toBe(true)

  await expect(page.getByRole('heading', { name: 'E2E Customer Updated' })).toBeVisible()

  await page.getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByText('Delete customer?')).toBeVisible()

  const deleteResponse = page.waitForResponse((response) => isCustomerApiResponse(response, 'DELETE'))
  await page.getByRole('button', { name: 'Delete customer' }).click()
  await expect((await deleteResponse).ok()).toBe(true)

  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'E2E Customer Updated' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page).toHaveURL(/\/sign-in/)
  await page.goto('/customers')
  await expect(page).toHaveURL(/\/sign-in\?redirect=/)
})
