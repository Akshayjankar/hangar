import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        line: "var(--line)",
        text: "var(--text)",
        muted: "var(--muted)",
        primary: "var(--primary)",
        "primary-text": "var(--primary-text)",
        run: "var(--run)",
        "run-text": "var(--run-text)",
        start: "var(--start)",
        "start-text": "var(--start-text)",
        warn: "var(--warn)",
        "warn-text": "var(--warn-text)",
        err: "var(--err)",
        "err-text": "var(--err-text)",
        off: "var(--off)",
        // Categorical accents
        sky: "var(--accent-sky)",
        mint: "var(--accent-mint)",
        sand: "var(--accent-sand)",
        rose: "var(--accent-rose)",
        lilac: "var(--accent-lilac)",
        steel: "var(--accent-steel)",
      },
      fontFamily: {
        sans: ["var(--font-bricolage)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      borderRadius: {
        panel: "6px",
        rack: "6px",
        pill: "999px",
        input: "4px",
      },
    },
  },
  plugins: [],
};

export default config;

