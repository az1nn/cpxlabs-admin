import { zodResolver } from '@hookform/resolvers/zod'
import { Button, FormField, Input } from '@cpxlabs-admin/ui'
import { useForm } from 'react-hook-form'

import { opportunityFormSchema, type OpportunityFormValues } from './opportunity.schema'

type OpportunityFormProps = {
  defaultValues: OpportunityFormValues
  isSubmitting: boolean
  submitError?: string
  onSubmit: (values: OpportunityFormValues) => Promise<void> | void
  onCancel: () => void
}

export function OpportunityForm({
  defaultValues,
  isSubmitting,
  submitError,
  onSubmit,
  onCancel,
}: OpportunityFormProps) {
  const form = useForm<OpportunityFormValues>({
    resolver: zodResolver(opportunityFormSchema),
    defaultValues,
  })

  return (
    <form
      className="grid gap-5"
      noValidate
      onSubmit={form.handleSubmit(async (values) => onSubmit(values))}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField label="Opportunity name" htmlFor="opportunity-name" error={form.formState.errors.name?.message}>
          <Input id="opportunity-name" {...form.register('name')} />
        </FormField>
        <FormField label="Account" htmlFor="opportunity-account" error={form.formState.errors.accountName?.message}>
          <Input id="opportunity-account" autoComplete="organization" {...form.register('accountName')} />
        </FormField>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <FormField label="Amount" htmlFor="opportunity-amount" error={form.formState.errors.amount?.message}>
          <Input
            id="opportunity-amount"
            type="number"
            min="0"
            step="0.01"
            inputMode="decimal"
            {...form.register('amount', { valueAsNumber: true })}
          />
        </FormField>
        <FormField label="Currency" htmlFor="opportunity-currency" error={form.formState.errors.currency?.message}>
          <Input id="opportunity-currency" maxLength={3} className="uppercase" {...form.register('currency')} />
        </FormField>
        <FormField
          label="Expected close"
          htmlFor="opportunity-close-date"
          error={form.formState.errors.expectedCloseDate?.message}
        >
          <Input id="opportunity-close-date" type="date" {...form.register('expectedCloseDate')} />
        </FormField>
      </div>

      {submitError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive" role="alert">
          {submitError}
        </div>
      ) : null}

      <div className="flex justify-end gap-2 border-t pt-5">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>Cancel</Button>
        <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating…' : 'Create opportunity'}</Button>
      </div>
    </form>
  )
}
