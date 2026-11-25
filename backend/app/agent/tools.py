import json
from typing import Optional
import uuid
from langchain_core.tools import tool

from app.core.exceptions import DomainException
from app.services.cart_service import CartService
from app.services.faq_service import FaqService
from app.services.product_service import ProductService


def build_agent_tools(
    session_id: str,
    product_service: ProductService,
    cart_service: CartService,
    faq_service: FaqService,
    collected_ui_actions: list[dict],
):
    @tool
    async def buscar_produto(consulta: str) -> str:
        """Consulta nome, preço, resumo, variações e estoque em tempo real por nome ou SKU do produto."""
        product = await product_service.find_product_for_chat(consulta)
        if not product:
            return json.dumps(
                {"encontrado": False, "mensagem": "Produto não encontrado exatamente. Use sugerir_similares."},
                ensure_ascii=False,
            )

        variants_info = [
            {
                "variant_id": str(v.id),
                "attributes": v.attributes,
                "stock": v.stock_quantity,
                "price": float(v.price_override or product.price),
            }
            for v in product.variants
        ]
        available = [v for v in variants_info if v["stock"] > 0]
        if available:
            collected_ui_actions.append(
                {
                    "type": "SELECT_VARIANT",
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "options": [
                        {
                            "variant_id": v["variant_id"],
                            "label": " • ".join(f"{k}: {val}" for k, val in v["attributes"].items()),
                            "price": v["price"],
                            "prompt": f"Adicionar ao carrinho o produto {product.sku} na variação {v['variant_id']}",
                        }
                        for v in available
                    ],
                }
            )
        return json.dumps(
            {
                "encontrado": True,
                "sku": product.sku,
                "nome": product.name,
                "preco": float(product.price),
                "descricao_resumida": product.short_description,
                "estoque_total": product.total_stock,
                "disponivel": product.total_stock > 0,
                "variacoes_obrigatorias": product.required_variation_keys,
                "variacoes": variants_info,
            },
            ensure_ascii=False,
        )

    @tool
    async def sugerir_similares(termo_busca: str) -> str:
        """Busca produtos similares via busca semântica no pgvector quando o item pedido não existe."""
        similares = await product_service.suggest_similar_products(termo_busca, limit=3)
        return json.dumps(
            [
                {
                    "sku": p.sku,
                    "nome": p.name,
                    "preco": float(p.price),
                    "resumo": p.short_description,
                    "disponivel": p.total_stock > 0,
                }
                for p in similares
            ],
            ensure_ascii=False,
        )

    @tool
    async def adicionar_ao_carrinho(
        sku_ou_nome: str,
        variant_id: Optional[str] = None,
        quantidade: int = 1,
    ) -> str:
        """Adiciona um produto ao carrinho. Exige variant_id se o produto tiver variações obrigatórias."""
        product = await product_service.find_product_for_chat(sku_ou_nome)
        if not product:
            return json.dumps({"sucesso": False, "motivo": "Produto não encontrado. Consulte antes."}, ensure_ascii=False)

        available_variants = [v for v in product.variants if v.stock_quantity >= quantidade]
        if not available_variants:
            return json.dumps({"sucesso": False, "motivo": "Produto sem estoque suficiente no momento."}, ensure_ascii=False)

        chosen_variant = None
        if variant_id:
            try:
                parsed_id = uuid.UUID(variant_id)
                chosen_variant = next((v for v in available_variants if v.id == parsed_id), None)
            except ValueError:
                chosen_variant = None

        if not chosen_variant:
            if len(available_variants) == 1 and not product.required_variation_keys:
                chosen_variant = available_variants[0]
            else:
                collected_ui_actions.append(
                    {
                        "type": "SELECT_VARIANT",
                        "product_name": product.name,
                        "product_sku": product.sku,
                        "options": [
                            {
                                "variant_id": str(v.id),
                                "label": " • ".join(f"{k}: {val}" for k, val in v.attributes.items()),
                                "price": float(v.price_override or product.price),
                                "prompt": f"Adicionar ao carrinho o produto {product.sku} na variação {v.id}",
                            }
                            for v in available_variants
                        ],
                    }
                )
                return json.dumps(
                    {
                        "sucesso": False,
                        "precisa_escolher_variacao": True,
                        "chaves_obrigatorias": product.required_variation_keys,
                        "opcoes": [{"variant_id": str(v.id), "atributos": v.attributes} for v in available_variants],
                    },
                    ensure_ascii=False,
                )

        try:
            summary = await cart_service.add_variant_to_cart(session_id, chosen_variant.id, quantidade)
        except DomainException as exc:
            return json.dumps({"sucesso": False, "motivo": exc.message}, ensure_ascii=False)

        collected_ui_actions.append(
            {
                "type": "CART_UPDATED",
                "checkout_url": "/checkout",
                "total_items": summary.total_items,
                "subtotal": float(summary.subtotal),
                "items": [
                    {
                        "name": i.product_name,
                        "attributes": i.attributes,
                        "quantity": i.quantity,
                        "line_total": float(i.line_total),
                    }
                    for i in summary.items
                ],
            }
        )
        return json.dumps(
            {
                "sucesso": True,
                "resumo_carrinho": {
                    "total_itens": summary.total_items,
                    "subtotal": float(summary.subtotal),
                    "itens": [
                        {"nome": i.product_name, "qtd": i.quantity, "subtotal_item": float(i.line_total)}
                        for i in summary.items
                    ],
                },
            },
            ensure_ascii=False,
        )

    @tool
    async def consultar_faq(pergunta: str) -> str:
        """Consulta políticas atualizadas da Lumen (trocas, frete, garantia, pagamento) via RAG no pgvector."""
        faqs = await faq_service.search_faqs(pergunta, limit=3)
        return json.dumps(
            [{"categoria": f.category, "pergunta": f.question, "resposta": f.answer} for f in faqs],
            ensure_ascii=False,
        )

    return [buscar_produto, sugerir_similares, adicionar_ao_carrinho, consultar_faq]
