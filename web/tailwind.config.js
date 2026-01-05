/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#FFA500',
          primaryHover: '#FF8C00',
          soft: '#FFF5E6',
          mid: '#FFE5CC',
          deep: '#FF6600',
        },
        // 添加 gray 色系以兼容现有代码
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
      },
      animation: {
        'loading-bar': 'loading-bar 0.8s ease-in-out',
        'typing': 'typing 1.5s infinite',
      },
      keyframes: {
        'loading-bar': {
          '0%': { width: '0' },
          '50%': { width: '60%' },
          '100%': { width: '100%' },
        },
        'typing': {
          '0%, 60%, 100%': { transform: 'translateY(0)' },
          '30%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}
