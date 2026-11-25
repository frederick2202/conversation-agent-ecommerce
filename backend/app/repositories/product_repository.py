from typing import Optional
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Product, ProductVariant


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, category: Optional[str] = None, search: Optional[str] = None) -> list[Product]:
        stmt = select(Product).options(selectinload(Product.variants), selectinload(Product.reviews))
        if category and category != "Tudo":
            stmt = stmt.where(Product.category == category)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(pattern),
                    Product.sku.ilike(pattern),
                    Product.brand.ilike(pattern),
                    Product.short_description.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Product.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        stmt = (
            select(Product)
            .options(selectinload(Product.variants), selectinload(Product.reviews))
            .where(Product.id == product_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_name_or_sku(self, query: str) -> Optional[Product]:
        cleaned = query.strip()
        stmt = (
            select(Product)
            .options(selectinload(Product.variants), selectinload(Product.reviews))
            .where(or_(Product.sku.ilike(cleaned), Product.name.ilike(f"%{cleaned}%")))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_variant_by_id(self, variant_id: uuid.UUID) -> Optional[ProductVariant]:
        stmt = (
            select(ProductVariant)
            .options(selectinload(ProductVariant.product))
            .where(ProductVariant.id == variant_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def semantic_search(self, query_embedding: list[float], limit: int = 3) -> list[Product]:
        stmt = (
            select(Product)
            .options(selectinload(Product.variants), selectinload(Product.reviews))
            .where(Product.embedding.is_not(None))
            .order_by(Product.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.commit()
