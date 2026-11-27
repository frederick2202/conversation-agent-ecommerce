"""
Rotas HTTP do agente de IA (chat): /api/v1/chat/...
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.cart_repository import CartRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.faq_repository import FaqRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.chat import ChatHistoryItem, ChatMessageRequest
from app.services.cart_service import CartService
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.faq_service import FaqService
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/chat", tags=["Agente IA"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Monta o ChatService com todos os services que as ferramentas do agente utilizam.

    Todos compartilham a mesma sessão de banco da requisição.
    """
    emb = EmbeddingService()
    product_repo = ProductRepository(db)
    return ChatService(
        chat_repo=ChatRepository(db),
        product_service=ProductService(product_repo, emb),
        cart_service=CartService(CartRepository(db), product_repo),
        faq_service=FaqService(FaqRepository(db), emb),
    )


@router.get("/sessions/{session_id}", response_model=list[ChatHistoryItem])
async def get_history(session_id: str, service: ChatService = Depends(get_chat_service)):
    """Histórico de mensagens da sessão (inclui `ui_actions` para redesenhar botões/cards)."""
    return await service.get_history(session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(session_id: str, service: ChatService = Depends(get_chat_service)):
    """Apaga o histórico de conversa da sessão."""
    await service.clear_session(session_id)


@router.post("/stream")
async def stream_chat(payload: ChatMessageRequest, service: ChatService = Depends(get_chat_service)):
    """Envia uma mensagem ao agente e recebe a resposta em streaming (Server-Sent Events).

    Eventos emitidos: `token` (texto incremental), `ui_actions` (opcional) e `done`.
    Detalhes do formato em `app/services/chat_service.py`.
    """
    return StreamingResponse(
        service.stream_reply(payload.session_id, payload.message),
        media_type="text/event-stream",
        # Evita que proxies/navegador façam cache ou bufferizem o stream.
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
