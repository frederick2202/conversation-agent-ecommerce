"use client";

/**
 * Banner principal ("bento grid") exibido no topo da vitrine quando não há
 * filtros ativos (ver app/page.tsx).
 *
 * Layout: carrossel grande com os 3 primeiros produtos recebidos (setas
 * anterior/próximo, navegação circular) + coluna lateral com os produtos de
 * índice 1 e 2 como cards menores. Clicar em qualquer destaque abre o
 * ProductDetailModal através de `onOpenProduct`.
 */

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Product } from "@/types";
import { formatBRL } from "@/lib/api";

interface HeroBentoProps {
  /** Lista de produtos da vitrine; apenas os 3 primeiros são usados. */
  featured: Product[];
  /** Callback para abrir o modal de detalhes do produto clicado. */
  onOpenProduct: (product: Product) => void;
}

/** Banner de destaques com carrossel + cards laterais. */
export function HeroBento({ featured, onOpenProduct }: HeroBentoProps) {
  /** Índice do slide atual do carrossel (0 a slides.length - 1). */
  const [slide, setSlide] = useState(0);
  const slides = featured.slice(0, 3);
  const current = slides[slide];
  const sideCards = featured.slice(1, 3);

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-[#FF2A85] via-[#6D28D9] to-[#0B172E] pt-8 pb-10 px-4 lg:px-8">
      {/* Chamada promocional com âncora para o catálogo */}
      <div className="mx-auto max-w-6xl text-center mb-8">
        <span className="inline-block rounded-md border border-white/60 bg-white/10 px-4 py-1 text-xs font-extrabold tracking-widest text-white uppercase backdrop-blur">
          LUMEN TECH WEEK
        </span>
        <h1 className="mt-3 text-2xl sm:text-4xl font-black tracking-tight text-white drop-shadow">
          PERFORMANCE REAL COM ATENDIMENTO POR IA!
        </h1>
        <a
          href="#catalogo"
          className="mt-4 inline-flex items-center justify-center rounded-lg bg-white px-8 py-2.5 text-sm font-bold text-[#0F2B5B] shadow-lg hover:bg-slate-100 transition"
        >
          Confira as ofertas
        </a>
      </div>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Carrossel principal (ocupa 2 colunas no desktop) */}
        <div className="relative lg:col-span-2 overflow-hidden rounded-2xl bg-[#132952] min-h-[300px] shadow-2xl border border-white/15">
          {current && (
            <>
              <img
                src={current.image_url}
                alt={current.name}
                className="h-full w-full object-cover opacity-55"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0B172E] via-[#0B172E]/50 to-transparent p-6 flex flex-col justify-end">
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="rounded bg-[#F04E5E] px-2.5 py-1 text-xs font-bold text-white">
                    -{current.discount_percent}% OFF
                  </span>
                  <span className="rounded bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur">
                    10x SEM JUROS • SKU {current.sku}
                  </span>
                </div>
                <h2 className="text-2xl font-extrabold text-white">{current.name}</h2>
                <p className="mt-1 text-sm text-slate-200 max-w-xl">{current.short_description}</p>
                <div className="mt-4 flex items-center gap-4">
                  <button
                    onClick={() => onOpenProduct(current)}
                    className="rounded-lg bg-white px-6 py-2.5 text-sm font-bold text-[#0F2B5B] hover:bg-slate-100 transition"
                  >
                    Ver detalhes • {formatBRL(current.price)}
                  </button>
                </div>
              </div>

              {/* Setas de navegação; o módulo (%) faz o carrossel dar a volta */}
              {slides.length > 1 && (
                <>
                  <button
                    aria-label="Slide anterior"
                    onClick={() => setSlide((s) => (s - 1 + slides.length) % slides.length)}
                    className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-white p-2 text-[#0F2B5B] shadow-md hover:scale-105 transition"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button
                    aria-label="Próximo slide"
                    onClick={() => setSlide((s) => (s + 1) % slides.length)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-white p-2 text-[#0F2B5B] shadow-md hover:scale-105 transition"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </>
              )}
            </>
          )}
        </div>

        {/* Coluna lateral com até 2 destaques menores */}
        <div className="flex flex-col gap-4">
          {sideCards.map((prod) => (
            <div
              key={prod.id}
              onClick={() => onOpenProduct(prod)}
              className="group relative flex-1 cursor-pointer overflow-hidden rounded-2xl bg-[#132952] border border-white/15 p-5 flex flex-col justify-end min-h-[142px] shadow-xl"
            >
              <img
                src={prod.image_url}
                alt={prod.name}
                className="absolute inset-0 h-full w-full object-cover opacity-40 group-hover:scale-105 transition duration-300"
              />
              <div className="relative z-10">
                <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-300">
                  {prod.brand} • {prod.category}
                </span>
                <h3 className="text-base font-extrabold text-white line-clamp-1">{prod.name}</h3>
                <div className="mt-2 flex items-center gap-2">
                  <span className="rounded bg-[#F04E5E] px-2 py-0.5 text-xs font-bold text-white">
                    -{prod.discount_percent}%
                  </span>
                  <span className="text-sm font-bold text-white">{formatBRL(prod.price)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
