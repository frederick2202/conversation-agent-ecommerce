/**
 * Tipos de domínio compartilhados pelo frontend.
 *
 * Estas interfaces espelham os contratos JSON retornados pela API FastAPI
 * (schemas Pydantic em backend/app/schemas). Se o backend mudar um campo,
 * atualize aqui também para manter a tipagem consistente.
 * Observação: IDs (UUID) e valores monetários (Decimal) chegam serializados
 * como string/number no JSON e são tratados aqui como `string`/`number`.
 */

/**
 * Variação vendável de um produto (ex.: cor + armazenamento).
 * É a variação — e não o produto — que possui estoque e que entra no carrinho.
 */
export interface ProductVariant {
  /** UUID da variação; é o valor enviado como `variant_id` ao adicionar ao carrinho. */
  id: string;
  variant_sku: string;
  /** Pares chave/valor que descrevem a variação, ex.: `{ cor: "Preto", armazenamento: "1TB" }`. */
  attributes: Record<string, string>;
  /** Estoque disponível; quando 0 a variação aparece desabilitada na UI. */
  stock_quantity: number;
  /** Preço específico da variação; quando ausente/nulo vale o `price` do produto. */
  price_override?: number | null;
}

/** Produto do catálogo, como retornado por `GET /api/v1/products`. */
export interface Product {
  id: string;
  /** Código legível do produto (ex.: "LMN-NB-001"), usado também pelo agente de IA. */
  sku: string;
  name: string;
  brand: string;
  /** Categoria textual; deve bater com as opções do Sidebar/TopHeader (ex.: "Monitores"). */
  category: string;
  short_description: string;
  description: string;
  /** Preço de venda atual (exibido na vitrine); `original_price` é o preço "de". */
  price: number;
  original_price?: number | null;
  discount_percent: number;
  image_url: string;
  /** Etiquetas curtas de especificação exibidas no card (as 3 primeiras). */
  specs_tags: string[];
  /** Chaves de atributo que o cliente precisa escolher antes de comprar (ex.: ["cor"]). */
  required_variation_keys: string[];
  variants: ProductVariant[];
  /** Soma do estoque de todas as variações (calculado no backend). */
  total_stock: number;
  /** Média das avaliações (0 quando não há avaliações). */
  average_rating: number;
  review_count: number;
}

/** Avaliação de um produto feita por um cliente (nota de 1 a 5). */
export interface Review {
  id: string;
  product_id: string;
  author_name: string;
  rating: number;
  comment?: string | null;
  created_at: string;
}

/** Linha do carrinho: uma variação específica com sua quantidade. */
export interface CartItem {
  /** ID da linha do carrinho (usado em PATCH para alterar quantidade/remover). */
  item_id: string;
  product_id: string;
  variant_id: string;
  sku: string;
  product_name: string;
  image_url: string;
  attributes: Record<string, string>;
  /** Preço unitário efetivo (price_override da variação ou preço do produto). */
  unit_price: number;
  quantity: number;
  /** `unit_price * quantity`, calculado no backend. */
  line_total: number;
}

/**
 * Resumo completo do carrinho de uma sessão. Todos os endpoints de carrinho
 * (GET, adicionar, atualizar) retornam este objeto já recalculado, então o
 * frontend apenas substitui o estado local pela resposta.
 */
export interface CartSummary {
  /** Identificador anônimo da sessão do navegador (ver StoreContext). */
  session_id: string;
  items: CartItem[];
  /** Soma das quantidades de todos os itens. */
  total_items: number;
  subtotal: number;
}

/** Pergunta frequente cadastrada no painel admin e usada pelo agente via RAG. */
export interface Faq {
  id: string;
  category: string;
  question: string;
  answer: string;
  updated_at: string;
}

/**
 * Ação de interface emitida pelo agente de IA junto com a resposta do chat.
 * As ferramentas (tools) do agente LangGraph geram essas ações no backend, que
 * as envia no evento SSE `ui_actions` (`data: {"actions": ChatUiAction[]}`) do
 * `POST /api/v1/chat/stream` e também as persiste no histórico. O
 * LumenChatWidget as renderiza como componentes interativos abaixo da mensagem.
 *
 * - `SELECT_VARIANT`: o produto exige escolha de variação; usa `product_name`,
 *   `product_sku` e `options` (renderizadas como botões).
 * - `CART_UPDATED`: o agente adicionou algo ao carrinho; usa `checkout_url`,
 *   `total_items`, `subtotal` e `items` (renderizado como card com link de checkout).
 */
export interface ChatUiAction {
  type: "SELECT_VARIANT" | "CART_UPDATED";
  product_name?: string;
  product_sku?: string;
  /**
   * Opções de variação (apenas em `SELECT_VARIANT`). `prompt` é o texto que
   * será enviado de volta ao chat quando o usuário clicar no botão, pedindo
   * ao agente para adicionar aquela variação ao carrinho.
   */
  options?: Array<{ variant_id: string; label: string; price: number; prompt: string }>;
  /** Rota de checkout sugerida pelo agente (ex.: "/checkout"). */
  checkout_url?: string;
  total_items?: number;
  subtotal?: number;
  /** Snapshot resumido dos itens do carrinho após a atualização. */
  items?: Array<{ name: string; attributes: Record<string, string>; quantity: number; line_total: number }>;
}

/**
 * Mensagem do histórico do chat. É o formato retornado por
 * `GET /api/v1/chat/sessions/{session_id}` (o histórico é apagado com `DELETE`
 * no mesmo path) e também o estado local do widget durante o streaming.
 */
export interface ChatMessageItem {
  role: "user" | "assistant";
  content: string;
  /** Ações de UI associadas à resposta do assistente (persistidas no histórico). */
  ui_actions?: ChatUiAction[];
}
