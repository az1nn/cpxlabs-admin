import { zodResolver } from '@hookform/resolvers/zod'
import { Button, FormField, Input, Select } from '@cpxlabs-admin/ui'
import { useForm } from 'react-hook-form'

import { customerInputSchema } from './customer.schema'
import type { CustomerInput } from './customer.types'

type CustomerFormProps = {
  defaultValues: CustomerInput
  submitLabel: string
  isSubmitting: boolean
  submitError?: string
  onSubmit: (input: CustomerInput) => Promise<void> | void
  onCancel: () => void
}

export function CustomerForm({
  defaultValues,
  submitLabel,
  isSubmitting,
  submitError,
  onSubmit,
  onCancel,
}: CustomerFormProps) {
  const form = useForm<CustomerInput>({
    resolver: zodResolver(customerInputSchema),
    defaultValues,
  })

  return (
    <form
      className="grid gap-5"
      onSubmit={form.handleSubmit(async (values) => onSubmit(values))}
      noValidate
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField
          label="Name"
          htmlFor="customer-name"
          error={form.formState.errors.name?.message}
        >
          <Input id="customer-name" autoComplete="name" {...form.register('name')} />
        </FormField>

        <FormField
          label="Company"
          htmlFor="customer-company"
          error={form.formState.errors.company?.message}
        >
          <Input id="customer-company" autoComplete="organization" {...form.register('company')} />
        </FormField>
      </div>

      <FormField
        label="Email"
        htmlFor="customer-email"
        error={form.formState.errors.email?.message}
      >
        <Input id="customer-email" type="email" autoComplete="email" {...form.register('email')} />
      </FormField>

      <FormField
        label="Status"
        htmlFor="customer-status"
        error={form.formState.errors.status?.message}
      >
        <Select id="customer-status" {...form.register('status')}>
          <option value="lead">Lead</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </Select>
      </FormField>

      {submitError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive" role="alert">
          {submitError}
        </div>
      ) : null}

      <div className="flex justify-end gap-2 border-t pt-5">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : submitLabel}
        </Button>
      </div>
    </form>
  )
}
