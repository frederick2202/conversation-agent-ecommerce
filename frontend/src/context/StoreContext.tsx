"use client";

/**
 * Estado global da loja (React Context), disponibilizado a toda a aplicação
 * pelo `StoreProvider` montado em app/layout.tsx.
 *
 * Responsabilidades:
 * - Gerar/persistir o `sessionId` anônimo que identifica o carrinho e o histórico
 *   de chat do visitante no backend (não há login).
 * - Manter o carrinho (`CartSummary`) sincronizado com a API.
 * - Controlar a abertura do CartDrawer.
 * - Exibir notificações "toast" globais.
 *
 * Consumido via hook `useStore()` por páginas e componentes (TopHeader,
 * CartDrawer, ProductDetailModal, LumenChatWidget, checkout, admin...).
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CartSummary } from "@/types";

/** Notificação temporária exibida no canto superior direito. */
interface ToastState {
  message: string;
  /** Define a cor: success = verde, error = vermelho, info = azul. */
  type: "success" | "error" | "info";
}

/** Valores e ações expostos pelo contexto da loja. */
interface StoreContextValue {
  /** ID anônimo da sessão; string vazia até o primeiro useEffect rodar no cliente. */
  sessionId: string;
  /** Carrinho atual vindo do backend; `null` até a primeira carga. */
  cart: CartSummary | null;
  isCartOpen: boolean;
  setCartOpen: (open: boolean) => void;
  /** Recarrega o carrinho do backend (usado, p.ex., quando o agente de IA altera o carrinho). */
  refreshCart: () => Promise<void>;
  /** Adiciona uma variação ao carrinho e mostra um toast de sucesso/erro. */
  addToCart: (variantId: string, qty?: number) => Promise<void>;
  /** Altera a quantidade de uma linha do carrinho (0 remove o item). */
  updateItemQty: (itemId: string, qty: number) => Promise<void>;
  toast: ToastState | null;
  showToast: (message: string, type?: ToastState["type"]) => void;
}

const StoreContext = createContext<StoreContextValue | null>(null);

/**
 * Provider do estado global da loja. Além de prover o contexto, renderiza
 * o toast global por cima de todo o conteúdo.
 */
export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string>("");
  const [cart, setCart] = useState<CartSummary | null>(null);
  const [isCartOpen, setCartOpen] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  /** Exibe um toast que some automaticamente após ~3,8 s. */
  const showToast = useCallback((message: string, type: ToastState["type"] = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3800);
  }, []);

  // Gera (na primeira visita) ou recupera do localStorage o ID de sessão anônimo.
  // Roda apenas no cliente, pois localStorage/crypto não existem no SSR.
  // O mesmo ID é usado pelo carrinho e pelo histórico do chat, por isso o
  // carrinho e a conversa persistem entre recarregamentos da página.
  useEffect(() => {
    let sid = localStorage.getItem("lumen_session_id");
    if (!sid) {
      sid = `lumen-${crypto.randomUUID()}`;
      localStorage.setItem("lumen_session_id", sid);
    }
    setSessionId(sid);
  }, []);

  /** Busca o carrinho no backend (que o cria vazio se ainda não existir). Erros são silenciados. */
  const refreshCart = useCallback(async () => {
    if (!sessionId) return;
    try {
      setCart(await api.getCart(sessionId));
    } catch {
      // Backend pode ainda estar iniciando
    }
  }, [sessionId]);

  // Carrega o carrinho assim que o sessionId fica disponível
  // (refreshCart muda de identidade quando sessionId muda).
  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  // As ações abaixo substituem o estado local pelo CartSummary devolvido
  // pela API, mantendo o backend como fonte da verdade (totais, estoque etc.).
  const addToCart = async (variantId: string, qty = 1) => {
    if (!sessionId) return;
    try {
      const updated = await api.addCartItem(sessionId, variantId, qty);
      setCart(updated);
      showToast("Produto adicionado ao carrinho!", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao adicionar item.", "error");
    }
  };

  const updateItemQty = async (itemId: string, qty: number) => {
    if (!sessionId) return;
    try {
      const updated = await api.updateCartItem(sessionId, itemId, qty);
      setCart(updated);
      showToast(qty === 0 ? "Item removido do carrinho." : "Quantidade atualizada.", "info");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao atualizar item.", "error");
    }
  };

  return (
    <StoreContext.Provider
      value={{
        sessionId,
        cart,
        isCartOpen,
        setCartOpen,
        refreshCart,
        addToCart,
        updateItemQty,
        toast,
        showToast,
      }}
    >
      {children}
      {/* Toast global (z-index alto para ficar acima de modais e do chat) */}
      {toast && (
        <div
          role="status"
          className={`fixed top-5 right-5 z-[100] rounded-lg px-4 py-3 text-sm font-medium text-white shadow-xl transition-all ${
            toast.type === "error"
              ? "bg-[#F04E5E]"
              : toast.type === "info"
              ? "bg-[#0099D6]"
              : "bg-emerald-600"
          }`}
        >
          {toast.message}
        </div>
      )}
    </StoreContext.Provider>
  );
}

/**
 * Hook de acesso ao estado global da loja.
 * @throws Error se usado fora de um `StoreProvider`.
 */
export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore deve ser usado dentro de StoreProvider");
  return ctx;
}
