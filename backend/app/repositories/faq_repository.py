from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Faq


class FaqRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Faq]:
        stmt = select(Faq).order_by(Faq.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, faq_id: uuid.UUID) -> Optional[Faq]:
        result = await self.db.execute(select(Faq).where(Faq.id == faq_id))
        return result.scalar_one_or_none()

    async def semantic_search(self, query_embedding: list[float], limit: int = 3) -> list[Faq]:
        stmt = (
            select(Faq)
            .where(Faq.embedding.is_not(None))
            .order_by(Faq.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save(self, faq: Faq) -> Faq:
        self.db.add(faq)
        await self.db.commit()
        await self.db.refresh(faq)
        return faq

    async def delete(self, faq: Faq) -> None:
        await self.db.delete(faq)
        await self.db.commit()
