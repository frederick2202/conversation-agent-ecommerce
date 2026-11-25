from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=3, max_length=120)
    message: str = Field(..., min_length=1, max_length=2000)


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    ui_actions: Optional[list[dict[str, Any]]] = None
    created_at: datetime
