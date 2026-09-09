import { expect, test, type Page } from '@playwright/test'

import { referenceUsers, signIn } from './auth'

type CreatedOpportunity = {
  id: string
  name: string
  version: number
}

async function createOpportunityViaApi(page: Page, name: string): Promise<CreatedOpportunity> {
  const response = await page.request.post('/api/opportunities', {
    data: {
      name,
      accountName: 'CPXLabs E2E',
      amountMinor: 1250000,
      currency: 'BRL',
      expectedCloseDate: '2026-12-20',
    },
  })
  expect(response.status()).toBe(201)
  return response.json() as Promise<CreatedOpportunity>
}

test('viewer can read an opportunity but receives no workflow mutation controls', async ({ page }) => {
  await signIn(page, referenceUsers.manager, '/opportunities')
  const opportunity = await createOpportunityViaApi(page, `Viewer Read ${Date.now()}`)

  await page.context().clearCookies()
  await signIn(page, referenceUsers.viewer, `/opportunities/${opportunity.id}`)

  await expect(page.getByRole('heading', { name: opportunity.name })).toBeVisible()
  await expect(page.getByRole('button', { name: /Move to/ })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Mark lost' })).toHaveCount(0)

  const forbidden = await page.request.post(`/api/opportunities/${opportunity.id}/commands/transition`, {
    data: { targetStage: 'discovery', expectedVersion: 1 },
  })
  expect(forbidden.status()).toBe(403)
  await expect(forbidden.json()).resolves.toMatchObject({ error: { code: 'FORBIDDEN' } })
})

test('manager creates opportunities and completes won and lost terminal journeys', async ({ page }) => {
  await signIn(page, referenceUsers.manager, '/opportunities')
  await page.getByRole('button', { name: 'New opportunity' }).click()

  const wonName = `Won Journey ${Date.now()}`
  await page.getByLabel('Opportunity name').fill(wonName)
  await page.getByLabel('Account').fill('Enterprise Account')
  await page.getByLabel('Amount').fill('125000.50')
  await page.getByLabel('Currency').fill('BRL')
  await page.getByLabel('Expected close').fill('2026-12-31')
  await page.getByRole('button', { name: 'Create opportunity' }).click()

  await expect(page.getByRole('heading', { name: wonName })).toBeVisible()
  await expect(page.getByText(/version 1/)).toBeVisible()

  await page.getByRole('button', { name: 'Move to Discovery' }).click()
  await expect(page.getByRole('button', { name: 'Move to Proposal' })).toBeVisible()
  await page.getByRole('button', { name: 'Move to Proposal' }).click()
  await expect(page.getByRole('button', { name: 'Move to Negotiation' })).toBeVisible()
  await page.getByRole('button', { name: 'Move to Negotiation' }).click()
  await expect(page.getByRole('button', { name: 'Move to Won' })).toBeVisible()
  await page.getByRole('button', { name: 'Move to Won' }).click()
  await expect(page.getByText(/Won is terminal/)).toBeVisible()
  await expect(page.getByRole('button', { name: /Move to/ })).toHaveCount(0)

  const lost = await createOpportunityViaApi(page, `Lost Journey ${Date.now()}`)
  await page.goto(`/opportunities/${lost.id}`)
  await page.getByLabel('Loss reason').fill('Customer selected incumbent renewal')
  await page.getByRole('button', { name: 'Mark lost' }).click()
  await expect(page.getByText('Customer selected incumbent renewal')).toBeVisible()
  await expect(page.getByText(/Lost is terminal/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Mark lost' })).toHaveCount(0)
})

test('admin receives opportunity creation and transition controls', async ({ page }) => {
  await signIn(page, referenceUsers.admin, '/opportunities')
  await expect(page.getByRole('button', { name: 'New opportunity' })).toBeVisible()

  const opportunity = await createOpportunityViaApi(page, `Admin Journey ${Date.now()}`)
  await page.goto(`/opportunities/${opportunity.id}`)
  await expect(page.getByRole('button', { name: 'Move to Discovery' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Mark lost' })).toBeVisible()
})

test('stale workflow command refreshes authoritative state instead of retrying', async ({ page }) => {
  await signIn(page, referenceUsers.manager, '/opportunities')
  const opportunity = await createOpportunityViaApi(page, `Conflict Journey ${Date.now()}`)
  await page.goto(`/opportunities/${opportunity.id}`)

  await expect(page.getByText(/version 1/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Move to Discovery' })).toBeVisible()

  const concurrent = await page.request.post(`/api/opportunities/${opportunity.id}/commands/transition`, {
    data: { targetStage: 'discovery', expectedVersion: 1 },
  })
  expect(concurrent.status()).toBe(200)

  await page.getByRole('button', { name: 'Move to Discovery' }).click()
  await expect(page.getByRole('alert')).toContainText('changed after you loaded it')
  await expect(page.getByText(/version 2/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Move to Proposal' })).toBeVisible()
})
