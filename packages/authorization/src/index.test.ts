import { describe, expect, it } from 'vitest'

import { can, capabilitiesForRole, createPrincipal } from './index'

describe('role capability policy', () => {
  it('maps admin, manager and viewer to the reference matrix', () => {
    expect([...capabilitiesForRole('admin')]).toEqual([
      'customers.read',
      'customers.create',
      'customers.update',
      'customers.delete',
      'opportunities.read',
      'opportunities.create',
      'opportunities.transition',
      'audit.read',
    ])
    expect([...capabilitiesForRole('manager')]).toEqual([
      'customers.read',
      'customers.create',
      'customers.update',
      'opportunities.read',
      'opportunities.create',
      'opportunities.transition',
    ])
    expect([...capabilitiesForRole('viewer')]).toEqual([
      'customers.read',
      'opportunities.read',
    ])
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
    expect(can(viewer, 'opportunities.read')).toBe(true)
    expect(can(viewer, 'customers.update')).toBe(false)
    expect(can(viewer, 'customers.delete')).toBe(false)
    expect(can(viewer, 'opportunities.create')).toBe(false)
    expect(can(viewer, 'opportunities.transition')).toBe(false)
    expect(can(viewer, 'audit.read')).toBe(false)
  })
})
