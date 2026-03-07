/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0e17",
        surface: "#111827",
        "surface-2": "#1a2235",
        "surface-3": "#1f2b3d",
        border: "#2a3650",
        "text-primary": "#e2e8f0",
        "text-dim": "#8896ae",
        "text-muted": "#5a6a84",
        accent: "#3b82f6",
        "accent-light": "#60a5fa",
      },
    },
  },
  plugins: [],
};
