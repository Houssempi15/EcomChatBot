import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "#6366F1",
          light: "#818CF8",
          dark: "#4F46E5",
        },
        cta: {
          DEFAULT: "#10B981",
          light: "#34D399",
          dark: "#059669",
        },
        brand: {
          bg: "#F5F3FF",
          text: "#1E1B4B",
          sidebar: "#1E1B4B",
          "sidebar-hover": "#2D2A5E",
          "sidebar-active": "#6366F1",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
