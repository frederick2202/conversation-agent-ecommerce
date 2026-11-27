"use client";

/**
 * Painel lateral (drawer) do carrinho de compras.
 *
 * Montado globalmente em app/layout.tsx e aberto/fechado via `isCartOpen`
 * do StoreContext (botão "Carrinho" no TopHeader). Lista os itens do carrinho,
 * permite alterar quantidades/remover (cada ação chama a API e substitui o
 * carrinho local pela resposta) e leva ao checkout.
 */

import Link from "next/link";
import { Minus, Plus, Trash2, X } from "lucide-react";
import { useStore } from "@/context/StoreContext";
import { formatBRL } from "@/lib/api";

/** Drawer do carrinho; não renderiza nada enquanto estiver fechado. */
export function CartDrawer() {
  const { cart, isCartOpen, setCartOpen, updateItemQty } = useStore();
  if (!isCartOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
      <div className="flex h-full w-full max-w-md flex-col bg-[#0F2145] text-white shadow-2xl border-l border-white/10">
        {/* Cabeçalho: título com total de itens + botão fechar */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4 bg-[#0B172E]">
          <h2 className="text-base font-extrabold">Seu Carrinho ({cart?.total_items ?? 0})</h2>
          <button onClick={() => setCartOpen(false)} className="rounded-lg p-1.5 hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Lista de itens (rolável); -/+ alteram a quantidade e a lixeira envia quantidade 0 (remove) */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {!cart || cart.items.length === 0 ? (
            <p className="text-center text-sm text-slate-400 mt-10">
              Seu carrinho está vazio. Explore o catálogo ou peça ajuda à Lumen AI!
            </p>
          ) : (
            cart.items.map((item) => (
              <div key={item.item_id} className="flex gap-3 rounded-xl bg-[#132952] p-3 border border-white/10">
                <img src={item.image_url} alt={item.product_name} className="h-16 w-16 rounded-lg object-cover" />
                <div className="flex-1">
                  <p className="text-sm font-bold line-clamp-1">{item.product_name}</p>
                  <p className="text-[11px] text-slate-300">
                    {Object.entries(item.attributes).map(([k, v]) => `${k}: ${v}`).join(" • ")}
                  </p>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateItemQty(item.item_id, item.quantity - 1)}
                        className="rounded bg-[#0B172E] p-1 hover:bg-white/10"
                      >
                        <Minus className="h-3.5 w-3.5" />
                      </button>
                      <span className="text-xs font-bold">{item.quantity}</span>
                      <button
                        onClick={() => updateItemQty(item.item_id, item.quantity + 1)}
                        className="rounded bg-[#0B172E] p-1 hover:bg-white/10"
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => updateItemQty(item.item_id, 0)}
                        aria-label="Remover item"
                        className="ml-1 text-rose-400 hover:text-rose-300"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <span className="text-sm font-bold">{formatBRL(item.line_total)}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Rodapé: subtotal + link para checkout (desabilitado via CSS se o carrinho estiver vazio) */}
        <div className="border-t border-white/10 bg-[#0B172E] p-5 space-y-3">
          <div className="flex justify-between text-base font-extrabold">
            <span>Subtotal</span>
            <span>{formatBRL(cart?.subtotal ?? 0)}</span>
          </div>
          <Link
            href="/checkout"
            onClick={() => setCartOpen(false)}
            className={`block w-full rounded-xl py-3 text-center text-sm font-bold text-white transition ${
              cart && cart.items.length > 0
                ? "bg-emerald-600 hover:bg-emerald-500"
                : "pointer-events-none bg-slate-700 opacity-50"
            }`}
          >
            Finalizar Compra
          </Link>
        </div>
      </div>
    </div>
  );
}
