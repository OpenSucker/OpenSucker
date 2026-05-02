/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          0: '#050508',
          1: '#0a0a12',
          2: '#12121f',
          3: '#1a1a2e',
        },
        accent: {
          DEFAULT: '#00ff96',
          soft: 'rgba(0,255,150,0.1)',
        },
        text: {
          1: '#ffffff',
          2: '#a0a0c0',
          3: '#606080',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Noto Sans SC', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        r: '12px',
      }
    },
  },
  plugins: [],
}
