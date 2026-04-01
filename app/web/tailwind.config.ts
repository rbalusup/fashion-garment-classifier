import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ai: {
          50: '#eff6ff',
          100: '#dbeafe',
          400: '#60a5fa',
          700: '#1d4ed8',
        },
        designer: {
          50: '#fffbeb',
          100: '#fef3c7',
          400: '#fbbf24',
          700: '#b45309',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
