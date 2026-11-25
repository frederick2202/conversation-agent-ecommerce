import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Review


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_product(self, product_id: uuid.UUID) -> list[Review]:
        stmt = select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save(self, review: Review) -> Review:
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review
