/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0e0e10',
        surface: '#18181b',
        elevated: '#1f1f23',
        border: '#2d2d35',
        purple: {
          DEFAULT: '#9146ff',
          hover: '#a970ff',
          dim: '#6b35c7',
        },
        text: {
          primary: '#efeff1',
          secondary: '#adadb8',
          muted: '#7d7d8e',
        },
      },
    },
  },
  plugins: [],
}
