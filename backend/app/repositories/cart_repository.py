"""
Acesso a dados do carrinho (tabelas `carts` e `cart_items`).
Repositórios só fazem consultas/persistência; regras de negócio ficam em `CartService`.
"""

from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Cart, CartItem, ProductVariant


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_by_session(self, session_id: str) -> Cart:
        """Busca o carrinho da sessão (com itens, variações e produtos já carregados) ou cria um novo."""
        stmt = (
            select(Cart)
            # Carregamento antecipado em cadeia: itens -> variação -> produto (necessário para calcular preços).
            .options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product))
            .where(Cart.session_id == session_id)
        )
        result = await self.db.execute(stmt)
        cart = result.scalar_one_or_none()
        if not cart:
            cart = Cart(session_id=session_id)
            self.db.add(cart)
            await self.db.commit()
            await self.db.refresh(cart)
        return cart

    async def get_item(self, cart_id: uuid.UUID, variant_id: uuid.UUID) -> Optional[CartItem]:
        """Retorna o item de uma variação específica dentro do carrinho, se existir."""
        stmt = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_item_by_id(self, item_id: uuid.UUID) -> Optional[CartItem]:
        stmt = select(CartItem).options(selectinload(CartItem.variant)).where(CartItem.id == item_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_item(self, item: CartItem) -> CartItem:
        """Insere ou atualiza um item e faz commit imediatamente."""
        self.db.add(item)
        await self.db.commit()
        return item

    async def delete_item(self, item: CartItem) -> None:
        await self.db.delete(item)
        await self.db.commit()

    async def clear_cart(self, cart: Cart) -> None:
        """Remove todos os itens do carrinho (o registro do carrinho é mantido)."""
        # `list(...)` cria uma cópia para não iterar sobre a coleção enquanto ela é alterada.
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.commit()
