/**
 * Configuração do PostCSS: processa o CSS com Tailwind e adiciona
 * prefixos de navegador automaticamente (autoprefixer).
 */
/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;
