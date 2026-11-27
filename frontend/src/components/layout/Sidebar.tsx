"use client";

/**
 * Menu lateral fixo da vitrine (visível apenas em telas grandes, `lg:flex`).
 *
 * Exibe o logo, atalhos ("Lumen Black", "Catálogo", "Ofertas da Semana" — todos
 * hoje apenas resetam o filtro para "Tudo"), a lista de categorias e links para
 * o painel admin e a central de ajuda. O estado da categoria fica na página
 * (app/page.tsx); este componente só o exibe e notifica mudanças.
 */

import Link from "next/link";
import {
  Cpu,
  Headphones,
  Keyboard,
  LayoutGrid,
  LifeBuoy,
  Menu,
  Monitor,
  Settings,
  Smartphone,
  Sparkles,
  Tag,
} from "lucide-react";

interface SidebarProps {
  /** Categoria atualmente ativa (para destacar o item). */
  selectedCategory: string;
  /** Callback para alterar a categoria; "Tudo" remove o filtro. */
  onSelectCategory: (cat: string) => void;
}

/**
 * Categorias do catálogo. O `label` é enviado como filtro `category` para a API,
 * portanto deve ser idêntico à categoria cadastrada no backend (e às opções do
 * TopHeader e do formulário do painel admin).
 */
const CATEGORIES = [
  { label: "Notebooks & PCs", icon: Cpu },
  { label: "Smartphones", icon: Smartphone },
  { label: "Áudio & Fones", icon: Headphones },
  { label: "Periféricos", icon: Keyboard },
  { label: "Monitores", icon: Monitor },
];

/** Barra lateral de navegação por categorias (desktop). */
export function Sidebar({ selectedCategory, onSelectCategory }: SidebarProps) {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col bg-[#0F2B5B] text-slate-100 border-r border-white/10 lg:flex">
      {/* Logo (volta para a home e limpa o filtro) */}
      <div className="flex h-16 items-center gap-3 px-4 border-b border-white/10">
        <Menu className="h-5 w-5 text-slate-300" />
        <Link
          href="/"
          onClick={() => onSelectCategory("Tudo")}
          className="flex items-center gap-2 rounded-md border border-cyan-400/50 bg-[#0B1F44] px-3 py-1 text-sm font-extrabold tracking-wider text-white"
        >
          <Sparkles className="h-4 w-4 text-cyan-400" />
          LUMEN TECH
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5 text-sm">
        {/* Atalhos promocionais (todos aplicam o filtro "Tudo") */}
        <div className="space-y-1">
          <button
            onClick={() => onSelectCategory("Tudo")}
            className={`flex w-full items-center justify-between rounded-lg px-3 py-2 font-medium transition ${
              selectedCategory === "Tudo" ? "bg-white/15 text-white" : "text-slate-200 hover:bg-white/10"
            }`}
          >
            <span className="flex items-center gap-2.5">
              <Sparkles className="h-4 w-4 text-cyan-300" />
              Lumen Black
            </span>
            <span className="rounded bg-[#F04E5E] px-1.5 py-0.5 text-[10px] font-bold uppercase text-white">
              Novo
            </span>
          </button>

          <button
            onClick={() => onSelectCategory("Tudo")}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-slate-200 hover:bg-white/10"
          >
            <LayoutGrid className="h-4 w-4 text-slate-300" />
            Catálogo
          </button>

          <button
            onClick={() => onSelectCategory("Tudo")}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-slate-200 hover:bg-white/10"
          >
            <Tag className="h-4 w-4 text-slate-300" />
            Ofertas da Semana
          </button>
        </div>

        <hr className="border-white/10" />

        {/* Filtros por categoria */}
        <div className="space-y-1">
          {CATEGORIES.map(({ label, icon: Icon }) => (
            <button
              key={label}
              onClick={() => onSelectCategory(label)}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2 transition ${
                selectedCategory === label
                  ? "bg-[#0099D6]/25 text-white font-semibold"
                  : "text-slate-200 hover:bg-white/10"
              }`}
            >
              <span className="flex items-center gap-2.5">
                <Icon className="h-4 w-4 text-slate-300" />
                {label}
              </span>
              <span className="text-xs text-slate-400">›</span>
            </button>
          ))}
        </div>

        <hr className="border-white/10" />

        {/* Links institucionais: painel admin e âncora para o catálogo */}
        <div className="space-y-1">
          <Link
            href="/admin"
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-slate-200 hover:bg-white/10"
          >
            <Settings className="h-4 w-4 text-cyan-300" />
            Painel Admin (RAG)
          </Link>
          <a
            href="#catalogo"
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-slate-200 hover:bg-white/10"
          >
            <LifeBuoy className="h-4 w-4 text-slate-300" />
            Central de Ajuda
          </a>
        </div>
      </nav>
    </aside>
  );
}
