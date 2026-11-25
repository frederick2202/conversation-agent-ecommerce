export interface ProductVariant {
  id: string;
  variant_sku: string;
  attributes: Record<string, string>;
  stock_quantity: number;
  price_override?: number | null;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  brand: string;
  category: string;
  short_description: string;
  description: string;
  price: number;
  original_price?: number | null;
  discount_percent: number;
  image_url: string;
  specs_tags: string[];
  required_variation_keys: string[];
  variants: ProductVariant[];
  total_stock: number;
  average_rating: number;
  review_count: number;
}

export interface Review {
  id: string;
  product_id: string;
  author_name: string;
  rating: number;
  comment?: string | null;
  created_at: string;
}

export interface CartItem {
  item_id: string;
  product_id: string;
  variant_id: string;
  sku: string;
  product_name: string;
  image_url: string;
  attributes: Record<string, string>;
  unit_price: number;
  quantity: number;
  line_total: number;
}

export interface CartSummary {
  session_id: string;
  items: CartItem[];
  total_items: number;
  subtotal: number;
}

export interface Faq {
  id: string;
  category: string;
  question: string;
  answer: string;
  updated_at: string;
}

export interface ChatUiAction {
  type: "SELECT_VARIANT" | "CART_UPDATED";
  product_name?: string;
  product_sku?: string;
  options?: Array<{ variant_id: string; label: string; price: number; prompt: string }>;
  checkout_url?: string;
  total_items?: number;
  subtotal?: number;
  items?: Array<{ name: string; attributes: Record<string, string>; quantity: number; line_total: number }>;
}

export interface ChatMessageItem {
  role: "user" | "assistant";
  content: string;
  ui_actions?: ChatUiAction[];
}
