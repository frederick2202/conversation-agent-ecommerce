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
        stmt = (
            select(Cart)
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
        stmt = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_item_by_id(self, item_id: uuid.UUID) -> Optional[CartItem]:
        stmt = select(CartItem).options(selectinload(CartItem.variant)).where(CartItem.id == item_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_item(self, item: CartItem) -> CartItem:
        self.db.add(item)
        await self.db.commit()
        return item

    async def delete_item(self, item: CartItem) -> None:
        await self.db.delete(item)
        await self.db.commit()

    async def clear_cart(self, cart: Cart) -> None:
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.commit()
