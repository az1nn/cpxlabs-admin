import type { ReactNode } from 'react'

export type FormFieldProps = {
  label: string
  htmlFor: string
  error?: string
  description?: string
  children: ReactNode
}

export function FormField({ label, htmlFor, error, description, children }: FormFieldProps) {
  return (
    <div className="grid gap-1.5">
      <label className="text-sm font-medium" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {description && !error ? (
        <p className="m-0 text-xs text-muted-foreground">{description}</p>
      ) : null}
      {error ? (
        <p className="m-0 text-xs font-medium text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
