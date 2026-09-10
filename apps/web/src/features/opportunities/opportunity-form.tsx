import { zodResolver } from '@hookform/resolvers/zod'
import { Button, FormField, Input } from '@cpxlabs-admin/ui'
import { useForm } from 'react-hook-form'

import { currencyMinorUnitStep } from './opportunity-money'
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
  const currency = form.watch('currency')
  const minorUnitStep = currencyMinorUnitStep(currency)

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
            type="text"
            inputMode="decimal"
            pattern="[0-9]+([.][0-9]+)?"
            placeholder={`Minor-unit step ${minorUnitStep}`}
            title={`Use a non-negative decimal amount. ${currency.trim().toUpperCase() || 'Currency'} supports increments of ${minorUnitStep}.`}
            {...form.register('amount')}
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
