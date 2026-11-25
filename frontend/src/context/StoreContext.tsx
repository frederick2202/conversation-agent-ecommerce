"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CartSummary } from "@/types";

interface ToastState {
  message: string;
  type: "success" | "error" | "info";
}

interface StoreContextValue {
  sessionId: string;
  cart: CartSummary | null;
  isCartOpen: boolean;
  setCartOpen: (open: boolean) => void;
  refreshCart: () => Promise<void>;
  addToCart: (variantId: string, qty?: number) => Promise<void>;
  updateItemQty: (itemId: string, qty: number) => Promise<void>;
  toast: ToastState | null;
  showToast: (message: string, type?: ToastState["type"]) => void;
}

const StoreContext = createContext<StoreContextValue | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string>("");
  const [cart, setCart] = useState<CartSummary | null>(null);
  const [isCartOpen, setCartOpen] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  const showToast = useCallback((message: string, type: ToastState["type"] = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3800);
  }, []);

  useEffect(() => {
    let sid = localStorage.getItem("lumen_session_id");
    if (!sid) {
      sid = `lumen-${crypto.randomUUID()}`;
      localStorage.setItem("lumen_session_id", sid);
    }
    setSessionId(sid);
  }, []);

  const refreshCart = useCallback(async () => {
    if (!sessionId) return;
    try {
      setCart(await api.getCart(sessionId));
    } catch {
      // Backend pode ainda estar iniciando
    }
  }, [sessionId]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

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

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore deve ser usado dentro de StoreProvider");
  return ctx;
}
