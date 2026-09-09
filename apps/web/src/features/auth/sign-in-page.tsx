import { zodResolver } from '@hookform/resolvers/zod'
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, FormField, Input } from '@cpxlabs-admin/ui'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { AuthenticationError } from '../../platform/authentication/auth-service'
import { useAppSession } from '../../platform/authentication/session-provider'

const signInSchema = z.object({
  email: z.string().trim().email('Enter a valid email address'),
  password: z.string().min(1, 'Enter your password'),
})

type SignInValues = z.infer<typeof signInSchema>

type SignInPageProps = {
  onAuthenticated(): void
}

export function SignInPage({ onAuthenticated }: SignInPageProps) {
  const session = useAppSession()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const form = useForm<SignInValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: '', password: '' },
  })

  const submit = form.handleSubmit(async (values) => {
    setSubmitError(null)
    try {
      await session.signIn(values)
      onAuthenticated()
    } catch (error) {
      setSubmitError(
        error instanceof AuthenticationError
          ? error.message
          : session.error ?? 'Unable to sign in. Try again.',
      )
    }
  })

  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-5">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to CPXLabs Admin</CardTitle>
          <CardDescription>
            Use your provisioned enterprise account to continue.
          </CardDescription>
        </CardHeader>
        <CardContent>
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

            {submitError || session.error ? (
              <p className="m-0 text-sm font-medium text-destructive" role="alert">
                {submitError ?? session.error}
              </p>
            ) : null}

            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}
