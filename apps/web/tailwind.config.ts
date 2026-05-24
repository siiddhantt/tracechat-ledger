import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        paper: "#fffaf0",
        marker: "#fff176",
        mint: "#b8f3d4",
        coral: "#ffb3a7",
        sky: "#a7d8ff",
      },
      boxShadow: {
        sketch: "5px 5px 0 #171717",
        sketchSoft: "3px 3px 0 #171717",
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};

export default config;
