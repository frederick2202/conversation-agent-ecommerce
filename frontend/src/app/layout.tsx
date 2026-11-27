/**
 * Layout raiz do App Router (Next.js 14) — envolve todas as páginas.
 *
 * Define metadados de SEO, fonte Inter, tema escuro e monta, uma única vez
 * para toda a aplicação:
 * - `StoreProvider`: estado global (sessão, carrinho, toasts);
 * - `CartDrawer`: painel lateral do carrinho (aberto pelo TopHeader);
 * - `LumenChatWidget`: chat flutuante com o agente de IA.
 * Por estarem no layout, carrinho e chat ficam disponíveis em todas as rotas
 * (/, /checkout, /admin) sem perder estado na navegação client-side.
 */
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { StoreProvider } from "@/context/StoreContext";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { LumenChatWidget } from "@/components/chat/LumenChatWidget";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lumen | E-Commerce de Eletrônicos com IA",
  description: "Loja de eletrônicos de alta performance com assistente conversacional em tempo real.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} bg-[#0B172E] text-white antialiased`}>
        <StoreProvider>
          {/* Conteúdo da rota atual */}
          {children}
          {/* Componentes globais sobrepostos (fixed), compartilhando o StoreContext */}
          <CartDrawer />
          <LumenChatWidget />
        </StoreProvider>
      </body>
    </html>
  );
}
