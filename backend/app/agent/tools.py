"""
Ferramentas (tools) que o agente de IA pode chamar durante a conversa.

Como funciona:
- Cada função decorada com `@tool` vira uma ferramenta do LangChain. O NOME da função,
  a DOCSTRING e os PARÂMETROS são enviados ao LLM, que os usa para decidir quando e como
  chamá-la — por isso as docstrings das ferramentas são instruções para o modelo e devem
  ser mantidas curtas e precisas.
- As ferramentas retornam strings JSON (lidas pelo LLM para compor a resposta).
- Além disso, algumas ferramentas anexam "ações de UI" em `collected_ui_actions`. Essa lista
  é enviada ao frontend no fim da resposta (evento SSE `ui_actions`) e vira componentes
  interativos no chat:
    * SELECT_VARIANT -> botões para o cliente escolher a variação; cada botão reenvia ao chat
                        o texto do campo `prompt` (ex.: "Adicionar ao carrinho o produto X na variação Y").
    * CART_UPDATED   -> resumo do carrinho atualizado + link para o checkout.
"""

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
    """Cria as ferramentas do agente vinculadas à sessão atual.

    As ferramentas são closures: capturam `session_id`, os services e a lista
    `collected_ui_actions` (mutada in-place) sem expor esses detalhes ao LLM.

    Args:
        session_id: identificador da sessão do cliente (mesmo usado no carrinho).
        product_service / cart_service / faq_service: services de domínio já instanciados.
        collected_ui_actions: lista onde as ferramentas acumulam ações de UI para o frontend.
    """

    @tool
    async def buscar_produto(consulta: str) -> str:
        """Consulta nome, preço, resumo, variações e estoque em tempo real por nome ou SKU do produto."""
        product = await product_service.find_product_for_chat(consulta)
        if not product:
            # Orienta o LLM a tentar a busca semântica em seguida.
            return json.dumps(
                {"encontrado": False, "mensagem": "Produto não encontrado exatamente. Use sugerir_similares."},
                ensure_ascii=False,
            )

        variants_info = [
            {
                "variant_id": str(v.id),
                "attributes": v.attributes,
                "stock": v.stock_quantity,
                # Preço efetivo: o da variação, se houver override; senão o preço base do produto.
                "price": float(v.price_override or product.price),
            }
            for v in product.variants
        ]
        available = [v for v in variants_info if v["stock"] > 0]
        if available:
            # Já oferece ao cliente os botões de variação disponíveis (somente com estoque).
            collected_ui_actions.append(
                {
                    "type": "SELECT_VARIANT",
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "options": [
                        {
                            "variant_id": v["variant_id"],
                            # Texto do botão, ex.: "cor: Preto • armazenamento: 512GB".
                            "label": " • ".join(f"{k}: {val}" for k, val in v["attributes"].items()),
                            "price": v["price"],
                            # Mensagem enviada ao agente quando o cliente clica no botão.
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

        # Considera apenas variações com estoque suficiente para a quantidade pedida.
        available_variants = [v for v in product.variants if v.stock_quantity >= quantidade]
        if not available_variants:
            return json.dumps({"sucesso": False, "motivo": "Produto sem estoque suficiente no momento."}, ensure_ascii=False)

        # 1) Tenta usar a variação informada pelo LLM (só é aceita se estiver entre as disponíveis).
        chosen_variant = None
        if variant_id:
            try:
                parsed_id = uuid.UUID(variant_id)
                chosen_variant = next((v for v in available_variants if v.id == parsed_id), None)
            except ValueError:
                # O LLM pode enviar um ID malformado; nesse caso tratamos como "não escolhido".
                chosen_variant = None

        if not chosen_variant:
            # 2) Se só existe uma opção e o produto não exige escolha, seleciona automaticamente.
            if len(available_variants) == 1 and not product.required_variation_keys:
                chosen_variant = available_variants[0]
            else:
                # 3) Caso contrário, pede ao cliente para escolher (botões SELECT_VARIANT) e aborta a adição.
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
            # O CartService revalida estoque (considerando o que já está no carrinho) e persiste o item.
            summary = await cart_service.add_variant_to_cart(session_id, chosen_variant.id, quantidade)
        except DomainException as exc:
            # Erros de negócio viram resposta para o LLM explicar ao cliente, em vez de quebrar o chat.
            return json.dumps({"sucesso": False, "motivo": exc.message}, ensure_ascii=False)

        # Informa o frontend para exibir o resumo do carrinho e atualizar o contador/drawer.
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
        # RAG: recupera as FAQs semanticamente mais próximas; o LLM redige a resposta com base nelas.
        faqs = await faq_service.search_faqs(pergunta, limit=3)
        return json.dumps(
            [{"categoria": f.category, "pergunta": f.question, "resposta": f.answer} for f in faqs],
            ensure_ascii=False,
        )

    return [buscar_produto, sugerir_similares, adicionar_ao_carrinho, consultar_faq]
