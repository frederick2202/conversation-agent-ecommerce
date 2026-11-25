"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Product } from "@/types";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopHeader } from "@/components/layout/TopHeader";
import { HeroBento } from "@/components/catalog/HeroBento";
import { TrustBar } from "@/components/catalog/TrustBar";
import { ProductCard } from "@/components/catalog/ProductCard";
import { ProductDetailModal } from "@/components/catalog/ProductDetailModal";

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [category, setCategory] = useState("Tudo");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listProducts(category, search);
      setProducts(data);
    } finally {
      setLoading(false);
    }
  }, [category, search]);

  useEffect(() => {
    const timer = setTimeout(loadProducts, 220);
    return () => clearTimeout(timer);
  }, [loadProducts]);

  return (
    <div className="min-h-screen bg-[#0B172E]">
      <Sidebar selectedCategory={category} onSelectCategory={setCategory} />

      <div className="lg:pl-60 flex flex-col min-h-screen">
        <TopHeader
          category={category}
          onCategoryChange={setCategory}
          search={search}
          onSearchChange={setSearch}
        />

        <main className="flex-1 pb-20">
          {!search && category === "Tudo" && products.length > 0 && (
            <>
              <HeroBento featured={products} onOpenProduct={setSelectedProduct} />
              <TrustBar />
            </>
          )}

          <section id="catalogo" className="mx-auto max-w-6xl px-4 lg:px-8 mt-10">
            <div className="mb-5 flex items-end justify-between">
              <div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-white">
                  {category === "Tudo" ? "Destaques em Eletrônicos Lumen" : category}
                </h2>
                <p className="text-sm text-slate-400">
                  Estoque atualizado em tempo real e suporte instantâneo via Lumen AI.
                </p>
              </div>
              {category !== "Tudo" && (
                <button
                  onClick={() => setCategory("Tudo")}
                  className="rounded-lg border border-white/25 px-4 py-1.5 text-xs font-semibold text-white hover:bg-white/10"
                >
                  Ver todos
                </button>
              )}
            </div>

            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {[1, 2, 3, 4].map((n) => (
                  <div key={n} className="h-72 animate-pulse rounded-xl bg-[#132952]" />
                ))}
              </div>
            ) : products.length === 0 ? (
              <div className="rounded-2xl bg-[#132952] p-10 text-center text-slate-300">
                Nenhum eletrônico encontrado para essa busca. Experimente perguntar à Lumen AI no chat!
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {products.map((p) => (
                  <ProductCard key={p.id} product={p} onSelect={setSelectedProduct} />
                ))}
              </div>
            )}
          </section>
        </main>
      </div>

      <ProductDetailModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
        onReviewAdded={loadProducts}
      />
    </div>
  );
}
