/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        "surface-2": "var(--color-surface-2)",
        "surface-3": "var(--color-surface-3)",
        border: "var(--color-border)",
        "text-primary": "var(--color-text-primary)",
        "text-dim": "var(--color-text-dim)",
        "text-muted": "var(--color-text-muted)",
        accent: "var(--color-accent)",
        "accent-light": "var(--color-accent-light)",
      },
    },
  },
  plugins: [],
};
