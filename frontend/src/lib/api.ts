import { CartSummary, ChatMessageItem, Faq, Product, Review } from "@/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

export const api = {
  listProducts: (category?: string, search?: string) => {
    const params = new URLSearchParams();
    if (category && category !== "Tudo") params.set("category", category);
    if (search) params.set("search", search);
    return request<Product[]>(`/api/v1/products?${params.toString()}`);
  },
  createProduct: (data: Record<string, unknown>) =>
    request<Product>("/api/v1/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (id: string, data: Record<string, unknown>) =>
    request<Product>(`/api/v1/products/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteProduct: (id: string) => request<void>(`/api/v1/products/${id}`, { method: "DELETE" }),

  listReviews: (productId: string) => request<Review[]>(`/api/v1/products/${productId}/reviews`),
  createReview: (productId: string, data: { author_name: string; rating: number; comment?: string }) =>
    request<Review>(`/api/v1/products/${productId}/reviews`, { method: "POST", body: JSON.stringify(data) }),

  getCart: (sessionId: string) => request<CartSummary>(`/api/v1/cart/${sessionId}`),
  addCartItem: (sessionId: string, variant_id: string, quantity = 1) =>
    request<CartSummary>(`/api/v1/cart/${sessionId}/items`, {
      method: "POST",
      body: JSON.stringify({ variant_id, quantity }),
    }),
  updateCartItem: (sessionId: string, itemId: string, quantity: number) =>
    request<CartSummary>(`/api/v1/cart/${sessionId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),
  checkout: (sessionId: string) =>
    request<{ order_code: string; total_paid: number; items_count: number; message: string }>(
      `/api/v1/cart/${sessionId}/checkout`,
      { method: "POST" }
    ),

  listFaqs: () => request<Faq[]>("/api/v1/faqs"),
  createFaq: (data: { category: string; question: string; answer: string }) =>
    request<Faq>("/api/v1/faqs", { method: "POST", body: JSON.stringify(data) }),
  updateFaq: (id: string, data: { category?: string; question?: string; answer?: string }) =>
    request<Faq>(`/api/v1/faqs/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteFaq: (id: string) => request<void>(`/api/v1/faqs/${id}`, { method: "DELETE" }),

  getChatHistory: (sessionId: string) => request<ChatMessageItem[]>(`/api/v1/chat/sessions/${sessionId}`),
  clearChatHistory: (sessionId: string) =>
    request<void>(`/api/v1/chat/sessions/${sessionId}`, { method: "DELETE" }),
};

export const formatBRL = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
