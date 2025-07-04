import { type Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        
        // Brand Colors - New Color Scheme (Animated Background Redesign)
        brand: {
          primary: "hsl(var(--brand-primary))", // #3674B5
          secondary: "hsl(var(--brand-secondary))", // #578FCA
          "accent-cream": "hsl(var(--brand-accent-cream))", // #F5F0CD
          "accent-gold": "hsl(var(--brand-accent-gold))", // #FADA7A
          black: "hsl(var(--brand-black))", // #000000
          white: "hsl(var(--brand-white))", // #FFFFFF
          // Derived variations for UI hierarchy
          "primary-light": "hsl(var(--brand-primary-light))",
          "primary-dark": "hsl(var(--brand-primary-dark))",
          "secondary-light": "hsl(var(--brand-secondary-light))",
          "secondary-dark": "hsl(var(--brand-secondary-dark))",
        },
        
        // UI Accent Elements using brand accent colors
        "accent-cream": "hsl(var(--brand-accent-cream))",
        "accent-gold": "hsl(var(--brand-accent-gold))",
        "focus-ring": "hsl(var(--focus-ring))",
        "highlight-bg": "hsl(var(--highlight-bg))",
        "notification-accent": "hsl(var(--notification-accent))",
        "badge-accent": "hsl(var(--badge-accent))",
        
        // Animation Colors - for VANTA topology backgrounds
        animation: {
          primary: "hsl(var(--animation-primary))",
          secondary: "hsl(var(--animation-secondary))",
          background: "hsl(var(--animation-background))",
        },
        
        // Legacy colors (maintained for backward compatibility)
        "lightest-blue": "#caf0f8",
        "navy-blue": "#193459",
        "light-blue": "#d5e3f0",
        "medium-blue": "#8fb3d9",
        cream: {
          DEFAULT: '#caf0f8',
        },
        "blue_green": {
          50: "#f0fdfa",
          100: "#ccfbf1", 
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
        },
        "sky_blue": {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0", opacity: "0" },
          to: { height: "var(--radix-accordion-content-height)", opacity: "1" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)", opacity: "1" },
          to: { height: "0", opacity: "0" },
        },
        "heartBeat": {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.3)' },
          '100%': { transform: 'scale(1)' },
        },
        
        // Motion-safe keyframes
        "fade-in": {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        "slide-in": {
          'from': { 
            opacity: '0',
            transform: 'translateY(20px)',
          },
          'to': { 
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        "scale-in": {
          'from': { 
            opacity: '0',
            transform: 'scale(0.95)',
          },
          'to': { 
            opacity: '1',
            transform: 'scale(1)',
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "heartBeat": "heartBeat 0.5s ease-in-out",
        
        // Reduced motion-safe animations
        "fade-in-safe": "fade-in 0.3s ease-out",
        "slide-in-safe": "slide-in 0.3s ease-out",
        "scale-in-safe": "scale-in 0.2s ease-out",
        
        // Enhanced animations for motion preference
        "fade-in-enhanced": "fade-in 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        "slide-in-enhanced": "slide-in 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        "scale-in-enhanced": "scale-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
      fontFamily: {
        josefin: ["Josefin Sans", "sans-serif"],
        sreda: ["sreda", "serif"],
        sofia: ["sofia-pro", "sans-serif"],
      },
      
      // Motion-aware transition durations
      transitionDuration: {
        'motion-safe': '150ms',
        'motion-reduce': '0ms',
        'motion-enhanced': '400ms',
      },
      
      // Custom CSS properties for motion control
      spacing: {
        'motion-offset': 'var(--motion-offset, 20px)',
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
    
    // Custom plugin for motion preferences
    function({ addUtilities, theme, variants }) {
      const motionUtilities = {
        // Reduced motion utilities
        '.motion-reduce-transform': {
          '@media (prefers-reduced-motion: reduce)': {
            transform: 'none !important',
          },
        },
        '.motion-reduce-animation': {
          '@media (prefers-reduced-motion: reduce)': {
            animation: 'none !important',
          },
        },
        '.motion-reduce-transition': {
          '@media (prefers-reduced-motion: reduce)': {
            transition: 'none !important',
          },
        },
        
        // Safe motion utilities
        '.motion-safe-fade': {
          opacity: '0',
          transition: 'opacity 0.3s ease-out',
          '@media (prefers-reduced-motion: reduce)': {
            opacity: '1',
            transition: 'none',
          },
        },
        '.motion-safe-slide': {
          transform: 'translateY(20px)',
          opacity: '0',
          transition: 'transform 0.3s ease-out, opacity 0.3s ease-out',
          '@media (prefers-reduced-motion: reduce)': {
            transform: 'none',
            opacity: '1',
            transition: 'none',
          },
        },
        '.motion-safe-scale': {
          transform: 'scale(0.95)',
          opacity: '0',
          transition: 'transform 0.2s ease-out, opacity 0.2s ease-out',
          '@media (prefers-reduced-motion: reduce)': {
            transform: 'none',
            opacity: '1',
            transition: 'none',
          },
        },
        
        // Enhanced motion utilities (for users who prefer motion)
        '.motion-enhanced-bounce': {
          '@media (prefers-reduced-motion: no-preference)': {
            animation: 'bounce 1s infinite',
          },
        },
        '.motion-enhanced-pulse': {
          '@media (prefers-reduced-motion: no-preference)': {
            animation: 'pulse 2s infinite',
          },
        },
        '.motion-enhanced-spin': {
          '@media (prefers-reduced-motion: no-preference)': {
            animation: 'spin 1s linear infinite',
          },
        },
        
        // Animation state utilities
        '.animate-in': {
          opacity: '1',
          transform: 'none',
        },
        '.animate-out': {
          opacity: '0',
          transform: 'translateY(20px)',
          '@media (prefers-reduced-motion: reduce)': {
            transform: 'none',
          },
        },
        
        // Custom motion-aware animations
        '.motion-aware-heartbeat': {
          '@media (prefers-reduced-motion: no-preference)': {
            animation: 'heartBeat 0.5s ease-in-out',
          },
          '@media (prefers-reduced-motion: reduce)': {
            transform: 'scale(1.05)',
            transition: 'transform 0.1s ease-out',
          },
        },
        
        // Loading states with motion preference
        '.loading-motion-safe': {
          '@media (prefers-reduced-motion: no-preference)': {
            animation: 'spin 1s linear infinite',
          },
          '@media (prefers-reduced-motion: reduce)': {
            animation: 'pulse 2s ease-in-out infinite',
          },
        },
        
        // Hover effects with motion preference
        '.hover-motion-safe': {
          transition: 'all 0.2s ease-out',
          '@media (prefers-reduced-motion: reduce)': {
            transition: 'none',
          },
          '&:hover': {
            transform: 'translateY(-2px)',
            '@media (prefers-reduced-motion: reduce)': {
              transform: 'none',
            },
          },
        },
      };
      
      addUtilities(motionUtilities);
    },
  ],
} satisfies Config;
