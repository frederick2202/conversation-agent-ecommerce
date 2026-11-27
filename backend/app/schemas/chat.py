"""
DTOs (Pydantic) do chat com o agente de IA.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Corpo de POST /chat/stream: mensagem do usuário + sessão (mesmo id usado no carrinho)."""

    session_id: str = Field(..., min_length=3, max_length=120)
    message: str = Field(..., min_length=1, max_length=2000)


class ChatHistoryItem(BaseModel):
    """Mensagem do histórico retornada por GET /chat/sessions/{session_id}."""

    role: str  # "user" ou "assistant".
    content: str
    ui_actions: Optional[list[dict[str, Any]]] = None  # Ações de UI (SELECT_VARIANT, CART_UPDATED).
    created_at: datetime
