/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#101F3C",
          50: "#E8EDF5",
          100: "#C5D1E6",
          200: "#8FA3CC",
          300: "#5A75B3",
          400: "#2D4E8A",
          500: "#101F3C",
          600: "#0d1a30",
          700: "#0a1426",
          800: "#070f1c",
          900: "#040a12",
        },
        accent: {
          DEFAULT: "#FA510F",
          light: "#FF7A3D",
          dark: "#E04500",
          glow: "rgba(250,81,15,0.15)",
        },
        emerald: {
          DEFAULT: "#10B981",
          light: "#34D399",
          dark: "#059669",
        },
        amber: {
          DEFAULT: "#F59E0B",
          light: "#FBBF24",
          dark: "#D97706",
        },
        coral: {
          DEFAULT: "#EF4444",
          light: "#F87171",
          dark: "#DC2626",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          secondary: "#FAFAFA",
          tertiary: "#F5F5F5",
          hover: "#F5F5F5",
        },
      },
      fontFamily: {
        display: ['"Barlow"', "sans-serif"],
        body: ['"Barlow"', "sans-serif"],
      },
      fontSize: {
        "xs": ["0.875rem", { lineHeight: "1.5" }],
        "sm": ["1rem", { lineHeight: "1.6" }],
      },
      boxShadow: {
        "glass": "0 8px 32px rgba(16,31,60,0.08)",
        "glass-lg": "0 16px 48px rgba(16,31,60,0.12)",
        "card": "0 1px 3px rgba(16,31,60,0.06), 0 1px 2px rgba(16,31,60,0.04)",
        "card-hover": "0 10px 25px rgba(16,31,60,0.1), 0 4px 10px rgba(16,31,60,0.06)",
        "glow-orange": "0 0 20px rgba(250,81,15,0.3)",
        "glow-emerald": "0 0 20px rgba(16,185,129,0.3)",
        "sidebar": "4px 0 24px rgba(16,31,60,0.15)",
        "modal": "0 25px 60px rgba(16,31,60,0.25)",
      },
      borderRadius: {
        "xl": "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "fade-in-up": "fadeInUp 0.5s ease-out",
        "fade-in-down": "fadeInDown 0.4s ease-out",
        "slide-in-right": "slideInRight 0.4s ease-out",
        "slide-in-left": "slideInLeft 0.3s ease-out",
        "scale-in": "scaleIn 0.3s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "float": "float 3s ease-in-out infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInDown: {
          "0%": { opacity: "0", transform: "translateY(-12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(250,81,15,0.2)" },
          "100%": { boxShadow: "0 0 20px rgba(250,81,15,0.4)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "mesh-gradient": "linear-gradient(135deg, #101F3C 0%, #1a2d4a 25%, #2a4060 50%, #FA510F 75%, #101F3C 100%)",
        "hero-gradient": "linear-gradient(135deg, #101F3C 0%, #1a2d4a 50%, #101F3C 100%)",
      },
    },
  },
  plugins: [],
};
