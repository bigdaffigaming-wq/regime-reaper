/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#0A0A0A',
        gold: '#D4AF37',
        bone: '#E8E4D8',
        'profit-green': '#6AFF4F',
        amber: '#FF9F1C',
        crimson: '#C1121F',
        surface: '#111111',
        card: '#1A1A1A',
        border: '#2A2A2A',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
