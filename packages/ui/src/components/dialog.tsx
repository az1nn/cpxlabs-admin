import { Dialog as BaseDialog } from '@base-ui/react/dialog'
import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'

export const Dialog = BaseDialog.Root
export const DialogTrigger = BaseDialog.Trigger
export const DialogClose = BaseDialog.Close
export const DialogTitle = BaseDialog.Title
export const DialogDescription = BaseDialog.Description

export function DialogContent({ className, ...props }: ComponentProps<typeof BaseDialog.Popup>) {
  return (
    <BaseDialog.Portal>
      <BaseDialog.Backdrop className="fixed inset-0 z-50 bg-black/45 transition-opacity" />
      <BaseDialog.Popup
        className={cn(
          'fixed left-1/2 top-1/2 z-50 grid w-[min(92vw,32rem)] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-lg border bg-popover p-6 text-popover-foreground shadow-xl outline-none',
          className,
        )}
        {...props}
      />
    </BaseDialog.Portal>
  )
}
