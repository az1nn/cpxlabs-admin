import { createPrincipal } from '@cpxlabs-admin/authorization'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { AuthorizationProvider, Can } from './authorization-provider'

function renderActions(role: 'admin' | 'manager' | 'viewer') {
  const principal = createPrincipal({
    id: `user-${role}`,
    email: `${role}@example.com`,
    name: role,
    role,
  })

  return renderToStaticMarkup(
    <AuthorizationProvider principal={principal}>
      <Can capability="customers.create"><span>Create</span></Can>
      <Can capability="customers.update"><span>Update</span></Can>
      <Can capability="customers.delete"><span>Delete</span></Can>
    </AuthorizationProvider>,
  )
}

describe('AuthorizationProvider', () => {
  it('derives visible actions exclusively from the supplied Principal capabilities', () => {
    expect(renderActions('viewer')).not.toContain('Create')
    expect(renderActions('viewer')).not.toContain('Update')
    expect(renderActions('viewer')).not.toContain('Delete')

    expect(renderActions('manager')).toContain('Create')
    expect(renderActions('manager')).toContain('Update')
    expect(renderActions('manager')).not.toContain('Delete')

    expect(renderActions('admin')).toContain('Create')
    expect(renderActions('admin')).toContain('Update')
    expect(renderActions('admin')).toContain('Delete')
  })
})
