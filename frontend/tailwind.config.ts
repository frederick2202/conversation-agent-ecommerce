/**
 * Configuração do Tailwind CSS.
 * `content` indica onde procurar classes utilizadas (tudo em src/).
 * A paleta `lumen.*` registra as cores da marca como tokens (ex.: `bg-lumen-card`);
 * os componentes atuais, porém, usam majoritariamente os valores hex diretamente
 * (ex.: `bg-[#132952]`).
 */
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
