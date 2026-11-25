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
          {children}
          <CartDrawer />
          <LumenChatWidget />
        </StoreProvider>
      </body>
    </html>
  );
}
