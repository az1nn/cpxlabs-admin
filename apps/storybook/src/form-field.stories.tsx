import { FormField, Input, Select } from '@cpxlabs-admin/ui'
import type { Meta, StoryObj } from '@storybook/react-vite'

const meta = {
  title: 'Forms/FormField',
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <div className="grid w-80 gap-5">
      <FormField label="Email" htmlFor="storybook-email" description="Used for account notifications.">
        <Input id="storybook-email" type="email" defaultValue="admin@example.com" />
      </FormField>
      <FormField label="Status" htmlFor="storybook-status">
        <Select id="storybook-status" defaultValue="active">
          <option value="lead">Lead</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </Select>
      </FormField>
    </div>
  ),
}

export const ValidationError: Story = {
  render: () => (
    <div className="w-80">
      <FormField label="Email" htmlFor="storybook-invalid-email" error="Enter a valid email address.">
        <Input id="storybook-invalid-email" type="email" aria-invalid="true" defaultValue="invalid" />
      </FormField>
    </div>
  ),
}
