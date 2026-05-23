/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        medical: {
          50: "#f0f7ff",
          100: "#e0effe",
          200: "#bae0fd",
          300: "#7cc5fb",
          400: "#36a7f7",
          500: "#0c8ce8",
          600: "#006fc6",
          700: "#0158a1",
          800: "#064b85",
          900: "#0b3f6e",
          950: "#072849"
        },
        tealmed: {
          50: "#edfffe",
          100: "#d1fffe",
          200: "#a8fffd",
          300: "#6bfbfa",
          400: "#27edef",
          500: "#00d0d5",
          600: "#00a6b2",
          700: "#05838f",
          800: "#0d6873",
          900: "#105661",
          950: "#023841"
        }
      },
      boxShadow: {
        card: "0 4px 20px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(15, 23, 42, 0.06)",
        "card-hover": "0 20px 50px rgba(15, 23, 42, 0.15), 0 8px 16px rgba(15, 23, 42, 0.08)",
        glow: "0 0 30px rgba(8, 145, 178, 0.3), 0 0 60px rgba(47, 99, 245, 0.15)",
        "glow-strong": "0 0 40px rgba(8, 145, 178, 0.4), 0 0 80px rgba(47, 99, 245, 0.2)",
        inner: "inset 0 2px 8px rgba(15, 23, 42, 0.1)",
        panel: "0 24px 80px rgba(0, 0, 0, 0.38)",
        "panel-strong": "0 0 0 1px rgba(45, 212, 191, 0.18), 0 24px 70px rgba(8, 145, 178, 0.15), 0 0 42px rgba(45, 212, 191, 0.15)"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Rajdhani", "Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      animation: {
        "fade-in": "fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-up": "slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1)",
        "float": "floatGentle 3s ease-in-out infinite",
        "pulse-soft": "pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer": "shimmer 1.8s linear infinite",
        drift: "drift 8s ease-in-out infinite"
      },
      backdropBlur: {
        xs: "2px"
      },
      borderRadius: {
        "4xl": "2rem"
      }
    }
  },
  plugins: []
};
