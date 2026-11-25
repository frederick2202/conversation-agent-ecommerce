"use client";

import { Star } from "lucide-react";
import { Product } from "@/types";
import { formatBRL } from "@/lib/api";

interface ProductCardProps {
  product: Product;
  onSelect: (product: Product) => void;
}

export function ProductCard({ product, onSelect }: ProductCardProps) {
  return (
    <article
      onClick={() => onSelect(product)}
      className="group cursor-pointer overflow-hidden rounded-xl bg-[#132952] border border-white/10 hover:border-cyan-400/60 transition shadow-lg flex flex-col"
    >
      <div className="flex items-center justify-between bg-[#0F2145] px-3 py-1.5 text-[11px] font-semibold text-slate-300">
        <span>{product.brand}</span>
        <span className="font-mono text-cyan-300">{product.sku}</span>
      </div>

      <div className="aspect-[16/10] w-full overflow-hidden bg-[#0B172E]">
        <img
          src={product.image_url}
          alt={product.name}
          className="h-full w-full object-cover group-hover:scale-105 transition duration-300"
        />
      </div>

      <div className="flex flex-1 flex-col justify-between p-4">
        <div>
          <h3 className="text-sm font-bold text-white line-clamp-2 group-hover:text-cyan-300 transition">
            {product.name}
          </h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {product.specs_tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="rounded bg-[#0B172E] px-2 py-0.5 text-[10px] font-medium text-slate-300"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {product.discount_percent > 0 && (
              <span className="rounded bg-[#F04E5E] px-2 py-0.5 text-xs font-extrabold text-white">
                -{product.discount_percent}%
              </span>
            )}
            <span className="text-base font-extrabold text-white">{formatBRL(product.price)}</span>
          </div>

          <span className="flex items-center gap-1 text-xs text-amber-400 font-semibold">
            <Star className="h-3.5 w-3.5 fill-amber-400" />
            {product.review_count > 0 ? product.average_rating.toFixed(1) : "Novo"}
          </span>
        </div>
      </div>
    </article>
  );
}
