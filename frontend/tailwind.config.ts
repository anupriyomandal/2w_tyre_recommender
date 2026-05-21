import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ceat: {
          blue: '#0055AA',
          'dark-blue': '#273C6F',
          orange: '#F58220',
          'light-bg': '#EEF3FA',
          'pale-blue': '#E0EAF8',
        },
      },
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
      },
      keyframes: {
        'bounce-dot': {
          '0%, 80%, 100%': { transform: 'scale(0.55)', opacity: '0.35' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        'slide-up-fade': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-left-fade': {
          from: { opacity: '0', transform: 'translateX(-10px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'slide-right-fade': {
          from: { opacity: '0', transform: 'translateX(10px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'row-appear': {
          from: { opacity: '0', transform: 'translateX(-6px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        'bounce-dot': 'bounce-dot 1.4s ease-in-out infinite',
        'slide-up-fade': 'slide-up-fade 0.3s ease-out forwards',
        'slide-left-fade': 'slide-left-fade 0.28s ease-out forwards',
        'slide-right-fade': 'slide-right-fade 0.28s ease-out forwards',
        'row-appear': 'row-appear 0.2s ease-out forwards',
        'spin': 'spin 0.9s linear infinite',
      },
    },
  },
  plugins: [],
}

export default config
