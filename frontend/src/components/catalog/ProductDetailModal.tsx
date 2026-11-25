"use client";

import { useEffect, useState } from "react";
import { ShoppingCart, Star, X } from "lucide-react";
import { api, formatBRL } from "@/lib/api";
import { useStore } from "@/context/StoreContext";
import { Product, Review } from "@/types";

interface Props {
  product: Product | null;
  onClose: () => void;
  onReviewAdded: () => void;
}

export function ProductDetailModal({ product, onClose, onReviewAdded }: Props) {
  const { addToCart, showToast } = useStore();
  const [selectedVariantId, setSelectedVariantId] = useState<string>("");
  const [reviews, setReviews] = useState<Review[]>([]);
  const [rating, setRating] = useState<number>(5);
  const [authorName, setAuthorName] = useState<string>("");
  const [comment, setComment] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!product) return;
    const firstAvailable = product.variants.find((v) => v.stock_quantity > 0);
    setSelectedVariantId(firstAvailable?.id || "");
    api.listReviews(product.id).then(setReviews).catch(() => setReviews([]));
  }, [product]);

  if (!product) return null;

  const selectedVariant = product.variants.find((v) => v.id === selectedVariantId);
  const displayPrice = selectedVariant?.price_override ?? product.price;

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating < 1 || rating > 5) return;
    setSubmitting(true);
    try {
      const created = await api.createReview(product.id, {
        author_name: authorName.trim() || "Cliente Lumen",
        rating,
        comment: comment.trim() || undefined,
      });
      setReviews((prev) => [created, ...prev]);
      setComment("");
      setAuthorName("");
      setRating(5);
      showToast("Avaliação registrada com sucesso! Obrigado pelo feedback.", "success");
      onReviewAdded();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao enviar avaliação.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-[#0F2145] border border-white/15 text-white shadow-2xl">
        <div className="sticky top-0 flex items-center justify-between bg-[#0B172E] px-6 py-4 border-b border-white/10">
          <div>
            <span className="text-xs font-mono text-cyan-400">{product.sku} • {product.brand}</span>
            <h2 className="text-lg font-extrabold">{product.name}</h2>
          </div>
          <button onClick={onClose} aria-label="Fechar modal" className="rounded-lg p-2 hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
          <img src={product.image_url} alt={product.name} className="w-full rounded-xl object-cover aspect-video" />

          <div className="space-y-4">
            <p className="text-sm text-slate-300">{product.description}</p>
            <div className="text-2xl font-black text-white">{formatBRL(displayPrice)}</div>

            <div>
              <p className="text-xs font-bold uppercase text-slate-400 mb-2">Selecione a variação:</p>
              <div className="flex flex-wrap gap-2">
                {product.variants.map((variant) => {
                  const out = variant.stock_quantity === 0;
                  const label = Object.entries(variant.attributes)
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(" | ");
                  return (
                    <button
                      key={variant.id}
                      disabled={out}
                      onClick={() => setSelectedVariantId(variant.id)}
                      className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                        out
                          ? "cursor-not-allowed border-white/5 bg-white/5 text-slate-500 line-through"
                          : selectedVariantId === variant.id
                          ? "border-cyan-400 bg-[#0099D6] text-white"
                          : "border-white/20 bg-[#132952] text-slate-200 hover:border-cyan-300"
                      }`}
                    >
                      {label} ({variant.stock_quantity} disp.)
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              disabled={!selectedVariantId}
              onClick={() => addToCart(selectedVariantId, 1)}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#0099D6] py-3.5 text-sm font-bold text-white hover:bg-[#0082B8] disabled:opacity-40 transition"
            >
              <ShoppingCart className="h-4 w-4" />
              Adicionar ao Carrinho
            </button>
          </div>
        </div>

        <div className="border-t border-white/10 p-6 space-y-6 bg-[#0B172E]/60">
          <h3 className="text-base font-extrabold">Avaliações dos Clientes ({reviews.length})</h3>

          <form onSubmit={handleReviewSubmit} className="rounded-xl bg-[#132952] p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs font-bold uppercase text-slate-300">Sua nota (1 a 5 estrelas):</span>
              <div className="flex items-center gap-1" role="radiogroup" aria-label="Nota de 1 a 5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    type="button"
                    key={star}
                    onClick={() => setRating(star)}
                    aria-label={`${star} estrelas`}
                    className="p-1 transition hover:scale-110"
                  >
                    <Star
                      className={`h-6 w-6 ${
                        star <= rating ? "fill-amber-400 text-amber-400" : "text-slate-500"
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            <input
              type="text"
              value={authorName}
              onChange={(e) => setAuthorName(e.target.value)}
              placeholder="Seu nome (opcional)"
              className="w-full rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm text-white"
            />
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Conte sua experiência com o produto (opcional)..."
              className="w-full rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm text-white"
            />
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-emerald-600 px-5 py-2 text-sm font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {submitting ? "Enviando..." : "Publicar Avaliação"}
            </button>
          </form>

          <div className="space-y-3">
            {reviews.length === 0 ? (
              <p className="text-sm text-slate-400">Seja o primeiro a avaliar este produto.</p>
            ) : (
              reviews.map((rev) => (
                <div key={rev.id} className="rounded-xl bg-[#132952]/70 p-4 border border-white/5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold">{rev.author_name}</span>
                    <span className="flex items-center gap-0.5 text-amber-400 text-xs font-bold">
                      {"★".repeat(rev.rating)}
                      <span className="text-slate-500">{"★".repeat(5 - rev.rating)}</span>
                    </span>
                  </div>
                  {rev.comment && <p className="mt-1.5 text-sm text-slate-300">{rev.comment}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
