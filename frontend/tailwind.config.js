/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        heading: ['"Work Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        bio: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          500: "#64748B",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
        },
        brand: {
          DEFAULT: "#2563EB",
          hover: "#1D4ED8",
          soft: "#DBEAFE",
        },
        danger: "#EF4444",
        warn: "#F59E0B",
        ok: "#10B981",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.04)",
      },
    },
  },
  plugins: [],
};
