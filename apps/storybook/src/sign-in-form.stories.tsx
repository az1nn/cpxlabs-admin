import type { Meta, StoryObj } from '@storybook/react-vite'

import { SignInForm } from '../../web/src/features/auth/sign-in-form'

const meta = {
  title: 'Authentication/SignInForm',
  component: SignInForm,
  args: {
    onSubmit: async () => undefined,
  },
  parameters: {
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <div className="w-[24rem] rounded-lg border bg-background p-6 shadow-sm">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof SignInForm>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const InvalidCredentials: Story = {
  args: {
    error: 'Invalid email or password',
  },
}
