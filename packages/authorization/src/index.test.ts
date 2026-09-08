import { describe, expect, it } from 'vitest'

import { can, capabilitiesForRole, createPrincipal } from './index'

describe('role capability policy', () => {
  it('maps admin, manager and viewer to the reference matrix', () => {
    expect([...capabilitiesForRole('admin')]).toEqual([
      'customers.read',
      'customers.create',
      'customers.edit',
      'customers.delete',
    ])
    expect([...capabilitiesForRole('manager')]).toEqual([
      'customers.read',
      'customers.create',
      'customers.edit',
    ])
    expect([...capabilitiesForRole('viewer')]).toEqual(['customers.read'])
  })

  it('denies missing principals and missing capabilities by default', () => {
    expect(can(null, 'customers.read')).toBe(false)
    const viewer = createPrincipal({
      id: 'viewer',
      email: 'viewer@example.com',
      name: 'Viewer',
      role: 'viewer',
    })
    expect(can(viewer, 'customers.read')).toBe(true)
    expect(can(viewer, 'customers.edit')).toBe(false)
    expect(can(viewer, 'customers.delete')).toBe(false)
  })
})
