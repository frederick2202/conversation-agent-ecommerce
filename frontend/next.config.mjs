/**
 * Configuração do Next.js.
 * `images.remotePatterns` libera qualquer host HTTPS para o componente next/image,
 * já que as imagens de produto são URLs externas cadastradas no admin
 * (atualmente as telas usam <img> simples, mas a regra fica pronta para next/image).
 */
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**" },
    ],
  },
};

export default nextConfig;
