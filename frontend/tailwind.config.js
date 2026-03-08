/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
    theme: {
        spacing: {
            '0': '0px', '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px',
            '6': '24px', '7': '28px', '8': '32px', '9': '36px', '10': '40px',
            '12': '48px', '14': '56px', '16': '64px', '20': '80px', '24': '96px',
        },
        extend: {
            colors: {
                navy: { 50: '#E8EDF5', 100: '#C5D0E6', 200: '#8BA1CB', 300: '#4A6FA5', 400: '#1B3A6B', 500: '#0F172A', 600: '#0B1120', 700: '#070B16' },
                border: '#E2E8F0',
                surface: '#FFFFFF',
                workspace: '#F8FAFC',
                emerald: { 50: '#ECFDF5', 500: '#10B981', 600: '#059669', 700: '#047857' },
                gold: { 50: '#FFFBEB', 400: '#B45309', 500: '#92400E' },
                danger: { 50: '#FEF2F2', 500: '#DC2626', 600: '#991B1B' },
                warn: { 50: '#FFFBEB', 500: '#D97706', 600: '#92400E' },
            },
            fontFamily: {
                sans: ['"Inter"', '"Public Sans"', 'system-ui', 'sans-serif'],
                mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
            },
            fontSize: {
                'data': ['12px', { lineHeight: '16px' }],
                'label': ['11px', { lineHeight: '16px', letterSpacing: '0.04em' }],
                'body': ['13px', { lineHeight: '20px' }],
                'heading': ['15px', { lineHeight: '24px' }],
                'title': ['18px', { lineHeight: '28px' }],
            },
        },
    },
    plugins: [],
};
