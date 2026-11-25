from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import ChatMessage


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_history(self, session_id: str, limit: int = 20) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_message(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def clear_session(self, session_id: str) -> None:
        await self.db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        await self.db.commit()
