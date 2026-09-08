import type { ComponentProps } from 'react'

import { cn } from '../lib/cn'

export type SelectProps = ComponentProps<'select'>

export function Select({ className, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        'flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}
