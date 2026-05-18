/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Custom dark cyber palette
        cyber: {
          bg:       '#0a0e1a',
          surface:  '#0f1629',
          card:     '#141d35',
          border:   '#1e2d4a',
          accent:   '#00d4ff',
          green:    '#00ff88',
          red:      '#ff3366',
          orange:   '#ff8c00',
          yellow:   '#ffd700',
          purple:   '#9d4edd',
          text:     '#c8d8f0',
          muted:    '#5a7090',
        },
      },
      fontFamily: {
        mono:    ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Orbitron', 'monospace'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow':  'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-line':   'scanLine 2s linear infinite',
        'glow':        'glow 2s ease-in-out infinite alternate',
        'fade-in':     'fadeIn 0.3s ease-out',
        'slide-in':    'slideIn 0.3s ease-out',
        'blink':       'blink 1s step-end infinite',
      },
      keyframes: {
        scanLine: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glow: {
          'from': { boxShadow: '0 0 10px #00d4ff44' },
          'to':   { boxShadow: '0 0 20px #00d4ff88, 0 0 40px #00d4ff44' },
        },
        fadeIn: {
          from: { opacity: 0, transform: 'translateY(8px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        slideIn: {
          from: { opacity: 0, transform: 'translateX(-16px)' },
          to:   { opacity: 1, transform: 'translateX(0)' },
        },
        blink: {
          '0%, 100%': { opacity: 1 },
          '50%':      { opacity: 0 },
        },
      },
      backgroundImage: {
        'grid-cyber': `
          linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)
        `,
      },
      backgroundSize: {
        'grid-cyber': '40px 40px',
      },
    },
  },
  plugins: [],
}
