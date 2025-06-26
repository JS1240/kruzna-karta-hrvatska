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
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "heartBeat": "heartBeat 0.5s ease-in-out",
      },
      fontFamily: {
        josefin: ["Josefin Sans", "sans-serif"],
        sreda: ["sreda", "serif"],
        sofia: ["sofia-pro", "sans-serif"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
