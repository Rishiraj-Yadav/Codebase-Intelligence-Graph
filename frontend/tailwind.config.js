/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0B0F17',
          surface: '#111827',
          card: '#1F2937',
          border: '#374151',
          accent: '#3B82F6'
        },
        intent: {
          authentication: '#EF4444',     // Red
          'data processing': '#3B82F6',   // Blue
          'API communication': '#10B981', // Emerald
          'business logic': '#F59E0B',    // Amber
          database: '#8B5CF6',            // Purple
          'UI rendering': '#EC4899',      // Pink
          testing: '#6B7280',             // Gray
          configuration: '#6366F1',       // Indigo
          'error handling': '#DC2626',    // Dark Red
          caching: '#14B8A6',             // Teal
          logging: '#9CA3AF',             // Slate
          'file I/O': '#D97706',          // Dark Amber
          'machine learning': '#06B6D4',  // Cyan
          messaging: '#A855F7',          // Violet
          utility: '#64748B'              // Slate Dark
        }
      },
      animation: {
        'pulse-smell': 'pulseSmell 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-impact': 'glowImpact 1.5s ease-in-out infinite alternate',
      },
      keyframes: {
        pulseSmell: {
          '0%, 100%': { stroke: '#EF4444', strokeWidth: '3px', strokeOpacity: '1.0' },
          '50%': { stroke: '#F87171', strokeWidth: '7px', strokeOpacity: '0.4' },
        },
        glowImpact: {
          '0%': { filter: 'drop-shadow(0 0 6px rgba(245, 158, 11, 0.8))' },
          '100%': { filter: 'drop-shadow(0 0 16px rgba(239, 68, 68, 0.9))' }
        }
      }
    },
  },
  plugins: [],
}
