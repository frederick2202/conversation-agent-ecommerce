"""
DTOs (Pydantic) do carrinho: corpo das requisições e formato das respostas da API.
"""

from decimal import Decimal
import uuid
from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    """Corpo de POST /cart/{session_id}/items."""

    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=20)  # Entre 1 e 20 unidades por operação.


class UpdateCartItemRequest(BaseModel):
    """Corpo de PATCH /cart/{session_id}/items/{item_id}. Quantidade 0 remove o item."""

    quantity: int = Field(ge=0, le=20)


class CartItemDetail(BaseModel):
    """Item do carrinho já "enriquecido" com dados do produto e preços calculados."""

    item_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID
    sku: str  # SKU da variação (não do produto).
    product_name: str
    image_url: str
    attributes: dict[str, str]
    unit_price: Decimal
    quantity: int
    line_total: Decimal  # unit_price * quantity


class CartSummaryResponse(BaseModel):
    """Resumo completo do carrinho retornado por todas as rotas de carrinho."""

    session_id: str
    items: list[CartItemDetail]
    total_items: int  # Soma das quantidades (não o número de linhas).
    subtotal: Decimal
