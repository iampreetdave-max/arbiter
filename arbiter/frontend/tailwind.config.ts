import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Arbiter monochrome palette — no colour except critical states
        'bg-primary':    '#000000',
        'bg-secondary':  '#0a0a0a',
        'bg-tertiary':   '#111111',
        'bg-elevated':   '#1a1a1a',
        'text-primary':  '#ffffff',
        'text-secondary':'#a0a0a0',
        'text-muted':    '#555555',
        'border-default':'#222222',
        'border-hover':  '#444444',
        'border-focus':  '#ffffff',
        'color-success': '#22c55e',
        'color-error':   '#ef4444',
        'color-warning': '#f59e0b',
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'Menlo', 'Monaco', 'monospace'],
      },
      animation: {
        'blink':    'blink 1s step-end infinite',
        'shine':    'shine 3s linear infinite',
        'fade-in':  'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
        shine: {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition:  '200% center' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
