import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "accent-1": "var(--accent-1)",
        "accent-2": "var(--accent-2)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        gain: "var(--gain)",
        loss: "var(--loss)",
      },
    },
  },
  plugins: [],
};

export default config;
