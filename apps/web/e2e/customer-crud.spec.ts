import { expect, test } from '@playwright/test'

test('customer CRUD journey remains functional and addressable', async ({ page }) => {
  await page.goto('/customers')

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
  await page.getByRole('button', { name: 'Create customer' }).click()

  await expect(page.getByRole('heading', { name: 'E2E Customer' })).toBeVisible()
  await expect(page.getByText('e2e.customer@example.com')).toBeVisible()

  await page.getByRole('button', { name: 'Edit' }).click()
  await expect(page.getByRole('heading', { name: 'Edit E2E Customer' })).toBeVisible()

  await page.getByLabel('Name').fill('E2E Customer Updated')
  await page.getByRole('button', { name: 'Save changes' }).click()

  await expect(page.getByRole('heading', { name: 'E2E Customer Updated' })).toBeVisible()

  await page.getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByText('Delete customer?')).toBeVisible()
  await page.getByRole('button', { name: 'Delete customer' }).click()

  await expect(page.getByRole('heading', { name: 'Customers' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'E2E Customer Updated' })).toHaveCount(0)
})
