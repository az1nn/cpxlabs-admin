import type { Meta, StoryObj } from '@storybook/react-vite'

import { OpportunityStageBadge } from '../../web/src/features/opportunities/opportunity-stage-badge'

const meta = {
  title: 'Features/Opportunity Stage Badge',
  component: OpportunityStageBadge,
  parameters: {
    layout: 'centered',
    a11y: { test: 'error' },
  },
  args: { stage: 'qualification' },
} satisfies Meta<typeof OpportunityStageBadge>

export default meta
type Story = StoryObj<typeof meta>

export const Qualification: Story = {}
export const Discovery: Story = { args: { stage: 'discovery' } }
export const Proposal: Story = { args: { stage: 'proposal' } }
export const Negotiation: Story = { args: { stage: 'negotiation' } }
export const Won: Story = { args: { stage: 'won' } }
export const Lost: Story = { args: { stage: 'lost' } }
