import { zodResolver } from '@hookform/resolvers/zod'
import { Button, FormField, Input } from '@cpxlabs-admin/ui'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

const signInSchema = z.object({
  email: z.string().trim().email('Enter a valid email address'),
  password: z.string().min(1, 'Enter your password'),
})

export type SignInValues = z.infer<typeof signInSchema>

export type SignInFormProps = {
  error?: string | null
  onSubmit(values: SignInValues): Promise<void>
}

export function SignInForm({ error, onSubmit }: SignInFormProps) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const form = useForm<SignInValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: '', password: '' },
  })

  const submit = form.handleSubmit(async (values) => {
    setSubmitError(null)
    try {
      await onSubmit(values)
    } catch (cause) {
      setSubmitError(
        cause instanceof Error ? cause.message : 'Unable to sign in. Try again.',
      )
    }
  })

  return (
    <form className="grid gap-4" onSubmit={submit} noValidate>
      <FormField
        label="Email"
        htmlFor="email"
        error={form.formState.errors.email?.message}
      >
        <Input
          id="email"
          type="email"
          autoComplete="username"
          autoFocus
          aria-invalid={Boolean(form.formState.errors.email)}
          {...form.register('email')}
        />
      </FormField>

      <FormField
        label="Password"
        htmlFor="password"
        error={form.formState.errors.password?.message}
      >
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          aria-invalid={Boolean(form.formState.errors.password)}
          {...form.register('password')}
        />
      </FormField>

      {submitError || error ? (
        <p className="m-0 text-sm font-medium text-destructive" role="alert">
          {submitError ?? error}
        </p>
      ) : null}

      <Button type="submit" disabled={form.formState.isSubmitting}>
        {form.formState.isSubmitting ? 'Signing in…' : 'Sign in'}
      </Button>
    </form>
  )
}
