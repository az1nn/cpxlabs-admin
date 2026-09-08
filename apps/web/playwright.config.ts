import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]]
    : 'html',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      name: 'Fastify API',
      cwd: '../api',
      command: 'pnpm build && pnpm start',
      url: 'http://127.0.0.1:3001/health',
      env: {
        HOST: '127.0.0.1',
        PORT: '3001',
      },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      name: 'Vite web',
      command: 'pnpm build && pnpm exec vite preview --host 127.0.0.1 --port 4173 --strictPort',
      url: 'http://127.0.0.1:4173',
      env: {
        VITE_DATA_PROVIDER: 'http',
        VITE_API_BASE_URL: '/api',
      },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
})
