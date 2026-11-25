"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Package, PlusCircle, Trash2 } from "lucide-react";
import { api, formatBRL } from "@/lib/api";
import { useStore } from "@/context/StoreContext";
import { Faq, Product } from "@/types";

export default function AdminPage() {
  const { showToast } = useStore();
  const [tab, setTab] = useState<"faqs" | "products">("faqs");

  // Estado FAQs
  const [faqs, setFaqs] = useState<Faq[]>([]);
  const [faqCategory, setFaqCategory] = useState("Frete e Entrega");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  // Estado Produtos
  const [products, setProducts] = useState<Product[]>([]);
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [prodCategory, setProdCategory] = useState("Periféricos");
  const [price, setPrice] = useState("");
  const [shortDesc, setShortDesc] = useState("");
  const [imageUrl, setImageUrl] = useState("https://images.unsplash.com/photo-1518770660439-4636190af475?w=800");
  const [stock, setStock] = useState("10");

  // Confirmação irreversível
  const [confirmDelete, setConfirmDelete] = useState<{ type: "faq" | "product"; id: string; label: string } | null>(null);

  const loadAll = async () => {
    const [f, p] = await Promise.all([api.listFaqs(), api.listProducts()]);
    setFaqs(f);
    setProducts(p);
  };

  useEffect(() => {
    loadAll().catch(() => {});
  }, []);

  const handleSaveFaq = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    try {
      await api.createFaq({ category: faqCategory, question, answer });
      setQuestion("");
      setAnswer("");
      await loadAll();
      showToast("FAQ salva e vetorizada no pgvector! Agente atualizado.", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao salvar FAQ.", "error");
    }
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sku.trim() || !name.trim() || !price) return;
    try {
      await api.createProduct({
        sku: sku.trim().toUpperCase(),
        name: name.trim(),
        brand: brand.trim() || "Lumen",
        category: prodCategory,
        short_description: shortDesc.trim() || name.trim(),
        description: shortDesc.trim() || name.trim(),
        price: Number(price),
        discount_percent: 0,
        image_url: imageUrl.trim(),
        specs_tags: [prodCategory, "Garantia 12m"],
        required_variation_keys: ["cor"],
        variants: [
          {
            variant_sku: `${sku.trim().toUpperCase()}-STD`,
            attributes: { cor: "Padrão" },
            stock_quantity: Number(stock) || 10,
          },
        ],
      });
      setSku("");
      setName("");
      setBrand("");
      setPrice("");
      setShortDesc("");
      await loadAll();
      showToast("Produto criado e indexado no pgvector!", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao cadastrar produto.", "error");
    }
  };

  const executeDelete = async () => {
    if (!confirmDelete) return;
    try {
      if (confirmDelete.type === "faq") {
        await api.deleteFaq(confirmDelete.id);
      } else {
        await api.deleteProduct(confirmDelete.id);
      }
      setConfirmDelete(null);
      await loadAll();
      showToast("Registro removido com sucesso.", "info");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Erro ao excluir.", "error");
    }
  };

  return (
    <div className="min-h-screen bg-[#0B172E] px-4 py-10">
      <div className="mx-auto max-w-5xl space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:underline">
              <ArrowLeft className="h-4 w-4" /> Voltar à Loja
            </Link>
            <h1 className="mt-2 text-2xl font-extrabold">Painel Admin • Sincronização RAG (RF04)</h1>
          </div>

          <div className="flex rounded-xl bg-[#132952] p-1 border border-white/10">
            <button
              onClick={() => setTab("faqs")}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition ${
                tab === "faqs" ? "bg-[#0099D6] text-white" : "text-slate-300 hover:text-white"
              }`}
            >
              <BookOpen className="h-4 w-4" /> FAQs ({faqs.length})
            </button>
            <button
              onClick={() => setTab("products")}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition ${
                tab === "products" ? "bg-[#0099D6] text-white" : "text-slate-300 hover:text-white"
              }`}
            >
              <Package className="h-4 w-4" /> Produtos ({products.length})
            </button>
          </div>
        </div>

        {tab === "faqs" ? (
          <>
            <form onSubmit={handleSaveFaq} className="rounded-2xl bg-[#132952] border border-white/10 p-6 space-y-4">
              <h2 className="text-base font-bold flex items-center gap-2">
                <PlusCircle className="h-5 w-5 text-cyan-400" />
                Cadastrar Nova FAQ (Reindexação Automática)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input
                  value={faqCategory}
                  onChange={(e) => setFaqCategory(e.target.value)}
                  placeholder="Categoria (ex.: Trocas)"
                  className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm"
                />
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Pergunta frequente..."
                  required
                  className="md:col-span-2 rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm"
                />
              </div>
              <textarea
                rows={3}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Resposta oficial que a Lumen AI utilizará..."
                required
                className="w-full rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm"
              />
              <button
                type="submit"
                className="rounded-lg bg-[#0099D6] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#0082B8]"
              >
                Salvar e Sincronizar com IA
              </button>
            </form>

            <div className="space-y-3">
              {faqs.map((faq) => (
                <div key={faq.id} className="flex items-start justify-between gap-4 rounded-xl bg-[#132952] p-4 border border-white/10">
                  <div>
                    <span className="rounded bg-cyan-500/20 px-2 py-0.5 text-[11px] font-bold text-cyan-300">
                      {faq.category}
                    </span>
                    <h3 className="mt-1 font-bold text-sm">{faq.question}</h3>
                    <p className="mt-1 text-xs text-slate-300">{faq.answer}</p>
                  </div>
                  <button
                    onClick={() => setConfirmDelete({ type: "faq", id: faq.id, label: faq.question })}
                    aria-label="Excluir FAQ"
                    className="rounded-lg p-2 text-rose-400 hover:bg-rose-500/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <form onSubmit={handleSaveProduct} className="rounded-2xl bg-[#132952] border border-white/10 p-6 space-y-4">
              <h2 className="text-base font-bold flex items-center gap-2">
                <PlusCircle className="h-5 w-5 text-cyan-400" />
                Cadastrar Novo Eletrônico (Reindexação Automática)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input value={sku} onChange={(e) => setSku(e.target.value)} placeholder="SKU (ex.: LMN-PR-010)" required className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nome do produto" required className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
                <input value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="Marca" className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
                <select value={prodCategory} onChange={(e) => setProdCategory(e.target.value)} className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm">
                  <option>Notebooks & PCs</option>
                  <option>Smartphones</option>
                  <option>Áudio & Fones</option>
                  <option>Periféricos</option>
                  <option>Monitores</option>
                </select>
                <input type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="Preço (R$)" required className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
                <input type="number" value={stock} onChange={(e) => setStock(e.target.value)} placeholder="Estoque inicial" className="rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
              </div>
              <input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} placeholder="URL da imagem" className="w-full rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
              <textarea rows={2} value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} placeholder="Descrição resumida e especificações..." required className="w-full rounded-lg bg-[#0B172E] border border-white/15 px-3 py-2 text-sm" />
              <button type="submit" className="rounded-lg bg-[#0099D6] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#0082B8]">
                Cadastrar e Vetorizar Produto
              </button>
            </form>

            <div className="space-y-3">
              {products.map((prod) => (
                <div key={prod.id} className="flex items-center justify-between gap-4 rounded-xl bg-[#132952] p-4 border border-white/10">
                  <div className="flex items-center gap-3">
                    <img src={prod.image_url} alt={prod.name} className="h-12 w-16 rounded-lg object-cover" />
                    <div>
                      <span className="text-[11px] font-mono text-cyan-300">{prod.sku} • Estoque: {prod.total_stock}</span>
                      <h3 className="font-bold text-sm">{prod.name}</h3>
                      <p className="text-xs text-slate-300">{formatBRL(prod.price)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setConfirmDelete({ type: "product", id: prod.id, label: prod.name })}
                    aria-label="Excluir produto"
                    className="rounded-lg p-2 text-rose-400 hover:bg-rose-500/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-w-sm rounded-2xl bg-[#0F2145] border border-white/15 p-6 space-y-4">
            <h2 className="text-lg font-bold">Confirmar exclusão?</h2>
            <p className="text-sm text-slate-300">
              Tem certeza que deseja remover &ldquo;{confirmDelete.label}&rdquo;? Esta ação é irreversível.
            </p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setConfirmDelete(null)} className="rounded-lg bg-white/10 px-4 py-2 text-sm">
                Cancelar
              </button>
              <button onClick={executeDelete} className="rounded-lg bg-[#F04E5E] px-4 py-2 text-sm font-bold">
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
