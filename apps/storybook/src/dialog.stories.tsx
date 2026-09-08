import {
  Button,
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from '@cpxlabs-admin/ui'
import type { Meta, StoryObj } from '@storybook/react-vite'

const meta = {
  title: 'Feedback/Dialog',
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const Confirmation: Story = {
  render: () => (
    <Dialog defaultOpen>
      <DialogContent>
        <div className="grid gap-2">
          <DialogTitle className="text-lg font-semibold">Delete customer?</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            This action permanently removes the customer from the current data provider.
          </DialogDescription>
        </div>
        <div className="flex justify-end gap-2">
          <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
          <Button variant="destructive">Delete customer</Button>
        </div>
      </DialogContent>
    </Dialog>
  ),
}
