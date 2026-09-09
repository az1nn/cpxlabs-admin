import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@cpxlabs-admin/ui'

import { useAppSession } from '../../platform/authentication/session-provider'
import { SignInForm } from './sign-in-form'

type SignInPageProps = {
  onAuthenticated(): void
}

export function SignInPage({ onAuthenticated }: SignInPageProps) {
  const session = useAppSession()

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
          <SignInForm
            error={session.error}
            onSubmit={async (values) => {
              await session.signIn(values)
              onAuthenticated()
            }}
          />
        </CardContent>
      </Card>
    </main>
  )
}
