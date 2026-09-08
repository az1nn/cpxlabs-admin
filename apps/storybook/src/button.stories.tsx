import { Button } from '@cpxlabs-admin/ui'
import type { Meta, StoryObj } from '@storybook/react-vite'

const meta = {
  title: 'Actions/Button',
  component: Button,
  args: {
    children: 'Save changes',
  },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

export const Primary: Story = {}

export const Outline: Story = {
  args: { variant: 'outline', children: 'Cancel' },
}

export const Destructive: Story = {
  args: { variant: 'destructive', children: 'Delete customer' },
}

export const Disabled: Story = {
  args: { disabled: true, children: 'Saving…' },
}
