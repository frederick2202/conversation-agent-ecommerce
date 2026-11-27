"use client";

/**
 * Página de checkout (rota "/checkout").
 *
 * Mostra o resumo do carrinho atual (lido do StoreContext), pede confirmação
 * em um modal e chama `POST /api/v1/cart/{session_id}/checkout`. O backend
 * simula o pagamento: gera um código de pedido e esvazia o carrinho.
 * Esta rota também é o destino do link "Ir para o Checkout" exibido pelo
 * chat da Lumen AI (ui_action CART_UPDATED) e do botão do CartDrawer.
 */

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { api, formatBRL } from "@/lib/api";
import { useStore } from "@/context/StoreContext";

export default function CheckoutPage() {
  const { sessionId, cart, refreshCart, showToast } = useStore();
  /** Controla o modal de confirmação ("Finalizar pedido?"). */
  const [confirmOpen, setConfirmOpen] = useState(false);
  /** Resultado do pedido concluído; quando preenchido, a tela de sucesso substitui o resumo. */
  const [orderDone, setOrderDone] = useState<{ order_code: string; message: string } | null>(null);

  /** Finaliza o pedido no backend e recarrega o carrinho (que agora estará vazio). */
  const handleConfirmOrder = async () => {
    try {
      const res = await api.checkout(sessionId);
      setOrderDone({ order_code: res.order_code, message: res.message });
      setConfirmOpen(false);
      await refreshCart();
      showToast("Pedido finalizado com sucesso!", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao finalizar pedido.", "error");
    }
  };

  return (
    <div className="min-h-screen bg-[#0B172E] px-4 py-10">
      <div className="mx-auto max-w-3xl space-y-6">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Voltar para a loja
        </Link>

        {orderDone ? (
          /* Tela de sucesso após o pedido */
          <div className="rounded-2xl bg-[#132952] border border-emerald-500/40 p-8 text-center space-y-3">
            <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-400" />
            <h1 className="text-2xl font-extrabold">Pedido {orderDone.order_code} confirmado!</h1>
            <p className="text-sm text-slate-300">{orderDone.message}</p>
            <Link href="/" className="inline-block rounded-lg bg-[#0099D6] px-6 py-2.5 text-sm font-bold text-white">
              Continuar comprando
            </Link>
          </div>
        ) : (
          /* Resumo do carrinho (itens, atributos da variação e total) */
          <div className="rounded-2xl bg-[#132952] border border-white/10 p-6 space-y-5">
            <h1 className="text-2xl font-extrabold">Resumo do Checkout</h1>
            {!cart || cart.items.length === 0 ? (
              <p className="text-slate-300">Seu carrinho está vazio.</p>
            ) : (
              <>
                <div className="divide-y divide-white/10">
                  {cart.items.map((item) => (
                    <div key={item.item_id} className="flex justify-between py-3 text-sm">
                      <div>
                        <p className="font-bold">{item.product_name}</p>
                        <p className="text-xs text-slate-400">
                          Qtd: {item.quantity} •{" "}
                          {Object.entries(item.attributes).map(([k, v]) => `${k}: ${v}`).join(" | ")}
                        </p>
                      </div>
                      <span className="font-bold">{formatBRL(item.line_total)}</span>
                    </div>
                  ))}
                </div>

                <div className="flex justify-between border-t border-white/10 pt-4 text-lg font-black">
                  <span>Total</span>
                  <span>{formatBRL(cart.subtotal)}</span>
                </div>

                <button
                  onClick={() => setConfirmOpen(true)}
                  className="w-full rounded-xl bg-emerald-600 py-3.5 text-sm font-bold text-white hover:bg-emerald-500 transition"
                >
                  Confirmar e Pagar
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Modal de confirmação do pagamento */}
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-w-sm rounded-2xl bg-[#0F2145] border border-white/15 p-6 space-y-4">
            <h2 className="text-lg font-bold">Finalizar pedido?</h2>
            <p className="text-sm text-slate-300">
              Ao confirmar, o pagamento de {formatBRL(cart?.subtotal ?? 0)} será processado.
            </p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setConfirmOpen(false)} className="rounded-lg bg-white/10 px-4 py-2 text-sm">
                Cancelar
              </button>
              <button onClick={handleConfirmOrder} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold">
                Confirmar Pedido
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
