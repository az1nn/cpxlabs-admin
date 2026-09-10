import type { Meta, StoryObj } from '@storybook/react-vite'

import { OpportunityWorkflowPanel } from '../../web/src/features/opportunities/opportunity-workflow-panel'
import { AuthorizationProvider } from '../../web/src/platform/authorization/authorization-provider'

const managerPrincipal = {
  id: 'storybook-manager',
  email: 'manager@storybook.local',
  name: 'Storybook Manager',
  role: 'manager' as const,
  capabilities: new Set([
    'opportunities.read',
    'opportunities.create',
    'opportunities.transition',
  ] as const),
}

const proposalOpportunity = {
  id: 'opp_storybook',
  name: 'Enterprise Renewal',
  accountName: 'Acme Brasil',
  amountMinor: 12_500_000,
  currency: 'BRL',
  expectedCloseDate: '2026-11-30',
  stage: 'proposal' as const,
  version: 3,
  lossReason: null,
  createdAt: '2026-09-01T12:00:00.000Z',
  updatedAt: '2026-09-09T12:00:00.000Z',
}

const meta = {
  title: 'Features/Opportunity Workflow',
  component: OpportunityWorkflowPanel,
  decorators: [
    (Story) => (
      <AuthorizationProvider principal={managerPrincipal}>
        <div style={{ width: 'min(720px, 90vw)' }}><Story /></div>
      </AuthorizationProvider>
    ),
  ],
  parameters: {
    layout: 'centered',
    a11y: { test: 'error' },
  },
  args: {
    opportunity: proposalOpportunity,
    isPending: false,
    onTransition: () => undefined,
  },
} satisfies Meta<typeof OpportunityWorkflowPanel>

export default meta
type Story = StoryObj<typeof meta>

export const ProposalActions: Story = {}

export const ConflictRecoveryMessage: Story = {
  args: {
    conflictMessage: 'This opportunity changed after you loaded it. The latest server state has been refreshed; review it before issuing another command.',
  },
}

export const PendingCommand: Story = {
  args: { isPending: true },
}

export const TerminalWon: Story = {
  args: {
    opportunity: {
      ...proposalOpportunity,
      stage: 'won',
      version: 5,
    },
  },
}
