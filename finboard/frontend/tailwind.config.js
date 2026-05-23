/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0a0e14',
          panel: '#12171f',
          border: '#1e2a3a',
          green: '#00d4aa',
          red: '#ff4757',
          blue: '#4da6ff',
          yellow: '#ffd700',
          text: '#bfc7d5',
          muted: '#5c6e80',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
