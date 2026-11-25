import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        lumen: {
          bg: "#0B172E",
          sidebar: "#0F2B5B",
          card: "#132952",
          trust: "#071124",
          cyan: "#0099D6",
          coral: "#F04E5E",
        },
      },
    },
  },
  plugins: [],
};

export default config;
