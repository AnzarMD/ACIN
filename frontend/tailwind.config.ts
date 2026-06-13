import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        acin: {
          green: "#22c55e",
          blue: "#3b82f6",
          purple: "#8b5cf6",
          orange: "#f97316",
          red: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};

export default config;
