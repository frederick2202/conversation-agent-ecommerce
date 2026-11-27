"use client";

/**
 * Cabeçalho fixo (sticky) da vitrine.
 *
 * Contém a barra de busca com seletor de categoria (útil no mobile, onde o
 * Sidebar fica oculto), o atalho para o painel admin e o botão do carrinho com
 * contador de itens (`cart.total_items` do StoreContext), que abre o CartDrawer.
 * Filtros são controlados pela página (props `category`/`search`).
 */

import Link from "next/link";
import { Search, ShieldCheck, ShoppingCart } from "lucide-react";
import { useStore } from "@/context/StoreContext";

interface TopHeaderProps {
  /** Categoria selecionada ("Tudo" = sem filtro). */
  category: string;
  onCategoryChange: (cat: string) => void;
  /** Texto da busca; a página aplica debounce antes de consultar a API. */
  search: string;
  onSearchChange: (val: string) => void;
}

/** Opções do seletor de categoria; devem coincidir com as categorias do backend/Sidebar. */
const OPTIONS = ["Tudo", "Notebooks & PCs", "Smartphones", "Áudio & Fones", "Periféricos", "Monitores"];

/** Cabeçalho com busca, filtro de categoria, link admin e botão do carrinho. */
export function TopHeader({ category, onCategoryChange, search, onSearchChange }: TopHeaderProps) {
  const { cart, setCartOpen } = useStore();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 bg-[#0D1E3D]/95 px-4 lg:px-8 backdrop-blur border-b border-white/10">
      <div className="hidden lg:block w-24" />

      {/* Barra de busca: seletor de categoria + campo de texto */}
      <div className="flex w-full max-w-2xl items-center rounded-full bg-white px-3 py-1.5 shadow-md">
        <select
          aria-label="Filtrar categoria"
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="bg-transparent pr-2 text-xs font-semibold text-slate-700 focus:outline-none border-r border-slate-200"
        >
          {OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <Search className="ml-3 h-4 w-4 text-slate-400 shrink-0" />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Buscar eletrônico, marca ou SKU (ex.: LMN-NB-001)..."
          className="w-full bg-transparent px-2.5 py-1 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
        />
      </div>

      {/* Ações: link para o admin e botão que abre o CartDrawer */}
      <div className="flex items-center gap-3">
        <Link
          href="/admin"
          title="Painel Administrativo"
          className="hidden sm:flex items-center gap-1.5 rounded-full bg-[#162F5E] px-3 py-2 text-xs font-semibold text-slate-100 hover:bg-[#1E3D78] transition"
        >
          <ShieldCheck className="h-4 w-4 text-cyan-400" />
          Admin
        </Link>

        <button
          onClick={() => setCartOpen(true)}
          aria-label="Abrir carrinho de compras"
          className="relative flex items-center gap-2 rounded-full bg-[#0099D6] px-4 py-2 text-sm font-bold text-white hover:bg-[#0082B8] transition shadow"
        >
          <ShoppingCart className="h-4 w-4" />
          <span className="hidden sm:inline">Carrinho</span>
          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-[#F04E5E] px-1 text-xs font-extrabold text-white">
            {cart?.total_items ?? 0}
          </span>
        </button>
      </div>
    </header>
  );
}
