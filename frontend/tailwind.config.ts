import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a12",
        surface: "#14141f",
        border: "#22222f",
        muted: "#8a8a9a",
        gain: "#34d399",
        loss: "#f43f5e",
      },
      fontFamily: {
        mono: ["SF Mono", "Consolas", "Menlo", "monospace"],
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(90deg, #7c6df0, #4f8ff0, #06b6d4)",
      },
    },
  },
  plugins: [],
};

export default config;
