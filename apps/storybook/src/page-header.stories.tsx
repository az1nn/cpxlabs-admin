import { Button, PageHeader } from '@cpxlabs-admin/ui'
import type { Meta, StoryObj } from '@storybook/react-vite'

const meta = {
  title: 'Layout/PageHeader',
  component: PageHeader,
} satisfies Meta<typeof PageHeader>

export default meta
type Story = StoryObj<typeof meta>

export const WithActions: Story = {
  args: {
    eyebrow: 'CRM / Customers',
    title: 'Customers',
    description: 'Manage customer records, status and lifecycle operations.',
    actions: (
      <>
        <Button variant="outline">Export</Button>
        <Button>New customer</Button>
      </>
    ),
  },
}
