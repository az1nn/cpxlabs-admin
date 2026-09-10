import { describe, expect, it } from 'vitest'

import { demoDataProvider } from './demo-data-provider'
import { createHttpDataProvider } from './http-data-provider'

const genericCrudMethods = ['create', 'delete', 'getList', 'getOne', 'update']

function assertCrudOnly(provider: object) {
  expect(Object.keys(provider).sort()).toEqual(genericCrudMethods)
  expect('transition' in provider).toBe(false)
  expect('command' in provider).toBe(false)
  expect('executeCommand' in provider).toBe(false)
  expect('advanceStage' in provider).toBe(false)
  expect('transitionOpportunity' in provider).toBe(false)
}

describe('DataProvider architecture boundary', () => {
  it('keeps the demo provider generic CRUD-only', () => {
    assertCrudOnly(demoDataProvider)
  })

  it('keeps the HTTP provider generic CRUD-only', () => {
    assertCrudOnly(createHttpDataProvider({ baseUrl: '/api', fetch: (() => undefined) as unknown as typeof fetch }))
  })
})
