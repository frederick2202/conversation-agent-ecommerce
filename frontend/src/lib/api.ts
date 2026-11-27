/**
 * Cliente HTTP da API REST do backend Lumen (FastAPI).
 *
 * Centraliza todas as chamadas `fetch` do frontend (exceto o streaming do chat,
 * feito diretamente no LumenChatWidget por precisar ler o corpo como SSE).
 * Também exporta o helper `formatBRL` usado em toda a UI para exibir preços.
 */
import { CartSummary, ChatMessageItem, Faq, Product, Review } from "@/types";

/**
 * URL base do backend. Configurável via `NEXT_PUBLIC_API_URL` (ver .env.local.example);
 * por ser `NEXT_PUBLIC_*`, o valor é embutido no bundle do navegador em tempo de build.
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Wrapper genérico sobre `fetch` que:
 * - prefixa o caminho com `API_URL` e envia JSON por padrão;
 * - em respostas de erro, lê o corpo no formato padrão do backend
 *   (`{ error: { code, message } }`) e lança um `Error` com a mensagem amigável;
 * - em `204 No Content` (ex.: DELETE) retorna `undefined` sem tentar ler JSON.
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || "Erro ao comunicar com o servidor.");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

/**
 * Mapa de funções tipadas para cada endpoint REST (`/api/v1/...`).
 * Os endpoints de carrinho e chat são indexados pelo `sessionId` anônimo
 * gerado no StoreContext — não há autenticação de usuário.
 */
export const api = {
  // ---------- Produtos ----------
  /** Lista produtos; "Tudo" significa sem filtro de categoria. `search` busca por nome, SKU, marca ou descrição. */
  listProducts: (category?: string, search?: string) => {
    const params = new URLSearchParams();
    if (category && category !== "Tudo") params.set("category", category);
    if (search) params.set("search", search);
    return request<Product[]>(`/api/v1/products?${params.toString()}`);
  },
  /** Cria produto (painel admin). O backend também o indexa para busca semântica do agente. */
  createProduct: (data: Record<string, unknown>) =>
    request<Product>("/api/v1/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (id: string, data: Record<string, unknown>) =>
    request<Product>(`/api/v1/products/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteProduct: (id: string) => request<void>(`/api/v1/products/${id}`, { method: "DELETE" }),

  // ---------- Avaliações ----------
  listReviews: (productId: string) => request<Review[]>(`/api/v1/products/${productId}/reviews`),
  createReview: (productId: string, data: { author_name: string; rating: number; comment?: string }) =>
    request<Review>(`/api/v1/products/${productId}/reviews`, { method: "POST", body: JSON.stringify(data) }),

  // ---------- Carrinho (por sessão) ----------
  // Todas as operações retornam o CartSummary atualizado; o backend cria o carrinho sob demanda.
  getCart: (sessionId: string) => request<CartSummary>(`/api/v1/cart/${sessionId}`),
  /** Adiciona uma variação (não um produto) ao carrinho; o backend valida o estoque. */
  addCartItem: (sessionId: string, variant_id: string, quantity = 1) =>
    request<CartSummary>(`/api/v1/cart/${sessionId}/items`, {
      method: "POST",
      body: JSON.stringify({ variant_id, quantity }),
    }),
  /** Define a nova quantidade de uma linha; `quantity <= 0` remove o item. */
  updateCartItem: (sessionId: string, itemId: string, quantity: number) =>
    request<CartSummary>(`/api/v1/cart/${sessionId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),
  /**
   * Finaliza o pedido (checkout simulado): o backend gera um código de pedido
   * (`LMN-XXXXXXXX`), esvazia o carrinho e retorna o resumo. Não há gateway de pagamento real.
   */
  checkout: (sessionId: string) =>
    request<{ order_code: string; total_paid: number; items_count: number; message: string }>(
      `/api/v1/cart/${sessionId}/checkout`,
      { method: "POST" }
    ),

  // ---------- FAQs (base de conhecimento do agente) ----------
  listFaqs: () => request<Faq[]>("/api/v1/faqs"),
  createFaq: (data: { category: string; question: string; answer: string }) =>
    request<Faq>("/api/v1/faqs", { method: "POST", body: JSON.stringify(data) }),
  updateFaq: (id: string, data: { category?: string; question?: string; answer?: string }) =>
    request<Faq>(`/api/v1/faqs/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteFaq: (id: string) => request<void>(`/api/v1/faqs/${id}`, { method: "DELETE" }),

  // ---------- Chat ----------
  // O envio de mensagens (POST /api/v1/chat/stream, resposta em SSE `text/event-stream`
  // com eventos token / ui_actions / done) é feito diretamente no LumenChatWidget.
  /** Histórico persistido da conversa desta sessão (inclui `ui_actions` das respostas). */
  getChatHistory: (sessionId: string) => request<ChatMessageItem[]>(`/api/v1/chat/sessions/${sessionId}`),
  /** Apaga todo o histórico de chat da sessão (botão "Reiniciar conversa"). */
  clearChatHistory: (sessionId: string) =>
    request<void>(`/api/v1/chat/sessions/${sessionId}`, { method: "DELETE" }),
};

/** Formata um número como moeda brasileira (ex.: 1234.5 → "R$ 1.234,50"). */
export const formatBRL = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
