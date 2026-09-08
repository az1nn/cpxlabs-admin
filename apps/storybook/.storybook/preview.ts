import '@cpxlabs-admin/ui/styles.css'

import type { Preview } from '@storybook/react-vite'

const preview: Preview = {
  parameters: {
    a11y: {
      test: 'error',
    },
    layout: 'centered',
  },
}

export default preview
