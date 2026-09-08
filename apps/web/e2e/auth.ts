import { expect, type Page } from '@playwright/test'

export const referenceUsers = {
  admin: 'admin@cpxlabs.local',
  manager: 'manager@cpxlabs.local',
  viewer: 'viewer@cpxlabs.local',
} as const

function referencePassword() {
  const password = process.env.E2E_AUTH_PASSWORD ?? process.env.SEED_AUTH_PASSWORD
  if (!password) {
    throw new Error('E2E_AUTH_PASSWORD or SEED_AUTH_PASSWORD is required for authenticated E2E tests')
  }
  return password
}

export async function signIn(page: Page, email: string, redirect = '/') {
  await page.goto(`/sign-in?redirect=${encodeURIComponent(redirect)}`)
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(referencePassword())
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).not.toHaveURL(/\/sign-in(?:\?|$)/)
}
